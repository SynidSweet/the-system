"""Task state machine for the event-driven runtime engine."""

from enum import Enum
from typing import Dict, List, Set, Optional, Callable
from datetime import datetime
import asyncio

from ..events.event_types import EventType, EntityType
from ..events.event_manager import EventManager


class TaskState(str, Enum):
    """Task states for the runtime engine."""
    CREATED = "created"                    # Just created, needs process assignment
    PROCESS_ASSIGNED = "process_assigned"  # Process assigned, ready for process execution
    READY_FOR_AGENT = "ready_for_agent"    # Agent assigned, ready for LLM call
    WAITING_ON_DEPENDENCIES = "waiting_on_dependencies"  # Blocked on subtask completion
    AGENT_RESPONDING = "agent_responding"  # LLM call in progress
    TOOL_PROCESSING = "tool_processing"    # Tool calls being processed
    COMPLETED = "completed"                # Task finished successfully
    FAILED = "failed"                      # Task failed
    MANUAL_HOLD = "manual_hold"           # Manually paused for debugging


class StateTransition:
    """Represents a valid state transition."""
    
    def __init__(
        self,
        from_state: TaskState,
        to_state: TaskState,
        condition: Optional[Callable] = None,
        automatic: bool = True
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.automatic = automatic


class TaskStateMachine:
    """Manages task state transitions and validations."""
    
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.event_manager = event_manager
        
        # Define valid state transitions
        self.transitions: List[StateTransition] = [
            # Initial transitions
            StateTransition(TaskState.CREATED, TaskState.PROCESS_ASSIGNED),
            StateTransition(TaskState.PROCESS_ASSIGNED, TaskState.READY_FOR_AGENT),
            
            # Agent execution transitions
            StateTransition(TaskState.READY_FOR_AGENT, TaskState.AGENT_RESPONDING),
            StateTransition(TaskState.AGENT_RESPONDING, TaskState.TOOL_PROCESSING),
            StateTransition(TaskState.AGENT_RESPONDING, TaskState.COMPLETED),
            StateTransition(TaskState.AGENT_RESPONDING, TaskState.FAILED),
            
            # Tool processing transitions
            StateTransition(TaskState.TOOL_PROCESSING, TaskState.WAITING_ON_DEPENDENCIES),
            StateTransition(TaskState.TOOL_PROCESSING, TaskState.READY_FOR_AGENT),
            
            # Dependency resolution
            StateTransition(TaskState.WAITING_ON_DEPENDENCIES, TaskState.READY_FOR_AGENT),
            
            # Manual control transitions
            StateTransition(TaskState.READY_FOR_AGENT, TaskState.MANUAL_HOLD),
            StateTransition(TaskState.MANUAL_HOLD, TaskState.READY_FOR_AGENT),
            
            # Failure transitions (any state can fail)
            StateTransition(TaskState.CREATED, TaskState.FAILED),
            StateTransition(TaskState.PROCESS_ASSIGNED, TaskState.FAILED),
            StateTransition(TaskState.READY_FOR_AGENT, TaskState.FAILED),
            StateTransition(TaskState.WAITING_ON_DEPENDENCIES, TaskState.FAILED),
            StateTransition(TaskState.AGENT_RESPONDING, TaskState.FAILED),
            StateTransition(TaskState.TOOL_PROCESSING, TaskState.FAILED),
        ]
        
        # Build transition map for quick lookup
        self._build_transition_map()
    
    def _build_transition_map(self):
        """Build a map of valid transitions for quick lookup."""
        self.transition_map: Dict[TaskState, Set[TaskState]] = {}
        
        for transition in self.transitions:
            if transition.from_state not in self.transition_map:
                self.transition_map[transition.from_state] = set()
            self.transition_map[transition.from_state].add(transition.to_state)
    
    def is_valid_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """Check if a state transition is valid."""
        if from_state not in self.transition_map:
            return False
        return to_state in self.transition_map[from_state]
    
    def get_valid_transitions(self, current_state: TaskState) -> List[TaskState]:
        """Get all valid transitions from the current state."""
        return list(self.transition_map.get(current_state, set()))
    
    async def transition(
        self,
        task_id: int,
        current_state: TaskState,
        new_state: TaskState,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Execute a state transition with validation and logging."""
        # Validate transition
        if not self.is_valid_transition(current_state, new_state):
            if self.event_manager:
                await self.event_manager.log_event(
                    EventType.SYSTEM_WARNING,
                    EntityType.TASK,
                    task_id,
                    event_data={
                        "current_state": current_state.value,
                        "attempted_state": new_state.value,
                        "reason": "Invalid transition",
                        "event": "task_state_change_failed"
                    }
                )
            return False
        
        # Log successful transition
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_UPDATED,
                EntityType.TASK,
                task_id,
                event_data={
                    "old_state": current_state.value,
                    "new_state": new_state.value,
                    "field": "task_state",
                    "metadata": metadata
                }
            )
        
        return True
    
    def is_terminal_state(self, state: TaskState) -> bool:
        """Check if a state is terminal (no further transitions possible)."""
        return state in [TaskState.COMPLETED, TaskState.FAILED]
    
    def is_active_state(self, state: TaskState) -> bool:
        """Check if a state represents active processing."""
        return state in [
            TaskState.AGENT_RESPONDING,
            TaskState.TOOL_PROCESSING,
            TaskState.PROCESS_ASSIGNED
        ]
    
    def is_waiting_state(self, state: TaskState) -> bool:
        """Check if a state represents waiting."""
        return state in [
            TaskState.WAITING_ON_DEPENDENCIES,
            TaskState.MANUAL_HOLD
        ]
    
    def requires_agent_action(self, state: TaskState) -> bool:
        """Check if a state requires agent action."""
        return state == TaskState.READY_FOR_AGENT
    
    def can_be_cancelled(self, state: TaskState) -> bool:
        """Check if a task in this state can be cancelled."""
        return not self.is_terminal_state(state)
    
    def get_state_metadata(self, state: TaskState) -> Dict:
        """Get metadata about a state."""
        return {
            "name": state.value,
            "is_terminal": self.is_terminal_state(state),
            "is_active": self.is_active_state(state),
            "is_waiting": self.is_waiting_state(state),
            "requires_agent": self.requires_agent_action(state),
            "can_be_cancelled": self.can_be_cancelled(state),
            "valid_transitions": [s.value for s in self.get_valid_transitions(state)]
        }