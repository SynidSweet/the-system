"""
Event System Models
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import time

from .event_types import EventType, EventOutcome, EntityType, CounterType, ReviewFrequency


class ResourceUsage(BaseModel):
    """Resource usage metrics for an event"""
    llm_tokens: Optional[int] = None
    execution_time_ms: Optional[int] = None
    memory_mb: Optional[float] = None
    cpu_percentage: Optional[float] = None


class Event(BaseModel):
    """Core event model for comprehensive system tracking"""
    id: Optional[int] = None
    event_type: EventType
    primary_entity_type: EntityType
    primary_entity_id: int
    related_entities: Dict[str, List[int]] = Field(default_factory=dict)
    event_data: Dict[str, Any] = Field(default_factory=dict)
    outcome: Optional[EventOutcome] = None
    tree_id: Optional[int] = None
    parent_event_id: Optional[int] = None
    duration_seconds: float = 0.0
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    resource_usage: Optional[ResourceUsage] = None
    
    class Config:
        from_attributes = True


class ReviewCounter(BaseModel):
    """Rolling review counter for entity optimization triggers"""
    id: Optional[int] = None
    entity_type: EntityType
    entity_id: int
    counter_type: CounterType
    count: int = 0
    threshold: int
    last_review_at: Optional[float] = None
    next_review_due: Optional[float] = None
    review_frequency: ReviewFrequency = ReviewFrequency.THRESHOLD
    created_at: Optional[float] = Field(default_factory=time.time)
    
    class Config:
        from_attributes = True


class OptimizationOpportunity(BaseModel):
    """Identified optimization opportunity from event analysis"""
    id: Optional[int] = None
    entity_type: EntityType
    entity_id: int
    opportunity_type: str
    description: str
    potential_impact: float = 0.0
    effort_estimate: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, rejected
    created_by_event_id: Optional[int] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[str] = None
    
    class Config:
        from_attributes = True


class EntityEffectiveness(BaseModel):
    """Entity effectiveness tracking metrics"""
    id: Optional[int] = None
    entity_type: EntityType
    entity_id: int
    metric_name: str
    metric_value: float
    measured_at: float = Field(default_factory=time.time)
    event_id: Optional[int] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class EventPattern(BaseModel):
    """Detected pattern from event analysis"""
    pattern_type: str  # performance, usage, error, interaction
    entity_type: EntityType
    entity_id: int
    pattern_description: str
    frequency: int
    confidence: float
    first_occurrence: float
    last_occurrence: float
    pattern_data: Dict[str, Any] = Field(default_factory=dict)
    
    def is_significant(self, min_frequency: int = 3, min_confidence: float = 0.7) -> bool:
        """Check if pattern is significant enough to act on"""
        return self.frequency >= min_frequency and self.confidence >= min_confidence


class EventAnomaly(BaseModel):
    """Detected anomaly from event analysis"""
    anomaly_type: str  # performance, usage, error_rate, etc.
    entity_type: EntityType
    entity_id: int
    description: str
    severity: float  # 0.0 to 1.0
    baseline_value: float
    anomaly_value: float
    detected_at: float
    event_ids: List[int] = Field(default_factory=list)
    
    @property
    def deviation_percentage(self) -> float:
        """Calculate percentage deviation from baseline"""
        if self.baseline_value == 0:
            return float('inf') if self.anomaly_value > 0 else 0
        return abs((self.anomaly_value - self.baseline_value) / self.baseline_value) * 100


class SuccessPattern(BaseModel):
    """Pattern associated with successful outcomes"""
    pattern_id: str
    sequences: List[List[str]]  # Common event sequences
    parameters: Dict[str, Any]  # Common parameters
    performance: Dict[str, float]  # Performance characteristics
    context: Dict[str, Any]  # Context patterns
    frequency: int
    success_rate: float
    avg_duration_seconds: float
    
    def is_significant(self) -> bool:
        """Check if pattern is significant for automation"""
        return self.frequency >= 3 and self.success_rate >= 0.8


class PerformanceMetrics(BaseModel):
    """Performance metrics calculated from events"""
    task_completion_rate: float
    average_task_time: float
    error_rate: float
    resource_efficiency: float
    quality_score: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "task_completion_rate": self.task_completion_rate,
            "average_task_time": self.average_task_time,
            "error_rate": self.error_rate,
            "resource_efficiency": self.resource_efficiency,
            "quality_score": self.quality_score
        }


class OptimizationImpact(BaseModel):
    """Impact measurement for implemented optimizations"""
    optimization_event_id: int
    performance_change: float  # Percentage change
    quality_change: float
    efficiency_change: float
    user_satisfaction_change: Optional[float] = None
    confidence_level: float
    measurement_period_days: int
    
    @property
    def overall_impact(self) -> float:
        """Calculate overall impact score"""
        impacts = [self.performance_change, self.quality_change, self.efficiency_change]
        if self.user_satisfaction_change is not None:
            impacts.append(self.user_satisfaction_change)
        return sum(impacts) / len(impacts)


class EventSystemHealth(BaseModel):
    """Health metrics for the event system itself"""
    logging_rate: float  # Events per second
    logging_latency: float  # Milliseconds
    buffer_utilization: float  # Percentage
    analysis_lag: float  # Seconds behind real-time
    pattern_detection_rate: float  # Patterns detected per hour
    storage_efficiency: float  # Compression ratio
    query_performance: float  # Average query time ms
    system_overhead: float  # CPU percentage
    optimization_effectiveness: float  # Success rate of optimizations
    
    @property
    def overall_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        scores = []
        
        # Logging performance (0-25)
        logging_score = min(25, (1000 / max(1, self.logging_latency)) * 25)
        scores.append(logging_score)
        
        # Buffer health (0-25)
        buffer_score = max(0, 25 - (self.buffer_utilization * 0.25))
        scores.append(buffer_score)
        
        # Analysis performance (0-25)
        analysis_score = max(0, 25 - (self.analysis_lag * 2.5))
        scores.append(analysis_score)
        
        # System efficiency (0-25)
        efficiency_score = min(25, (100 - self.system_overhead) * 0.25)
        scores.append(efficiency_score)
        
        return sum(scores)