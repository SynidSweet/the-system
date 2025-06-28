# Event Analyzers Module

This module contains specialized analyzers for different aspects of event analysis, refactored from the monolithic `event_analyzer.py` file (769 lines) into modular components.

## Structure

```
analyzers/
├── __init__.py                  # Module exports
├── pattern_analyzer.py          # EventPatternAnalyzer (263 lines)
├── success_pattern_detector.py  # SuccessPatternDetector (130 lines)
├── performance_analyzer.py      # EventPerformanceAnalyzer (239 lines)
└── optimization_detector.py     # OptimizationDetector (168 lines)
```

## Analyzers

### EventPatternAnalyzer
Detects patterns and anomalies in event sequences:
- Performance degradation patterns
- Usage concentration patterns
- Recurring error patterns
- Event sequence patterns

### SuccessPatternDetector
Identifies patterns associated with successful outcomes:
- Workflow signatures from successful operations
- Common parameters in successful workflows
- Performance metrics of successful patterns

### EventPerformanceAnalyzer
Analyzes performance metrics from events:
- Entity performance metrics calculation
- Performance trend analysis
- Comparison with similar entities
- Performance improvement recommendations

### OptimizationDetector
Detects optimization opportunities from events:
- Performance optimization opportunities
- Process automation candidates
- Error handling improvements

## Usage

```python
from agent_system.core.events.analyzers import EventPatternAnalyzer

analyzer = EventPatternAnalyzer()
patterns = await analyzer.analyze_patterns(
    entity_type=EntityType.AGENT,
    entity_id=123,
    time_window_hours=24
)
```

## Backward Compatibility

The original `event_analyzer.py` now serves as a compatibility layer, importing all analyzers and creating global instances to maintain existing code functionality.