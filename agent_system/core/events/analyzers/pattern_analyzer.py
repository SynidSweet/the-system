"""
Event Pattern Analyzer - Detects patterns and anomalies in event sequences
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from ..event_types import EventType, EventOutcome, EntityType
from ..models import EventPattern
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()


class EventPatternAnalyzer:
    """Analyzes events for patterns and anomalies"""
    
    async def analyze_patterns(
        self,
        entity_type: EntityType,
        entity_id: int,
        time_window_hours: int = 24
    ) -> List[EventPattern]:
        """Analyze recent events for patterns"""
        events = await self._get_entity_events(entity_type, entity_id, time_window_hours)
        
        patterns = []
        
        # Detect performance patterns
        performance_pattern = await self._analyze_performance_pattern(events)
        if performance_pattern and performance_pattern.is_significant():
            patterns.append(performance_pattern)
        
        # Detect usage patterns
        usage_pattern = await self._analyze_usage_pattern(events)
        if usage_pattern and usage_pattern.is_significant():
            patterns.append(usage_pattern)
        
        # Detect error patterns
        error_pattern = await self._analyze_error_pattern(events)
        if error_pattern and error_pattern.is_significant():
            patterns.append(error_pattern)
        
        # Detect sequence patterns
        sequence_patterns = await self._analyze_sequence_patterns(events)
        patterns.extend([p for p in sequence_patterns if p.is_significant()])
        
        return patterns
    
    async def _get_entity_events(
        self,
        entity_type: EntityType,
        entity_id: int,
        hours: int
    ) -> List[Dict[str, Any]]:
        """Get events for analysis"""
        query = """
        SELECT * FROM events
        WHERE (primary_entity_type = ? AND primary_entity_id = ?)
           OR (related_entities LIKE ?)
        AND timestamp > ?
        ORDER BY timestamp
        """
        
        time_cutoff = datetime.utcnow() - timedelta(hours=hours)
        entity_ref = f'%"{entity_type.value}": [{entity_id}%'
        
        return await database.execute_query(
            query,
            (entity_type.value, entity_id, entity_ref, time_cutoff)
        )
    
    async def _analyze_performance_pattern(
        self,
        events: List[Dict[str, Any]]
    ) -> Optional[EventPattern]:
        """Analyze performance trends"""
        if not events:
            return None
        
        # Group events by type and calculate metrics
        event_groups = defaultdict(list)
        for event in events:
            if event['duration_seconds'] > 0:
                event_groups[event['event_type']].append(event)
        
        # Find significant performance changes
        for event_type, type_events in event_groups.items():
            if len(type_events) >= 5:
                durations = [e['duration_seconds'] for e in type_events]
                
                # Split into first half and second half
                mid = len(durations) // 2
                first_half = durations[:mid]
                second_half = durations[mid:]
                
                avg_first = statistics.mean(first_half)
                avg_second = statistics.mean(second_half)
                
                # Check for significant change (>20%)
                if avg_second > avg_first * 1.2:
                    return EventPattern(
                        pattern_type="performance_degradation",
                        entity_type=EntityType(events[0]['primary_entity_type']),
                        entity_id=events[0]['primary_entity_id'],
                        pattern_description=f"{event_type} operations slowing down by {((avg_second/avg_first)-1)*100:.0f}%",
                        frequency=len(type_events),
                        confidence=0.8,
                        first_occurrence=type_events[0]['timestamp'],
                        last_occurrence=type_events[-1]['timestamp'],
                        pattern_data={
                            'event_type': event_type,
                            'avg_duration_first_half': avg_first,
                            'avg_duration_second_half': avg_second
                        }
                    )
        
        return None
    
    async def _analyze_usage_pattern(
        self,
        events: List[Dict[str, Any]]
    ) -> Optional[EventPattern]:
        """Analyze usage patterns"""
        if not events:
            return None
        
        # Count events by hour
        hourly_counts = defaultdict(int)
        for event in events:
            hour = datetime.fromtimestamp(event['timestamp']).hour
            hourly_counts[hour] += 1
        
        if len(hourly_counts) >= 3:
            # Find peak usage hours
            sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)
            peak_hours = sorted_hours[:3]
            
            total_events = sum(hourly_counts.values())
            peak_percentage = sum(count for _, count in peak_hours) / total_events
            
            if peak_percentage > 0.5:  # More than 50% of usage in top 3 hours
                return EventPattern(
                    pattern_type="usage_concentration",
                    entity_type=EntityType(events[0]['primary_entity_type']),
                    entity_id=events[0]['primary_entity_id'],
                    pattern_description=f"Usage concentrated in hours {[h for h, _ in peak_hours]}",
                    frequency=total_events,
                    confidence=peak_percentage,
                    first_occurrence=events[0]['timestamp'],
                    last_occurrence=events[-1]['timestamp'],
                    pattern_data={
                        'hourly_distribution': dict(hourly_counts),
                        'peak_hours': peak_hours,
                        'concentration_ratio': peak_percentage
                    }
                )
        
        return None
    
    async def _analyze_error_pattern(
        self,
        events: List[Dict[str, Any]]
    ) -> Optional[EventPattern]:
        """Analyze error patterns"""
        error_events = [e for e in events if e['outcome'] in ['failure', 'error']]
        
        if len(error_events) >= 3:
            # Group errors by type or context
            error_groups = defaultdict(list)
            for error in error_events:
                # Try to extract error type from event_data
                event_data = json.loads(error['event_data']) if isinstance(error['event_data'], str) else error['event_data']
                error_type = event_data.get('error_type', 'unknown')
                error_groups[error_type].append(error)
            
            # Find most common error
            if error_groups:
                most_common_error = max(error_groups.items(), key=lambda x: len(x[1]))
                error_type, error_list = most_common_error
                
                if len(error_list) >= 3:
                    return EventPattern(
                        pattern_type="recurring_error",
                        entity_type=EntityType(events[0]['primary_entity_type']),
                        entity_id=events[0]['primary_entity_id'],
                        pattern_description=f"Recurring {error_type} errors",
                        frequency=len(error_list),
                        confidence=0.9,
                        first_occurrence=error_list[0]['timestamp'],
                        last_occurrence=error_list[-1]['timestamp'],
                        pattern_data={
                            'error_type': error_type,
                            'error_count': len(error_list),
                            'total_errors': len(error_events)
                        }
                    )
        
        return None
    
    async def _analyze_sequence_patterns(
        self,
        events: List[Dict[str, Any]]
    ) -> List[EventPattern]:
        """Analyze event sequences for patterns"""
        patterns = []
        
        # Build sequences of events
        sequences = []
        current_sequence = []
        
        for i, event in enumerate(events):
            if not current_sequence or (
                event['tree_id'] == current_sequence[-1]['tree_id'] and
                event['timestamp'] - current_sequence[-1]['timestamp'] < 300  # Within 5 minutes
            ):
                current_sequence.append(event)
            else:
                if len(current_sequence) >= 3:
                    sequences.append(current_sequence)
                current_sequence = [event]
        
        if len(current_sequence) >= 3:
            sequences.append(current_sequence)
        
        # Find common sequences
        sequence_signatures = []
        for seq in sequences:
            signature = tuple(e['event_type'] for e in seq)
            sequence_signatures.append(signature)
        
        # Count sequence occurrences
        sequence_counts = Counter(sequence_signatures)
        
        for signature, count in sequence_counts.items():
            if count >= 2 and len(signature) >= 3:
                # Calculate success rate for this sequence
                success_count = sum(
                    1 for seq in sequences
                    if tuple(e['event_type'] for e in seq) == signature
                    and seq[-1]['outcome'] == 'success'
                )
                success_rate = success_count / count
                
                patterns.append(EventPattern(
                    pattern_type="event_sequence",
                    entity_type=EntityType(events[0]['primary_entity_type']),
                    entity_id=events[0]['primary_entity_id'],
                    pattern_description=f"Sequence: {' -> '.join(signature)}",
                    frequency=count,
                    confidence=success_rate,
                    first_occurrence=events[0]['timestamp'],
                    last_occurrence=events[-1]['timestamp'],
                    pattern_data={
                        'sequence': list(signature),
                        'occurrences': count,
                        'success_rate': success_rate
                    }
                ))
        
        return patterns