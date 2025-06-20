"""
Event System Module
Comprehensive event tracking and analysis for the agent system
"""

from .event_types import (
    EventType, EventOutcome, EntityType, CounterType, ReviewFrequency
)
from .models import (
    Event, ResourceUsage, ReviewCounter, OptimizationOpportunity,
    EntityEffectiveness, EventPattern, EventAnomaly, SuccessPattern,
    PerformanceMetrics, OptimizationImpact, EventSystemHealth
)
from .event_manager import EventManager, event_manager
from .event_analyzer import (
    EventPatternAnalyzer, SuccessPatternDetector,
    EventPerformanceAnalyzer, OptimizationDetector,
    pattern_analyzer, success_detector, performance_analyzer, optimization_detector
)

__all__ = [
    # Event Types
    'EventType', 'EventOutcome', 'EntityType', 'CounterType', 'ReviewFrequency',
    
    # Models
    'Event', 'ResourceUsage', 'ReviewCounter', 'OptimizationOpportunity',
    'EntityEffectiveness', 'EventPattern', 'EventAnomaly', 'SuccessPattern',
    'PerformanceMetrics', 'OptimizationImpact', 'EventSystemHealth',
    
    # Manager
    'EventManager', 'event_manager',
    
    # Analyzers
    'EventPatternAnalyzer', 'SuccessPatternDetector',
    'EventPerformanceAnalyzer', 'OptimizationDetector',
    'pattern_analyzer', 'success_detector', 'performance_analyzer', 'optimization_detector'
]