"""
Event Analysis Tools - Pattern detection and optimization discovery

This module provides backward compatibility by importing analyzer classes
from their new modular locations.
"""
# Import all analyzers from the modular structure
from .analyzers import (
    EventPatternAnalyzer,
    SuccessPatternDetector,
    EventPerformanceAnalyzer,
    OptimizationDetector
)

# Create global analyzer instances for backward compatibility
pattern_analyzer = EventPatternAnalyzer()
success_detector = SuccessPatternDetector()
performance_analyzer = EventPerformanceAnalyzer()
optimization_detector = OptimizationDetector()

# Export all classes and instances
__all__ = [
    'EventPatternAnalyzer',
    'SuccessPatternDetector',
    'EventPerformanceAnalyzer',
    'OptimizationDetector',
    'pattern_analyzer',
    'success_detector',
    'performance_analyzer',
    'optimization_detector'
]