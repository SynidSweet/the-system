"""
Event Performance Analyzer - Analyzes performance metrics from events
"""
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from ..event_types import EventType, EntityType
from ..models import PerformanceMetrics
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()


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