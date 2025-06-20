"""
Event Analysis Tools - Pattern detection and optimization discovery
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from .event_types import EventType, EventOutcome, EntityType
from .models import (
    EventPattern, EventAnomaly, SuccessPattern, PerformanceMetrics,
    OptimizationOpportunity, OptimizationImpact
)
from ..database_manager import database


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


class SuccessPatternDetector:
    """Identifies patterns associated with successful outcomes"""
    
    async def identify_success_patterns(
        self,
        entity_type: Optional[EntityType] = None,
        time_window_days: int = 7
    ) -> List[SuccessPattern]:
        """Identify patterns from successful operations"""
        # Get successful events
        query = """
        SELECT * FROM events
        WHERE outcome = 'success'
        AND timestamp > ?
        """
        params = [datetime.utcnow() - timedelta(days=time_window_days)]
        
        if entity_type:
            query += " AND primary_entity_type = ?"
            params.append(entity_type.value)
        
        query += " ORDER BY tree_id, timestamp"
        
        events = await database.execute_query(query, tuple(params))
        
        # Group by tree_id to get complete workflows
        tree_groups = defaultdict(list)
        for event in events:
            if event['tree_id']:
                tree_groups[event['tree_id']].append(event)
        
        # Extract patterns from successful workflows
        patterns = []
        pattern_groups = defaultdict(list)
        
        for tree_id, tree_events in tree_groups.items():
            if len(tree_events) >= 3:
                # Create workflow signature
                signature = self._create_workflow_signature(tree_events)
                pattern_groups[signature].append(tree_events)
        
        # Analyze pattern groups
        for signature, workflows in pattern_groups.items():
            if len(workflows) >= 3:
                pattern = await self._extract_success_pattern(signature, workflows)
                if pattern and pattern.is_significant():
                    patterns.append(pattern)
        
        return patterns
    
    def _create_workflow_signature(self, events: List[Dict[str, Any]]) -> str:
        """Create a signature for a workflow"""
        # Simple signature based on event types and order
        event_types = [e['event_type'] for e in events]
        return '|'.join(event_types)
    
    async def _extract_success_pattern(
        self,
        signature: str,
        workflows: List[List[Dict[str, Any]]]
    ) -> Optional[SuccessPattern]:
        """Extract pattern from successful workflows"""
        if not workflows:
            return None
        
        # Analyze common sequences
        sequences = []
        for workflow in workflows:
            sequence = [e['event_type'] for e in workflow]
            sequences.append(sequence)
        
        # Extract common parameters
        common_params = {}
        all_params = []
        for workflow in workflows:
            workflow_params = {}
            for event in workflow:
                event_data = json.loads(event['event_data']) if isinstance(event['event_data'], str) else event['event_data']
                workflow_params.update(event_data)
            all_params.append(workflow_params)
        
        # Find parameters that appear in most workflows
        param_counts = Counter()
        for params in all_params:
            for key, value in params.items():
                if isinstance(value, (str, int, float, bool)):
                    param_counts[(key, value)] += 1
        
        for (key, value), count in param_counts.items():
            if count >= len(workflows) * 0.7:  # Present in 70% of workflows
                common_params[key] = value
        
        # Calculate performance metrics
        durations = []
        for workflow in workflows:
            total_duration = sum(e['duration_seconds'] for e in workflow if e['duration_seconds'])
            durations.append(total_duration)
        
        avg_duration = statistics.mean(durations) if durations else 0
        
        return SuccessPattern(
            pattern_id=signature,
            sequences=sequences[:5],  # Top 5 sequences
            parameters=common_params,
            performance={
                'avg_duration': avg_duration,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0
            },
            context={'workflow_count': len(workflows)},
            frequency=len(workflows),
            success_rate=1.0,  # All are successful
            avg_duration_seconds=avg_duration
        )


class EventPerformanceAnalyzer:
    """Analyzes performance metrics from events"""
    
    async def analyze_entity_performance(
        self,
        entity_type: EntityType,
        entity_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Comprehensive performance analysis"""
        events = await self._get_entity_events(entity_type, entity_id, days)
        
        if not events:
            return {
                'entity_type': entity_type.value,
                'entity_id': entity_id,
                'no_data': True
            }
        
        # Calculate performance metrics
        metrics = await self._calculate_performance_metrics(events)
        
        # Analyze trends
        trends = self._calculate_performance_trends(events)
        
        # Compare with similar entities
        comparison = await self._compare_with_similar_entities(
            entity_type, entity_id, metrics
        )
        
        return {
            'entity_type': entity_type.value,
            'entity_id': entity_id,
            'metrics': metrics.to_dict(),
            'trends': trends,
            'comparison': comparison,
            'recommendations': await self._generate_recommendations(metrics, trends)
        }
    
    async def _get_entity_events(
        self,
        entity_type: EntityType,
        entity_id: int,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get events for performance analysis"""
        query = """
        SELECT * FROM events
        WHERE primary_entity_type = ?
        AND primary_entity_id = ?
        AND timestamp > ?
        ORDER BY timestamp
        """
        
        time_cutoff = datetime.utcnow() - timedelta(days=days)
        return await database.execute_query(
            query,
            (entity_type.value, entity_id, time_cutoff)
        )
    
    async def _calculate_performance_metrics(
        self,
        events: List[Dict[str, Any]]
    ) -> PerformanceMetrics:
        """Calculate performance metrics from events"""
        total_tasks = sum(1 for e in events if e['event_type'] in ['task_started', 'task_completed', 'task_failed'])
        completed_tasks = sum(1 for e in events if e['event_type'] == 'task_completed')
        failed_tasks = sum(1 for e in events if e['event_type'] == 'task_failed')
        
        task_durations = [
            e['duration_seconds'] for e in events
            if e['event_type'] == 'task_completed' and e['duration_seconds'] > 0
        ]
        
        avg_task_time = statistics.mean(task_durations) if task_durations else 0
        
        # Calculate resource efficiency
        resource_events = [e for e in events if 'resource_usage' in e.get('metadata', {})]
        avg_resource_usage = 0
        if resource_events:
            usages = []
            for e in resource_events:
                metadata = json.loads(e['metadata']) if isinstance(e['metadata'], str) else e['metadata']
                if 'resource_usage' in metadata and 'cpu_percentage' in metadata['resource_usage']:
                    usages.append(metadata['resource_usage']['cpu_percentage'])
            avg_resource_usage = statistics.mean(usages) if usages else 0
        
        return PerformanceMetrics(
            task_completion_rate=completed_tasks / total_tasks if total_tasks > 0 else 0,
            average_task_time=avg_task_time,
            error_rate=failed_tasks / total_tasks if total_tasks > 0 else 0,
            resource_efficiency=1.0 - (avg_resource_usage / 100) if avg_resource_usage else 1.0,
            quality_score=0.8  # Placeholder - would be calculated from evaluations
        )
    
    def _calculate_performance_trends(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        # Group events by day
        daily_metrics = defaultdict(lambda: {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'durations': []
        })
        
        for event in events:
            day = datetime.fromtimestamp(event['timestamp']).date()
            metrics = daily_metrics[day]
            
            if event['event_type'] in ['task_started', 'task_completed', 'task_failed']:
                metrics['total'] += 1
            
            if event['event_type'] == 'task_completed':
                metrics['completed'] += 1
                if event['duration_seconds'] > 0:
                    metrics['durations'].append(event['duration_seconds'])
            elif event['event_type'] == 'task_failed':
                metrics['failed'] += 1
        
        # Calculate daily rates
        daily_rates = []
        for day, metrics in sorted(daily_metrics.items()):
            if metrics['total'] > 0:
                daily_rates.append({
                    'date': day.isoformat(),
                    'completion_rate': metrics['completed'] / metrics['total'],
                    'error_rate': metrics['failed'] / metrics['total'],
                    'avg_duration': statistics.mean(metrics['durations']) if metrics['durations'] else 0
                })
        
        # Determine trend direction
        if len(daily_rates) >= 3:
            recent_rates = [r['completion_rate'] for r in daily_rates[-3:]]
            older_rates = [r['completion_rate'] for r in daily_rates[:3]]
            
            recent_avg = statistics.mean(recent_rates)
            older_avg = statistics.mean(older_rates)
            
            if recent_avg > older_avg * 1.1:
                trend = "improving"
            elif recent_avg < older_avg * 0.9:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            'daily_metrics': daily_rates,
            'trend_direction': trend
        }
    
    async def _compare_with_similar_entities(
        self,
        entity_type: EntityType,
        entity_id: int,
        metrics: PerformanceMetrics
    ) -> Dict[str, Any]:
        """Compare performance with similar entities"""
        # Get metrics for other entities of same type
        query = """
        SELECT 
            primary_entity_id,
            COUNT(CASE WHEN event_type = 'task_completed' THEN 1 END) as completed,
            COUNT(CASE WHEN event_type IN ('task_started', 'task_completed', 'task_failed') THEN 1 END) as total,
            AVG(CASE WHEN event_type = 'task_completed' THEN duration_seconds END) as avg_duration
        FROM events
        WHERE primary_entity_type = ?
        AND primary_entity_id != ?
        AND timestamp > ?
        GROUP BY primary_entity_id
        HAVING total > 5
        """
        
        time_cutoff = datetime.utcnow() - timedelta(days=30)
        results = await database.execute_query(
            query,
            (entity_type.value, entity_id, time_cutoff)
        )
        
        if not results:
            return {'no_comparison_data': True}
        
        # Calculate percentiles
        completion_rates = [r['completed'] / r['total'] for r in results if r['total'] > 0]
        durations = [r['avg_duration'] for r in results if r['avg_duration']]
        
        percentile_rank = 0
        if completion_rates:
            better_than = sum(1 for rate in completion_rates if metrics.task_completion_rate > rate)
            percentile_rank = (better_than / len(completion_rates)) * 100
        
        return {
            'percentile_rank': percentile_rank,
            'total_compared': len(results),
            'avg_completion_rate': statistics.mean(completion_rates) if completion_rates else 0,
            'avg_duration': statistics.mean(durations) if durations else 0
        }
    
    async def _generate_recommendations(
        self,
        metrics: PerformanceMetrics,
        trends: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if metrics.task_completion_rate < 0.8:
            recommendations.append("Low completion rate - investigate failure causes")
        
        if metrics.error_rate > 0.2:
            recommendations.append("High error rate - implement better error handling")
        
        if trends['trend_direction'] == 'degrading':
            recommendations.append("Performance degrading - review recent changes")
        
        if metrics.average_task_time > 300:  # 5 minutes
            recommendations.append("Long task duration - consider optimization or parallelization")
        
        return recommendations


class OptimizationDetector:
    """Detects optimization opportunities from events"""
    
    async def detect_optimization_opportunities(
        self,
        entity_type: Optional[EntityType] = None,
        hours: int = 24
    ) -> List[OptimizationOpportunity]:
        """Analyze events to find optimization opportunities"""
        # Get recent events
        query = """
        SELECT * FROM events
        WHERE timestamp > ?
        """
        params = [datetime.utcnow() - timedelta(hours=hours)]
        
        if entity_type:
            query += " AND primary_entity_type = ?"
            params.append(entity_type.value)
        
        events = await database.execute_query(query, tuple(params))
        
        opportunities = []
        
        # Check for performance issues
        perf_opportunities = await self._detect_performance_issues(events)
        opportunities.extend(perf_opportunities)
        
        # Check for automation opportunities
        auto_opportunities = await self._detect_automation_opportunities(events)
        opportunities.extend(auto_opportunities)
        
        # Check for error patterns
        error_opportunities = await self._detect_error_patterns(events)
        opportunities.extend(error_opportunities)
        
        return opportunities
    
    async def _detect_performance_issues(
        self,
        events: List[Dict[str, Any]]
    ) -> List[OptimizationOpportunity]:
        """Detect performance optimization opportunities"""
        opportunities = []
        
        # Group by entity and event type
        entity_performance = defaultdict(lambda: defaultdict(list))
        
        for event in events:
            if event['duration_seconds'] > 0:
                key = (event['primary_entity_type'], event['primary_entity_id'])
                entity_performance[key][event['event_type']].append(event['duration_seconds'])
        
        # Find entities with degrading performance
        for (entity_type, entity_id), event_types in entity_performance.items():
            for event_type, durations in event_types.items():
                if len(durations) >= 5:
                    # Check if recent operations are slower
                    recent = durations[-3:]
                    older = durations[:3]
                    
                    if statistics.mean(recent) > statistics.mean(older) * 1.3:
                        opportunities.append(OptimizationOpportunity(
                            entity_type=EntityType(entity_type),
                            entity_id=entity_id,
                            opportunity_type="performance_optimization",
                            description=f"{event_type} operations degrading - recent avg {statistics.mean(recent):.1f}s vs {statistics.mean(older):.1f}s",
                            potential_impact=0.3,
                            effort_estimate="medium"
                        ))
        
        return opportunities
    
    async def _detect_automation_opportunities(
        self,
        events: List[Dict[str, Any]]
    ) -> List[OptimizationOpportunity]:
        """Detect automation opportunities"""
        opportunities = []
        
        # Find repeated successful sequences
        tree_sequences = defaultdict(list)
        
        for event in events:
            if event['tree_id'] and event['outcome'] == 'success':
                tree_sequences[event['tree_id']].append(event)
        
        # Group by sequence signature
        sequence_groups = defaultdict(list)
        for tree_id, tree_events in tree_sequences.items():
            if len(tree_events) >= 3:
                signature = '|'.join(e['event_type'] for e in tree_events)
                sequence_groups[signature].append(tree_events)
        
        # Find frequently repeated sequences
        for signature, occurrences in sequence_groups.items():
            if len(occurrences) >= 3:
                # Calculate potential time savings
                avg_duration = statistics.mean(
                    sum(e['duration_seconds'] for e in seq if e['duration_seconds'])
                    for seq in occurrences
                )
                
                opportunities.append(OptimizationOpportunity(
                    entity_type=EntityType.PROCESS,
                    entity_id=0,  # New process
                    opportunity_type="process_automation",
                    description=f"Automate sequence: {signature.replace('|', ' -> ')}",
                    potential_impact=min(0.8, len(occurrences) * avg_duration / 3600),  # Hours saved
                    effort_estimate="low" if len(signature.split('|')) < 5 else "medium"
                ))
        
        return opportunities
    
    async def _detect_error_patterns(
        self,
        events: List[Dict[str, Any]]
    ) -> List[OptimizationOpportunity]:
        """Detect error-based optimization opportunities"""
        opportunities = []
        
        # Group errors by entity
        entity_errors = defaultdict(list)
        
        for event in events:
            if event['outcome'] in ['failure', 'error']:
                key = (event['primary_entity_type'], event['primary_entity_id'])
                entity_errors[key].append(event)
        
        # Find entities with high error rates
        for (entity_type, entity_id), errors in entity_errors.items():
            if len(errors) >= 3:
                # Extract error types
                error_types = []
                for error in errors:
                    event_data = json.loads(error['event_data']) if isinstance(error['event_data'], str) else error['event_data']
                    error_types.append(event_data.get('error_type', 'unknown'))
                
                # Find most common error
                error_counter = Counter(error_types)
                most_common = error_counter.most_common(1)[0]
                
                opportunities.append(OptimizationOpportunity(
                    entity_type=EntityType(entity_type),
                    entity_id=entity_id,
                    opportunity_type="error_handling",
                    description=f"Recurring {most_common[0]} errors ({most_common[1]} occurrences)",
                    potential_impact=0.5,
                    effort_estimate="medium"
                ))
        
        return opportunities


# Create global analyzer instances
pattern_analyzer = EventPatternAnalyzer()
success_detector = SuccessPatternDetector()
performance_analyzer = EventPerformanceAnalyzer()
optimization_detector = OptimizationDetector()