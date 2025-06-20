"""
Self-Improvement Engine for systematic optimization and evolution.

This engine orchestrates all self-improvement activities including:
- Rolling reviews
- Pattern-based improvements
- Automatic optimization
- Effectiveness tracking
- Safety validation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..database.db_manager import DatabaseManager
from ..core.event_manager import EventManager, EventType
from ..analysis.event_pattern_analyzer import EventPatternAnalyzer
from ..analysis.success_pattern_detector import SuccessPatternDetector
from ..analysis.performance_analyzer import EventPerformanceAnalyzer


class ImprovementType(Enum):
    """Types of improvements the system can make."""
    INSTRUCTION_UPDATE = "instruction_update"
    CONTEXT_OPTIMIZATION = "context_optimization"
    TOOL_REASSIGNMENT = "tool_reassignment"
    PROCESS_AUTOMATION = "process_automation"
    PERFORMANCE_TUNING = "performance_tuning"
    ERROR_PREVENTION = "error_prevention"


class ImprovementStatus(Enum):
    """Status of an improvement task."""
    PROPOSED = "proposed"
    VALIDATED = "validated"
    TESTING = "testing"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


@dataclass
class Improvement:
    """Represents a system improvement."""
    improvement_id: str
    improvement_type: ImprovementType
    entity_type: str
    entity_id: int
    description: str
    rationale: str
    expected_impact: Dict[str, Any]
    changes: Dict[str, Any]
    status: ImprovementStatus
    created_at: datetime
    deployed_at: Optional[datetime] = None
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None
    rollback_data: Optional[Dict[str, Any]] = None


class SelfImprovementEngine:
    """
    Orchestrates self-improvement activities across the system.
    
    This engine:
    1. Monitors system performance and patterns
    2. Identifies improvement opportunities
    3. Validates and tests improvements
    4. Deploys changes with safety mechanisms
    5. Tracks effectiveness and rolls back if needed
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        event_manager: EventManager
    ):
        self.db = db_manager
        self.event_manager = event_manager
        self.pattern_analyzer = EventPatternAnalyzer(db_manager)
        self.success_detector = SuccessPatternDetector(db_manager)
        self.performance_analyzer = EventPerformanceAnalyzer(db_manager)
        
        # Improvement configuration
        self.min_confidence_score = 0.8
        self.test_duration_hours = 24
        self.improvement_batch_size = 5
        self.rollback_threshold = -0.1  # 10% performance degradation triggers rollback
        
        # Active improvements tracking
        self.active_improvements: Dict[str, Improvement] = {}
        self.improvement_queue: List[Improvement] = []
        
        # Safety mechanisms
        self.max_concurrent_improvements = 3
        self.cooldown_period = timedelta(hours=6)
        self.last_improvement_time: Dict[str, datetime] = {}
    
    async def start(self):
        """Start the self-improvement engine."""
        # Start continuous monitoring
        asyncio.create_task(self._monitor_loop())
        
        # Start improvement execution
        asyncio.create_task(self._improvement_loop())
        
        # Start effectiveness tracking
        asyncio.create_task(self._effectiveness_loop())
        
        await self.event_manager.log_event(
            event_type=EventType.SYSTEM_EVENT,
            category="self_improvement",
            content="Self-improvement engine started",
            metadata={"engine_version": "1.0.0"}
        )
    
    async def _monitor_loop(self):
        """Continuously monitor for improvement opportunities."""
        while True:
            try:
                # Check rolling review triggers
                await self._check_review_triggers()
                
                # Analyze patterns for improvements
                await self._analyze_patterns()
                
                # Check optimization opportunities
                await self._check_opportunities()
                
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                await self.event_manager.log_event(
                    event_type=EventType.ERROR,
                    category="self_improvement",
                    content=f"Monitor loop error: {str(e)}",
                    metadata={"error_type": type(e).__name__}
                )
                await asyncio.sleep(60)
    
    async def _check_review_triggers(self):
        """Check and process rolling review triggers."""
        query = """
            SELECT rrc.*, e.name, e.entity_type
            FROM rolling_review_counters rrc
            JOIN entities e ON rrc.entity_id = e.entity_id 
                AND rrc.entity_type = e.entity_type
            WHERE (
                -- Threshold-based review
                (rrc.review_trigger_type = 'threshold' 
                 AND rrc.task_count >= rrc.review_interval)
                OR
                -- Periodic review
                (rrc.review_trigger_type = 'periodic' 
                 AND datetime(rrc.last_review_date, '+' || rrc.review_interval || ' days') <= datetime('now'))
                OR
                -- Hybrid review (either condition)
                (rrc.review_trigger_type = 'hybrid' 
                 AND (rrc.task_count >= rrc.review_interval 
                      OR datetime(rrc.last_review_date, '+' || rrc.review_interval || ' days') <= datetime('now')))
            )
            AND e.state = 'active'
        """
        
        rows = await self.db.fetch_all(query)
        
        for row in rows:
            await self._create_review_improvement(row)
    
    async def _analyze_patterns(self):
        """Analyze event patterns for improvement opportunities."""
        # Get recent patterns
        patterns = await self.pattern_analyzer.analyze_patterns(
            hours=24,
            min_frequency=5
        )
        
        # Look for improvement opportunities in patterns
        for pattern in patterns:
            if pattern['category'] == 'error' and pattern['frequency'] > 10:
                await self._create_error_prevention_improvement(pattern)
            
            elif pattern['category'] == 'performance' and pattern['avg_duration'] > 30:
                await self._create_performance_improvement(pattern)
            
            elif pattern['category'] == 'tool_usage' and pattern['failure_rate'] > 0.3:
                await self._create_tool_optimization_improvement(pattern)
    
    async def _check_opportunities(self):
        """Process optimization opportunities from the database."""
        query = """
            SELECT * FROM optimization_opportunities
            WHERE status = 'pending'
            AND confidence_score >= ?
            ORDER BY potential_impact DESC, created_at ASC
            LIMIT ?
        """
        
        opportunities = await self.db.fetch_all(
            query, 
            self.min_confidence_score,
            self.improvement_batch_size
        )
        
        for opp in opportunities:
            improvement = await self._convert_opportunity_to_improvement(opp)
            if improvement:
                self.improvement_queue.append(improvement)
    
    async def _improvement_loop(self):
        """Execute improvements from the queue."""
        while True:
            try:
                # Check if we can execute more improvements
                if len(self.active_improvements) >= self.max_concurrent_improvements:
                    await asyncio.sleep(60)
                    continue
                
                # Get next improvement from queue
                if not self.improvement_queue:
                    await asyncio.sleep(60)
                    continue
                
                improvement = self.improvement_queue.pop(0)
                
                # Check cooldown
                if not await self._check_cooldown(improvement):
                    # Put back in queue for later
                    self.improvement_queue.append(improvement)
                    await asyncio.sleep(60)
                    continue
                
                # Validate improvement
                if await self._validate_improvement(improvement):
                    # Deploy improvement
                    await self._deploy_improvement(improvement)
                else:
                    improvement.status = ImprovementStatus.REJECTED
                    await self._log_improvement_status(improvement)
                
            except Exception as e:
                await self.event_manager.log_event(
                    event_type=EventType.ERROR,
                    category="self_improvement",
                    content=f"Improvement loop error: {str(e)}",
                    metadata={"error_type": type(e).__name__}
                )
                await asyncio.sleep(60)
    
    async def _effectiveness_loop(self):
        """Track effectiveness of deployed improvements."""
        while True:
            try:
                for imp_id, improvement in list(self.active_improvements.items()):
                    if improvement.status == ImprovementStatus.DEPLOYED:
                        # Check if enough time has passed
                        if datetime.utcnow() - improvement.deployed_at > timedelta(hours=self.test_duration_hours):
                            await self._evaluate_improvement(improvement)
                
                await asyncio.sleep(3600)  # Check hourly
                
            except Exception as e:
                await self.event_manager.log_event(
                    event_type=EventType.ERROR,
                    category="self_improvement",
                    content=f"Effectiveness loop error: {str(e)}",
                    metadata={"error_type": type(e).__name__}
                )
                await asyncio.sleep(60)
    
    async def _create_review_improvement(self, review_data: Dict[str, Any]):
        """Create improvement from review trigger."""
        entity_type = review_data['entity_type']
        entity_id = review_data['entity_id']
        entity_name = review_data['name']
        
        # Get entity performance data
        perf_data = await self.performance_analyzer.get_entity_performance(
            entity_type=entity_type,
            entity_id=entity_id,
            hours=168  # 1 week
        )
        
        if not perf_data:
            return
        
        # Determine improvement type based on performance
        if perf_data['error_rate'] > 0.2:
            improvement_type = ImprovementType.ERROR_PREVENTION
            description = f"Reduce error rate for {entity_name}"
        elif perf_data['avg_duration'] > perf_data['peer_avg_duration'] * 1.5:
            improvement_type = ImprovementType.PERFORMANCE_TUNING
            description = f"Optimize performance for {entity_name}"
        else:
            improvement_type = ImprovementType.INSTRUCTION_UPDATE
            description = f"Update instructions for {entity_name} based on usage patterns"
        
        improvement = Improvement(
            improvement_id=f"imp_{entity_type}_{entity_id}_{datetime.utcnow().timestamp()}",
            improvement_type=improvement_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            rationale=f"Rolling review triggered after {review_data['task_count']} tasks",
            expected_impact={
                "error_reduction": 0.2 if improvement_type == ImprovementType.ERROR_PREVENTION else 0.05,
                "performance_gain": 0.3 if improvement_type == ImprovementType.PERFORMANCE_TUNING else 0.1
            },
            changes={},  # Will be populated during validation
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow(),
            metrics_before=perf_data
        )
        
        self.improvement_queue.append(improvement)
        
        # Update review counter
        await self.db.execute(
            """
            UPDATE rolling_review_counters
            SET task_count = 0, last_review_date = CURRENT_TIMESTAMP
            WHERE entity_type = ? AND entity_id = ?
            """,
            entity_type, entity_id
        )
    
    async def _create_error_prevention_improvement(self, pattern: Dict[str, Any]):
        """Create improvement to prevent recurring errors."""
        # Extract entity info from pattern
        entity_info = pattern.get('most_common_entity', {})
        if not entity_info:
            return
        
        improvement = Improvement(
            improvement_id=f"imp_error_{pattern['pattern_hash']}_{datetime.utcnow().timestamp()}",
            improvement_type=ImprovementType.ERROR_PREVENTION,
            entity_type=entity_info['entity_type'],
            entity_id=entity_info['entity_id'],
            description=f"Prevent recurring error: {pattern['pattern_description']}",
            rationale=f"Error pattern occurred {pattern['frequency']} times in 24 hours",
            expected_impact={
                "error_reduction": 0.8,
                "reliability_improvement": 0.5
            },
            changes={
                "add_validation": True,
                "enhance_error_handling": True,
                "update_constraints": pattern.get('suggested_constraints', [])
            },
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow()
        )
        
        self.improvement_queue.append(improvement)
    
    async def _create_performance_improvement(self, pattern: Dict[str, Any]):
        """Create improvement for performance optimization."""
        entity_info = pattern.get('slowest_entity', {})
        if not entity_info:
            return
        
        improvement = Improvement(
            improvement_id=f"imp_perf_{pattern['pattern_hash']}_{datetime.utcnow().timestamp()}",
            improvement_type=ImprovementType.PERFORMANCE_TUNING,
            entity_type=entity_info['entity_type'],
            entity_id=entity_info['entity_id'],
            description=f"Optimize slow operation: {pattern['operation']}",
            rationale=f"Average duration {pattern['avg_duration']}s exceeds threshold",
            expected_impact={
                "performance_gain": 0.5,
                "resource_efficiency": 0.3
            },
            changes={
                "optimize_query": pattern.get('slow_queries', []),
                "reduce_context": pattern.get('large_context', False),
                "cache_results": pattern.get('repeated_operations', False)
            },
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow()
        )
        
        self.improvement_queue.append(improvement)
    
    async def _create_tool_optimization_improvement(self, pattern: Dict[str, Any]):
        """Create improvement for tool usage optimization."""
        tool_info = pattern.get('tool_info', {})
        if not tool_info:
            return
        
        improvement = Improvement(
            improvement_id=f"imp_tool_{tool_info['tool_name']}_{datetime.utcnow().timestamp()}",
            improvement_type=ImprovementType.TOOL_REASSIGNMENT,
            entity_type='tool',
            entity_id=tool_info['tool_id'],
            description=f"Optimize tool usage for {tool_info['tool_name']}",
            rationale=f"Tool failure rate {pattern['failure_rate']} exceeds threshold",
            expected_impact={
                "reliability_improvement": 0.6,
                "efficiency_gain": 0.3
            },
            changes={
                "update_parameters": True,
                "reassign_to_agents": pattern.get('successful_agents', []),
                "add_retry_logic": True
            },
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow()
        )
        
        self.improvement_queue.append(improvement)
    
    async def _convert_opportunity_to_improvement(
        self, 
        opportunity: Dict[str, Any]
    ) -> Optional[Improvement]:
        """Convert an optimization opportunity to an improvement task."""
        # Map opportunity types to improvement types
        type_mapping = {
            'performance': ImprovementType.PERFORMANCE_TUNING,
            'error_reduction': ImprovementType.ERROR_PREVENTION,
            'automation': ImprovementType.PROCESS_AUTOMATION,
            'instruction': ImprovementType.INSTRUCTION_UPDATE,
            'context': ImprovementType.CONTEXT_OPTIMIZATION
        }
        
        improvement_type = type_mapping.get(
            opportunity['opportunity_type'], 
            ImprovementType.PERFORMANCE_TUNING
        )
        
        # Get current metrics
        metrics = await self.performance_analyzer.get_entity_performance(
            entity_type=opportunity['entity_type'],
            entity_id=opportunity['entity_id'],
            hours=168
        )
        
        improvement = Improvement(
            improvement_id=f"imp_opp_{opportunity['id']}_{datetime.utcnow().timestamp()}",
            improvement_type=improvement_type,
            entity_type=opportunity['entity_type'],
            entity_id=opportunity['entity_id'],
            description=opportunity['description'],
            rationale=f"Optimization opportunity with impact: {opportunity['potential_impact']}",
            expected_impact={
                "impact_score": opportunity['potential_impact'],
                "confidence": opportunity['confidence_score']
            },
            changes=json.loads(opportunity.get('metadata', '{}')),
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow(),
            metrics_before=metrics
        )
        
        # Update opportunity status
        await self.db.execute(
            "UPDATE optimization_opportunities SET status = 'in_progress' WHERE id = ?",
            opportunity['id']
        )
        
        return improvement
    
    async def _check_cooldown(self, improvement: Improvement) -> bool:
        """Check if entity is in cooldown period."""
        key = f"{improvement.entity_type}_{improvement.entity_id}"
        last_time = self.last_improvement_time.get(key)
        
        if last_time and datetime.utcnow() - last_time < self.cooldown_period:
            return False
        
        return True
    
    async def _validate_improvement(self, improvement: Improvement) -> bool:
        """Validate improvement before deployment."""
        # Check entity exists and is active
        entity = await self.db.fetch_one(
            """
            SELECT * FROM entities 
            WHERE entity_type = ? AND entity_id = ? AND state = 'active'
            """,
            improvement.entity_type, improvement.entity_id
        )
        
        if not entity:
            return False
        
        # Validate based on improvement type
        if improvement.improvement_type == ImprovementType.INSTRUCTION_UPDATE:
            return await self._validate_instruction_update(improvement, entity)
        elif improvement.improvement_type == ImprovementType.CONTEXT_OPTIMIZATION:
            return await self._validate_context_optimization(improvement, entity)
        elif improvement.improvement_type == ImprovementType.TOOL_REASSIGNMENT:
            return await self._validate_tool_reassignment(improvement, entity)
        elif improvement.improvement_type == ImprovementType.PROCESS_AUTOMATION:
            return await self._validate_process_automation(improvement, entity)
        elif improvement.improvement_type == ImprovementType.PERFORMANCE_TUNING:
            return await self._validate_performance_tuning(improvement, entity)
        elif improvement.improvement_type == ImprovementType.ERROR_PREVENTION:
            return await self._validate_error_prevention(improvement, entity)
        
        return True
    
    async def _validate_instruction_update(
        self, 
        improvement: Improvement, 
        entity: Dict[str, Any]
    ) -> bool:
        """Validate instruction update improvement."""
        if entity['entity_type'] != 'agent':
            return False
        
        # Get successful patterns
        patterns = await self.success_detector.detect_success_patterns(
            entity_type='agent',
            entity_id=entity['entity_id'],
            hours=168
        )
        
        if not patterns:
            return False
        
        # Generate improved instructions based on patterns
        improved_instructions = await self._generate_improved_instructions(
            current_instructions=entity.get('instruction', ''),
            success_patterns=patterns
        )
        
        improvement.changes['new_instructions'] = improved_instructions
        improvement.changes['backup_instructions'] = entity.get('instruction', '')
        
        return True
    
    async def _validate_context_optimization(
        self, 
        improvement: Improvement, 
        entity: Dict[str, Any]
    ) -> bool:
        """Validate context optimization improvement."""
        if entity['entity_type'] != 'agent':
            return False
        
        # Analyze context usage
        context_usage = await self._analyze_context_usage(entity['entity_id'])
        
        # Identify unused or rarely used context
        unused_contexts = [
            ctx for ctx, usage in context_usage.items() 
            if usage['access_count'] == 0
        ]
        
        rarely_used = [
            ctx for ctx, usage in context_usage.items() 
            if 0 < usage['access_count'] < 5
        ]
        
        improvement.changes['remove_contexts'] = unused_contexts
        improvement.changes['optional_contexts'] = rarely_used
        
        return len(unused_contexts) > 0 or len(rarely_used) > 0
    
    async def _validate_tool_reassignment(
        self, 
        improvement: Improvement, 
        entity: Dict[str, Any]
    ) -> bool:
        """Validate tool reassignment improvement."""
        # Get tool usage statistics
        tool_stats = await self._get_tool_usage_stats(
            improvement.entity_type,
            improvement.entity_id
        )
        
        if not tool_stats:
            return False
        
        # Identify underperforming tool assignments
        poor_performers = [
            stat for stat in tool_stats 
            if stat['failure_rate'] > 0.3 or stat['avg_duration'] > 60
        ]
        
        improvement.changes['reassignments'] = poor_performers
        
        return len(poor_performers) > 0
    
    async def _validate_process_automation(
        self, 
        improvement: Improvement, 
        entity: Dict[str, Any]
    ) -> bool:
        """Validate process automation improvement."""
        # Check if entity actions can be automated
        automation_candidates = await self._find_automation_candidates(
            improvement.entity_type,
            improvement.entity_id
        )
        
        if not automation_candidates:
            return False
        
        improvement.changes['automate_tasks'] = automation_candidates
        
        return True
    
    async def _validate_performance_tuning(
        self, 
        improvement: Improvement, 
        entity: Dict[str, Any]
    ) -> bool:
        """Validate performance tuning improvement."""
        # Identify performance bottlenecks
        bottlenecks = await self._identify_bottlenecks(
            improvement.entity_type,
            improvement.entity_id
        )
        
        if not bottlenecks:
            return False
        
        improvement.changes['optimize_operations'] = bottlenecks
        
        return True
    
    async def _validate_error_prevention(
        self, 
        improvement: Improvement, 
        entity: Dict[str, Any]
    ) -> bool:
        """Validate error prevention improvement."""
        # Get error patterns
        error_patterns = await self._get_error_patterns(
            improvement.entity_type,
            improvement.entity_id
        )
        
        if not error_patterns:
            return False
        
        # Generate prevention strategies
        prevention_strategies = []
        for pattern in error_patterns:
            strategy = {
                'error_type': pattern['error_type'],
                'prevention': self._get_prevention_strategy(pattern),
                'validation_rules': self._get_validation_rules(pattern)
            }
            prevention_strategies.append(strategy)
        
        improvement.changes['prevention_strategies'] = prevention_strategies
        
        return True
    
    async def _deploy_improvement(self, improvement: Improvement):
        """Deploy an improvement with safety mechanisms."""
        improvement.status = ImprovementStatus.TESTING
        improvement.deployed_at = datetime.utcnow()
        
        # Store rollback data
        improvement.rollback_data = await self._capture_rollback_data(improvement)
        
        try:
            # Apply changes based on improvement type
            if improvement.improvement_type == ImprovementType.INSTRUCTION_UPDATE:
                await self._deploy_instruction_update(improvement)
            elif improvement.improvement_type == ImprovementType.CONTEXT_OPTIMIZATION:
                await self._deploy_context_optimization(improvement)
            elif improvement.improvement_type == ImprovementType.TOOL_REASSIGNMENT:
                await self._deploy_tool_reassignment(improvement)
            elif improvement.improvement_type == ImprovementType.PROCESS_AUTOMATION:
                await self._deploy_process_automation(improvement)
            elif improvement.improvement_type == ImprovementType.PERFORMANCE_TUNING:
                await self._deploy_performance_tuning(improvement)
            elif improvement.improvement_type == ImprovementType.ERROR_PREVENTION:
                await self._deploy_error_prevention(improvement)
            
            improvement.status = ImprovementStatus.DEPLOYED
            self.active_improvements[improvement.improvement_id] = improvement
            
            # Update last improvement time
            key = f"{improvement.entity_type}_{improvement.entity_id}"
            self.last_improvement_time[key] = datetime.utcnow()
            
            # Log deployment
            await self.event_manager.log_event(
                event_type=EventType.OPTIMIZATION_IMPLEMENTED,
                category="self_improvement",
                content=f"Deployed improvement: {improvement.description}",
                metadata={
                    "improvement_id": improvement.improvement_id,
                    "improvement_type": improvement.improvement_type.value,
                    "entity_type": improvement.entity_type,
                    "entity_id": improvement.entity_id
                }
            )
            
        except Exception as e:
            # Rollback on error
            await self._rollback_improvement(improvement)
            improvement.status = ImprovementStatus.ROLLED_BACK
            
            await self.event_manager.log_event(
                event_type=EventType.ERROR,
                category="self_improvement",
                content=f"Failed to deploy improvement: {str(e)}",
                metadata={
                    "improvement_id": improvement.improvement_id,
                    "error_type": type(e).__name__
                }
            )
    
    async def _evaluate_improvement(self, improvement: Improvement):
        """Evaluate the effectiveness of a deployed improvement."""
        # Get current metrics
        current_metrics = await self.performance_analyzer.get_entity_performance(
            entity_type=improvement.entity_type,
            entity_id=improvement.entity_id,
            hours=24
        )
        
        improvement.metrics_after = current_metrics
        
        # Compare before and after
        effectiveness = self._calculate_effectiveness(
            improvement.metrics_before,
            improvement.metrics_after
        )
        
        # Check if improvement met expectations
        if effectiveness < self.rollback_threshold:
            # Rollback if performance degraded
            await self._rollback_improvement(improvement)
            improvement.status = ImprovementStatus.ROLLED_BACK
            
            await self.event_manager.log_event(
                event_type=EventType.OPTIMIZATION_ROLLED_BACK,
                category="self_improvement",
                content=f"Rolled back improvement due to performance degradation",
                metadata={
                    "improvement_id": improvement.improvement_id,
                    "effectiveness": effectiveness
                }
            )
        else:
            # Mark as successful
            improvement.status = ImprovementStatus.DEPLOYED
            
            # Update optimization opportunity if applicable
            await self._update_opportunity_status(improvement, 'completed')
            
            await self.event_manager.log_event(
                event_type=EventType.OPTIMIZATION_SUCCESSFUL,
                category="self_improvement",
                content=f"Improvement successful: {effectiveness:.2%} effectiveness",
                metadata={
                    "improvement_id": improvement.improvement_id,
                    "effectiveness": effectiveness,
                    "metrics_improved": self._get_improved_metrics(
                        improvement.metrics_before,
                        improvement.metrics_after
                    )
                }
            )
        
        # Remove from active improvements
        self.active_improvements.pop(improvement.improvement_id, None)
        
        # Store improvement history
        await self._store_improvement_history(improvement)
    
    def _calculate_effectiveness(
        self, 
        before: Dict[str, Any], 
        after: Dict[str, Any]
    ) -> float:
        """Calculate improvement effectiveness score."""
        if not before or not after:
            return 0.0
        
        scores = []
        
        # Error rate improvement (lower is better)
        if 'error_rate' in before and 'error_rate' in after:
            error_improvement = (before['error_rate'] - after['error_rate']) / max(before['error_rate'], 0.01)
            scores.append(error_improvement)
        
        # Performance improvement (lower duration is better)
        if 'avg_duration' in before and 'avg_duration' in after:
            perf_improvement = (before['avg_duration'] - after['avg_duration']) / max(before['avg_duration'], 0.01)
            scores.append(perf_improvement)
        
        # Success rate improvement (higher is better)
        if 'success_rate' in before and 'success_rate' in after:
            success_improvement = (after['success_rate'] - before['success_rate']) / max(1 - before['success_rate'], 0.01)
            scores.append(success_improvement)
        
        # Resource efficiency (lower is better)
        if 'resource_usage' in before and 'resource_usage' in after:
            resource_improvement = (before['resource_usage'] - after['resource_usage']) / max(before['resource_usage'], 0.01)
            scores.append(resource_improvement)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_improved_metrics(
        self, 
        before: Dict[str, Any], 
        after: Dict[str, Any]
    ) -> List[str]:
        """Get list of metrics that improved."""
        improved = []
        
        if before.get('error_rate', 1) > after.get('error_rate', 0):
            improved.append('error_rate')
        
        if before.get('avg_duration', float('inf')) > after.get('avg_duration', 0):
            improved.append('performance')
        
        if before.get('success_rate', 0) < after.get('success_rate', 1):
            improved.append('success_rate')
        
        if before.get('resource_usage', float('inf')) > after.get('resource_usage', 0):
            improved.append('resource_efficiency')
        
        return improved
    
    async def _capture_rollback_data(self, improvement: Improvement) -> Dict[str, Any]:
        """Capture current state for potential rollback."""
        rollback_data = {}
        
        if improvement.entity_type == 'agent':
            agent = await self.db.fetch_one(
                "SELECT * FROM agents WHERE id = ?",
                improvement.entity_id
            )
            if agent:
                rollback_data['agent_state'] = dict(agent)
        
        elif improvement.entity_type == 'tool':
            tool = await self.db.fetch_one(
                "SELECT * FROM tools WHERE id = ?",
                improvement.entity_id
            )
            if tool:
                rollback_data['tool_state'] = dict(tool)
        
        # Capture relationships
        relationships = await self.db.fetch_all(
            """
            SELECT * FROM entity_relationships 
            WHERE (source_type = ? AND source_id = ?)
               OR (target_type = ? AND target_id = ?)
            """,
            improvement.entity_type, improvement.entity_id,
            improvement.entity_type, improvement.entity_id
        )
        rollback_data['relationships'] = [dict(r) for r in relationships]
        
        return rollback_data
    
    async def _rollback_improvement(self, improvement: Improvement):
        """Rollback an improvement to previous state."""
        if not improvement.rollback_data:
            return
        
        try:
            # Restore based on entity type
            if improvement.entity_type == 'agent' and 'agent_state' in improvement.rollback_data:
                agent_state = improvement.rollback_data['agent_state']
                await self.db.execute(
                    """
                    UPDATE agents 
                    SET instruction = ?, context_documents = ?, 
                        available_tools = ?, constraints = ?
                    WHERE id = ?
                    """,
                    agent_state['instruction'],
                    agent_state['context_documents'],
                    agent_state['available_tools'],
                    agent_state['constraints'],
                    improvement.entity_id
                )
            
            elif improvement.entity_type == 'tool' and 'tool_state' in improvement.rollback_data:
                tool_state = improvement.rollback_data['tool_state']
                await self.db.execute(
                    """
                    UPDATE tools 
                    SET parameters = ?, permissions = ?
                    WHERE id = ?
                    """,
                    tool_state['parameters'],
                    tool_state['permissions'],
                    improvement.entity_id
                )
            
            await self.event_manager.log_event(
                event_type=EventType.SYSTEM_EVENT,
                category="self_improvement",
                content=f"Successfully rolled back improvement",
                metadata={"improvement_id": improvement.improvement_id}
            )
            
        except Exception as e:
            await self.event_manager.log_event(
                event_type=EventType.ERROR,
                category="self_improvement",
                content=f"Failed to rollback improvement: {str(e)}",
                metadata={
                    "improvement_id": improvement.improvement_id,
                    "error_type": type(e).__name__
                }
            )
    
    # Deployment methods for each improvement type
    
    async def _deploy_instruction_update(self, improvement: Improvement):
        """Deploy instruction update for an agent."""
        new_instructions = improvement.changes.get('new_instructions')
        if not new_instructions:
            return
        
        await self.db.execute(
            "UPDATE agents SET instruction = ? WHERE id = ?",
            new_instructions,
            improvement.entity_id
        )
    
    async def _deploy_context_optimization(self, improvement: Improvement):
        """Deploy context optimization for an agent."""
        # Get current context
        agent = await self.db.fetch_one(
            "SELECT context_documents FROM agents WHERE id = ?",
            improvement.entity_id
        )
        
        if not agent:
            return
        
        current_contexts = json.loads(agent['context_documents'])
        
        # Remove unused contexts
        remove_contexts = improvement.changes.get('remove_contexts', [])
        optimized_contexts = [
            ctx for ctx in current_contexts 
            if ctx not in remove_contexts
        ]
        
        await self.db.execute(
            "UPDATE agents SET context_documents = ? WHERE id = ?",
            json.dumps(optimized_contexts),
            improvement.entity_id
        )
    
    async def _deploy_tool_reassignment(self, improvement: Improvement):
        """Deploy tool reassignment."""
        reassignments = improvement.changes.get('reassignments', [])
        
        for reassignment in reassignments:
            # Remove tool from poor performers
            for agent_id in reassignment.get('remove_from', []):
                await self.db.execute(
                    """
                    DELETE FROM task_tool_assignments 
                    WHERE task_id IN (
                        SELECT id FROM tasks WHERE agent_id = ?
                    ) AND tool_name = ?
                    """,
                    agent_id, reassignment['tool_name']
                )
            
            # Add tool to good performers
            for agent_id in reassignment.get('assign_to', []):
                await self.db.execute(
                    """
                    INSERT OR IGNORE INTO agent_base_permissions 
                    (agent_type, base_tools)
                    SELECT 'agent', json_array(?)
                    WHERE EXISTS (SELECT 1 FROM agents WHERE id = ?)
                    """,
                    reassignment['tool_name'], agent_id
                )
    
    async def _deploy_process_automation(self, improvement: Improvement):
        """Deploy process automation."""
        # This would integrate with the process framework
        # For now, log the automation candidates
        await self.event_manager.log_event(
            event_type=EventType.SYSTEM_EVENT,
            category="self_improvement",
            content="Process automation candidates identified",
            metadata={
                "improvement_id": improvement.improvement_id,
                "candidates": improvement.changes.get('automate_tasks', [])
            }
        )
    
    async def _deploy_performance_tuning(self, improvement: Improvement):
        """Deploy performance tuning optimizations."""
        optimizations = improvement.changes.get('optimize_operations', [])
        
        for opt in optimizations:
            if opt['type'] == 'index':
                # Create database index
                await self.db.execute(opt['sql'])
            elif opt['type'] == 'cache':
                # Enable caching (would integrate with cache system)
                pass
            elif opt['type'] == 'batch':
                # Update batch sizes
                await self.db.execute(
                    """
                    UPDATE entities 
                    SET metadata = json_set(metadata, '$.batch_size', ?)
                    WHERE entity_type = ? AND entity_id = ?
                    """,
                    opt['batch_size'],
                    improvement.entity_type,
                    improvement.entity_id
                )
    
    async def _deploy_error_prevention(self, improvement: Improvement):
        """Deploy error prevention strategies."""
        strategies = improvement.changes.get('prevention_strategies', [])
        
        for strategy in strategies:
            # Add validation rules to constraints
            if improvement.entity_type == 'agent':
                agent = await self.db.fetch_one(
                    "SELECT constraints FROM agents WHERE id = ?",
                    improvement.entity_id
                )
                
                if agent:
                    constraints = json.loads(agent['constraints'])
                    constraints.extend(strategy['validation_rules'])
                    
                    await self.db.execute(
                        "UPDATE agents SET constraints = ? WHERE id = ?",
                        json.dumps(constraints),
                        improvement.entity_id
                    )
    
    # Helper methods
    
    async def _generate_improved_instructions(
        self, 
        current_instructions: str, 
        success_patterns: List[Dict[str, Any]]
    ) -> str:
        """Generate improved instructions based on success patterns."""
        # This is a simplified version - in production, this might use
        # an LLM to generate improved instructions based on patterns
        
        improvements = []
        
        for pattern in success_patterns[:3]:  # Top 3 patterns
            improvements.append(
                f"- {pattern['pattern_description']} (success rate: {pattern['success_rate']:.2%})"
            )
        
        improved = current_instructions + "\n\nBased on successful patterns:\n" + "\n".join(improvements)
        
        return improved
    
    async def _analyze_context_usage(self, agent_id: int) -> Dict[str, Dict[str, Any]]:
        """Analyze context document usage by an agent."""
        query = """
            SELECT 
                metadata->>'$.context_accessed' as context_name,
                COUNT(*) as access_count,
                AVG(CASE WHEN e.metadata->>'$.success' = 'true' THEN 1 ELSE 0 END) as success_rate
            FROM events e
            WHERE e.entity_type = 'agent' 
              AND e.entity_id = ?
              AND e.event_type = 'CONTEXT_ACCESSED'
              AND e.created_at > datetime('now', '-7 days')
            GROUP BY context_name
        """
        
        results = await self.db.fetch_all(query, agent_id)
        
        return {
            row['context_name']: {
                'access_count': row['access_count'],
                'success_rate': row['success_rate']
            }
            for row in results
        }
    
    async def _get_tool_usage_stats(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """Get tool usage statistics for an entity."""
        query = """
            SELECT 
                t.name as tool_name,
                t.id as tool_id,
                COUNT(*) as usage_count,
                AVG(CASE WHEN e.metadata->>'$.success' = 'true' THEN 0 ELSE 1 END) as failure_rate,
                AVG(CAST(e.metadata->>'$.duration' AS REAL)) as avg_duration
            FROM events e
            JOIN tools t ON t.name = e.metadata->>'$.tool_name'
            WHERE e.entity_type = ? 
              AND e.entity_id = ?
              AND e.event_type = 'TOOL_EXECUTED'
              AND e.created_at > datetime('now', '-7 days')
            GROUP BY t.name, t.id
        """
        
        results = await self.db.fetch_all(query, entity_type, entity_id)
        
        return [dict(row) for row in results]
    
    async def _find_automation_candidates(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """Find tasks that can be automated."""
        query = """
            SELECT 
                instruction,
                COUNT(*) as frequency,
                AVG(CAST(metadata->>'$.duration' AS REAL)) as avg_duration,
                MIN(CAST(metadata->>'$.duration' AS REAL)) as min_duration,
                MAX(CAST(metadata->>'$.duration' AS REAL)) as max_duration
            FROM tasks
            WHERE agent_id = ?
              AND status = 'completed'
              AND created_at > datetime('now', '-30 days')
            GROUP BY instruction
            HAVING frequency > 10 
              AND (max_duration - min_duration) / avg_duration < 0.2
            ORDER BY frequency DESC
        """
        
        if entity_type == 'agent':
            results = await self.db.fetch_all(query, entity_id)
            return [
                {
                    'task': row['instruction'],
                    'frequency': row['frequency'],
                    'consistency': 1 - (row['max_duration'] - row['min_duration']) / row['avg_duration']
                }
                for row in results
            ]
        
        return []
    
    async def _identify_bottlenecks(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Slow queries
        slow_queries = await self.db.fetch_all(
            """
            SELECT 
                metadata->>'$.query' as query,
                AVG(CAST(metadata->>'$.duration' AS REAL)) as avg_duration,
                COUNT(*) as frequency
            FROM events
            WHERE entity_type = ? 
              AND entity_id = ?
              AND event_type = 'DATABASE_QUERY'
              AND CAST(metadata->>'$.duration' AS REAL) > 1.0
              AND created_at > datetime('now', '-7 days')
            GROUP BY query
            ORDER BY avg_duration DESC
            LIMIT 5
            """,
            entity_type, entity_id
        )
        
        for query in slow_queries:
            bottlenecks.append({
                'type': 'index',
                'description': f"Slow query: {query['query'][:50]}...",
                'sql': f"CREATE INDEX idx_optimization_{entity_id} ON ...",  # Would be specific
                'impact': query['avg_duration']
            })
        
        return bottlenecks
    
    async def _get_error_patterns(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """Get recurring error patterns."""
        query = """
            SELECT 
                metadata->>'$.error_type' as error_type,
                metadata->>'$.error_message' as error_message,
                COUNT(*) as frequency,
                GROUP_CONCAT(DISTINCT metadata->>'$.context') as contexts
            FROM events
            WHERE entity_type = ? 
              AND entity_id = ?
              AND event_type = 'ERROR'
              AND created_at > datetime('now', '-7 days')
            GROUP BY error_type, error_message
            HAVING frequency > 3
            ORDER BY frequency DESC
        """
        
        results = await self.db.fetch_all(query, entity_type, entity_id)
        
        return [dict(row) for row in results]
    
    def _get_prevention_strategy(self, error_pattern: Dict[str, Any]) -> str:
        """Get prevention strategy for an error pattern."""
        error_type = error_pattern.get('error_type', '')
        
        strategies = {
            'ValidationError': 'Add input validation before processing',
            'TimeoutError': 'Increase timeout or optimize operation',
            'ResourceError': 'Add resource checks and limits',
            'PermissionError': 'Verify permissions before operation',
            'DataError': 'Add data integrity checks'
        }
        
        return strategies.get(error_type, 'Add error handling and retry logic')
    
    def _get_validation_rules(self, error_pattern: Dict[str, Any]) -> List[str]:
        """Get validation rules for preventing errors."""
        error_type = error_pattern.get('error_type', '')
        
        rules = {
            'ValidationError': [
                'Validate input types and formats',
                'Check required fields',
                'Verify data ranges'
            ],
            'TimeoutError': [
                'Check operation complexity before execution',
                'Add progress monitoring',
                'Implement chunking for large operations'
            ],
            'ResourceError': [
                'Check resource availability',
                'Implement resource pooling',
                'Add cleanup procedures'
            ]
        }
        
        return rules.get(error_type, ['Add defensive checks'])
    
    async def _update_opportunity_status(
        self, 
        improvement: Improvement, 
        status: str
    ):
        """Update optimization opportunity status."""
        # Extract opportunity ID from improvement ID if present
        if '_opp_' in improvement.improvement_id:
            opp_id = improvement.improvement_id.split('_opp_')[1].split('_')[0]
            
            await self.db.execute(
                """
                UPDATE optimization_opportunities 
                SET status = ?, 
                    metadata = json_set(metadata, '$.effectiveness', ?)
                WHERE id = ?
                """,
                status,
                improvement.metrics_after.get('effectiveness', 0),
                opp_id
            )
    
    async def _store_improvement_history(self, improvement: Improvement):
        """Store improvement in history for future reference."""
        await self.db.execute(
            """
            INSERT INTO improvement_history 
            (improvement_id, improvement_type, entity_type, entity_id,
             description, status, effectiveness, metrics_before, metrics_after,
             deployed_at, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            improvement.improvement_id,
            improvement.improvement_type.value,
            improvement.entity_type,
            improvement.entity_id,
            improvement.description,
            improvement.status.value,
            self._calculate_effectiveness(
                improvement.metrics_before,
                improvement.metrics_after
            ),
            json.dumps(improvement.metrics_before),
            json.dumps(improvement.metrics_after),
            improvement.deployed_at,
            datetime.utcnow()
        )
    
    async def _log_improvement_status(self, improvement: Improvement):
        """Log improvement status update."""
        await self.event_manager.log_event(
            event_type=EventType.SYSTEM_EVENT,
            category="self_improvement",
            content=f"Improvement status: {improvement.status.value}",
            metadata={
                "improvement_id": improvement.improvement_id,
                "description": improvement.description,
                "entity": f"{improvement.entity_type}_{improvement.entity_id}"
            }
        )