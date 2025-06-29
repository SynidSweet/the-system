"""
Success Pattern Detector - Identifies patterns associated with successful outcomes
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from ..event_types import EventType, EntityType
from ..models import SuccessPattern
from agent_system.config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()


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