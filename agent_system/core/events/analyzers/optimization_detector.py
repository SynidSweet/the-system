"""
Optimization Detector - Detects optimization opportunities from events
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from ..event_types import EventType, EntityType
from ..models import OptimizationOpportunity
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()


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