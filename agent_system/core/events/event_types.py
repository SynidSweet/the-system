"""
Event Types and Enums for the comprehensive event system
"""
from enum import Enum
from typing import TYPE_CHECKING


class EventType(str, Enum):
    # Entity lifecycle events
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SPAWNED = "task_spawned"
    TASK_BLOCKED = "task_blocked"
    TASK_RESUMED = "task_resumed"
    
    # Process events
    PROCESS_EXECUTED = "process_executed"
    PROCESS_STEP_COMPLETED = "process_step_completed"
    PROCESS_FAILED = "process_failed"
    
    # Tool events
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"
    
    # Agent events
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_PROMPT_SENT = "agent_prompt_sent"
    AGENT_RESPONSE_RECEIVED = "agent_response_received"
    AGENT_REASONING_COMPLETED = "agent_reasoning_completed"
    
    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_OPTIMIZATION = "system_optimization"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    
    # Review and optimization events
    REVIEW_TRIGGERED = "review_triggered"
    REVIEW_COMPLETED = "review_completed"
    OPTIMIZATION_DISCOVERED = "optimization_discovered"
    OPTIMIZATION_IMPLEMENTED = "optimization_implemented"
    
    # User interaction events
    USER_REQUEST_RECEIVED = "user_request_received"
    USER_RESPONSE_SENT = "user_response_sent"
    USER_FEEDBACK_RECEIVED = "user_feedback_received"


class EventOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class CounterType(str, Enum):
    USAGE = "usage"
    CREATION = "creation"
    MODIFICATION = "modification"
    ERROR = "error"
    SUCCESS = "success"
    FAILURE = "failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"


class ReviewFrequency(str, Enum):
    THRESHOLD = "threshold"
    PERIODIC = "periodic"
    HYBRID = "hybrid"


class EntityType(str, Enum):
    AGENT = "agent"
    TASK = "task"
    PROCESS = "process"
    TOOL = "tool"
    DOCUMENT = "document"
    EVENT = "event"
    SYSTEM = "system"