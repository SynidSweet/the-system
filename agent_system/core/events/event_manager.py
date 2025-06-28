"""
Event Manager - Core event logging and management system
"""
import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
from contextlib import asynccontextmanager

from .event_types import EventType, EventOutcome, EntityType, CounterType
from .models import Event, ResourceUsage, ReviewCounter
from agent_system.config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()


class EventManager:
    """Manages comprehensive event logging and processing"""
    
    def __init__(self):
        self.event_buffer: List[Event] = []
        self.batch_size = 100
        self.flush_interval_seconds = 10
        self.last_flush_time = time.time()
        self._flush_lock = asyncio.Lock()
        self._context_stack = []
        
    @asynccontextmanager
    async def event_context(self, tree_id: Optional[int] = None, parent_event_id: Optional[int] = None):
        """Context manager for event tracking"""
        context = {
            'tree_id': tree_id,
            'parent_event_id': parent_event_id,
            'start_time': time.time()
        }
        self._context_stack.append(context)
        try:
            yield context
        finally:
            self._context_stack.pop()
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current event context"""
        if self._context_stack:
            return self._context_stack[-1].copy()
        return {}
    
    async def log_event(
        self,
        event_type: EventType,
        primary_entity_type: EntityType,
        primary_entity_id: int,
        event_data: Dict[str, Any] = None,
        related_entities: Dict[str, List[int]] = None,
        outcome: Optional[EventOutcome] = None,
        duration_seconds: Optional[float] = None,
        resource_usage: Optional[ResourceUsage] = None,
        metadata: Dict[str, Any] = None
    ) -> int:
        """Log a system event with automatic context enrichment"""
        
        # Get context from stack
        context = self.get_current_context()
        
        # Calculate duration if not provided
        if duration_seconds is None and 'start_time' in context:
            duration_seconds = time.time() - context['start_time']
        
        # Create event
        event = Event(
            event_type=event_type,
            primary_entity_type=primary_entity_type,
            primary_entity_id=primary_entity_id,
            event_data=event_data or {},
            related_entities=related_entities or {},
            outcome=outcome,
            tree_id=context.get('tree_id'),
            parent_event_id=context.get('parent_event_id'),
            duration_seconds=duration_seconds or 0.0,
            resource_usage=resource_usage,
            metadata=metadata or {}
        )
        
        # Enrich event with additional context
        await self._enrich_event_context(event)
        
        # Add to buffer
        async with self._flush_lock:
            self.event_buffer.append(event)
            
            # Check if we should flush
            if len(self.event_buffer) >= self.batch_size:
                await self._flush_events()
        
        # Also check time-based flush
        if time.time() - self.last_flush_time > self.flush_interval_seconds:
            await self.flush()
        
        return event.id or 0
    
    async def _enrich_event_context(self, event: Event):
        """Automatically add contextual information to events"""
        # Add related entities from database if not provided
        if not event.related_entities and event.primary_entity_type == EntityType.TASK:
            try:
                task = await database.tasks.get_by_id(event.primary_entity_id)
                if task:
                    event.related_entities['agent'] = [task.agent_id]
                    if task.parent_task_id:
                        event.related_entities['task'] = [task.parent_task_id]
            except Exception:
                pass  # Don't fail event logging due to enrichment errors
        
        # Add system metadata
        event.metadata['logged_at'] = datetime.utcnow().isoformat()
        event.metadata['event_version'] = '1.0'
    
    async def _flush_events(self):
        """Flush event buffer to database"""
        if not self.event_buffer:
            return
        
        events_to_flush = self.event_buffer.copy()
        self.event_buffer.clear()
        self.last_flush_time = time.time()
        
        try:
            # Batch insert events
            for event in events_to_flush:
                event_id = await self._insert_event(event)
                event.id = event_id
                
                # Update rolling review counters
                await self._update_review_counters(event)
                
                # Check for optimization opportunities
                await self._check_optimization_triggers(event)
                
        except Exception as e:
            # Log error without creating recursive events
            print(f"Error flushing events: {e}")
            # Re-add events to buffer for retry
            self.event_buffer.extend(events_to_flush)
    
    async def _insert_event(self, event: Event) -> int:
        """Insert event into database"""
        query = """
        INSERT INTO events (
            event_type, primary_entity_type, primary_entity_id,
            related_entities, event_data, outcome, tree_id,
            parent_event_id, duration_seconds, timestamp, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            event.event_type.value,
            event.primary_entity_type.value,
            event.primary_entity_id,
            json.dumps(event.related_entities),
            json.dumps(event.event_data),
            event.outcome.value if event.outcome else None,
            event.tree_id,
            event.parent_event_id,
            event.duration_seconds,
            datetime.fromtimestamp(event.timestamp),
            json.dumps(event.metadata)
        )
        
        return await database.execute_command(query, params)
    
    async def _update_review_counters(self, event: Event):
        """Update rolling review counters based on event"""
        # Map event types to counter types
        counter_mappings = {
            EventType.TOOL_CALLED: (CounterType.USAGE, 1),
            EventType.TOOL_COMPLETED: (CounterType.SUCCESS, 1),
            EventType.TOOL_FAILED: (CounterType.FAILURE, 1),
            EventType.TASK_COMPLETED: (CounterType.SUCCESS, 1),
            EventType.TASK_FAILED: (CounterType.FAILURE, 1),
            EventType.SYSTEM_ERROR: (CounterType.ERROR, 1),
        }
        
        if event.event_type in counter_mappings:
            counter_type, increment = counter_mappings[event.event_type]
            await self._increment_counter(
                event.primary_entity_type,
                event.primary_entity_id,
                counter_type,
                increment
            )
    
    async def _increment_counter(
        self,
        entity_type: EntityType,
        entity_id: int,
        counter_type: CounterType,
        increment: int = 1
    ) -> bool:
        """Increment counter and check for review triggers"""
        # Get or create counter
        query = """
        SELECT * FROM rolling_review_counters
        WHERE entity_type = ? AND entity_id = ? AND counter_type = ?
        """
        params = (entity_type.value, entity_id, counter_type.value)
        
        results = await database.execute_query(query, params)
        
        if results:
            # Update existing counter
            counter = results[0]
            new_count = counter['count'] + increment
            
            # Check if threshold reached
            if new_count >= counter['threshold']:
                await self._trigger_review(entity_type, entity_id, counter_type, counter)
                # Reset counter
                update_query = """
                UPDATE rolling_review_counters
                SET count = 0, last_review_at = ?
                WHERE entity_type = ? AND entity_id = ? AND counter_type = ?
                """
                await database.execute_command(
                    update_query,
                    (datetime.utcnow(), entity_type.value, entity_id, counter_type.value)
                )
                return True
            else:
                # Just increment
                update_query = """
                UPDATE rolling_review_counters
                SET count = count + ?
                WHERE entity_type = ? AND entity_id = ? AND counter_type = ?
                """
                await database.execute_command(
                    update_query,
                    (increment, entity_type.value, entity_id, counter_type.value)
                )
        
        return False
    
    async def _trigger_review(
        self,
        entity_type: EntityType,
        entity_id: int,
        counter_type: CounterType,
        counter_data: Dict[str, Any]
    ):
        """Trigger optimization review for entity"""
        # Log review trigger event
        await self.log_event(
            EventType.REVIEW_TRIGGERED,
            entity_type,
            entity_id,
            event_data={
                'counter_type': counter_type.value,
                'counter_value': counter_data['count'],
                'threshold': counter_data['threshold'],
                'last_review': counter_data.get('last_review_at')
            }
        )
        
        # Create optimization review task
        # This will be implemented when we integrate with the task system
        pass
    
    async def _check_optimization_triggers(self, event: Event):
        """Check if event should trigger optimization analysis"""
        # Check for repeated failures
        if event.outcome == EventOutcome.FAILURE:
            await self._check_failure_pattern(event)
        
        # Check for performance degradation
        if event.duration_seconds > 0:
            await self._check_performance_degradation(event)
    
    async def _check_failure_pattern(self, event: Event):
        """Check for repeated failure patterns"""
        # Get recent failures for the same entity
        query = """
        SELECT COUNT(*) as failure_count
        FROM events
        WHERE primary_entity_type = ? 
        AND primary_entity_id = ?
        AND outcome = 'failure'
        AND timestamp > ?
        """
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        params = (
            event.primary_entity_type.value,
            event.primary_entity_id,
            one_hour_ago
        )
        
        results = await database.execute_query(query, params)
        
        if results and results[0]['failure_count'] >= 3:
            # Log optimization opportunity
            await self._log_optimization_opportunity(
                event.primary_entity_type,
                event.primary_entity_id,
                "repeated_failures",
                f"Entity has failed {results[0]['failure_count']} times in the last hour",
                event.id
            )
    
    async def _check_performance_degradation(self, event: Event):
        """Check for performance degradation"""
        # Get average duration for similar events
        query = """
        SELECT AVG(duration_seconds) as avg_duration
        FROM events
        WHERE event_type = ?
        AND primary_entity_type = ?
        AND primary_entity_id = ?
        AND outcome = 'success'
        AND timestamp > ?
        AND timestamp < ?
        """
        
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        params = (
            event.event_type.value,
            event.primary_entity_type.value,
            event.primary_entity_id,
            one_week_ago,
            datetime.fromtimestamp(event.timestamp)
        )
        
        results = await database.execute_query(query, params)
        
        if results and results[0]['avg_duration']:
            avg_duration = results[0]['avg_duration']
            if event.duration_seconds > avg_duration * 1.5:  # 50% slower
                await self._log_optimization_opportunity(
                    event.primary_entity_type,
                    event.primary_entity_id,
                    "performance_degradation",
                    f"Operation took {event.duration_seconds:.1f}s vs average {avg_duration:.1f}s",
                    event.id
                )
    
    async def _log_optimization_opportunity(
        self,
        entity_type: EntityType,
        entity_id: int,
        opportunity_type: str,
        description: str,
        created_by_event_id: int
    ):
        """Log an optimization opportunity"""
        query = """
        INSERT INTO optimization_opportunities (
            entity_type, entity_id, opportunity_type,
            description, created_by_event_id
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        params = (
            entity_type.value,
            entity_id,
            opportunity_type,
            description,
            created_by_event_id
        )
        
        await database.execute_command(query, params)
    
    async def flush(self):
        """Force flush of event buffer"""
        async with self._flush_lock:
            if self.event_buffer:
                await self._flush_events()
    
    async def get_entity_events(
        self,
        entity_type: EntityType,
        entity_id: int,
        hours: int = 24,
        event_types: Optional[List[EventType]] = None
    ) -> List[Dict[str, Any]]:
        """Get recent events for an entity"""
        query = """
        SELECT * FROM events
        WHERE primary_entity_type = ?
        AND primary_entity_id = ?
        AND timestamp > ?
        """
        
        params = [
            entity_type.value,
            entity_id,
            datetime.utcnow() - timedelta(hours=hours)
        ]
        
        if event_types:
            placeholders = ','.join(['?' for _ in event_types])
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])
        
        query += " ORDER BY timestamp DESC"
        
        return await database.execute_query(query, tuple(params))
    
    async def get_event_chain(self, root_event_id: int) -> List[Dict[str, Any]]:
        """Get complete event chain from root event"""
        events = []
        event_ids_to_process = [root_event_id]
        processed_ids = set()
        
        while event_ids_to_process:
            event_id = event_ids_to_process.pop(0)
            if event_id in processed_ids:
                continue
            
            # Get event
            query = "SELECT * FROM events WHERE id = ?"
            results = await database.execute_query(query, (event_id,))
            
            if results:
                event = results[0]
                events.append(event)
                processed_ids.add(event_id)
                
                # Find child events
                child_query = "SELECT id FROM events WHERE parent_event_id = ?"
                child_results = await database.execute_query(child_query, (event_id,))
                
                for child in child_results:
                    if child['id'] not in processed_ids:
                        event_ids_to_process.append(child['id'])
        
        # Sort by timestamp
        events.sort(key=lambda e: e['timestamp'])
        return events
    
    def should_log_detailed_event(
        self,
        event_type: EventType,
        entity_type: EntityType,
        context: Dict[str, Any]
    ) -> bool:
        """Determine if event should be logged with full detail"""
        # Always log detailed events for certain types
        always_detailed = {
            EventType.SYSTEM_ERROR,
            EventType.OPTIMIZATION_IMPLEMENTED,
            EventType.REVIEW_TRIGGERED,
            EventType.ENTITY_CREATED,
            EventType.ENTITY_DELETED
        }
        
        if event_type in always_detailed:
            return True
        
        # Log detailed events for critical operations
        if context.get('critical_operation', False):
            return True
        
        # Sample routine operations
        sampling_rates = {
            EventType.TOOL_CALLED: 0.1,  # 10% sampling
            EventType.TOOL_COMPLETED: 0.1,
            EventType.AGENT_PROMPT_SENT: 0.2,  # 20% sampling
            EventType.AGENT_RESPONSE_RECEIVED: 0.2,
        }
        
        rate = sampling_rates.get(event_type, 0.5)  # Default 50% sampling
        return random.random() < rate


# Global event manager instance
event_manager = EventManager()