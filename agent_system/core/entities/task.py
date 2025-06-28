"""Task entity implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from ..entities.base import Entity, EntityState
from ..events.event_types import EntityType, EventType


class TaskState(str, Enum):
    """Task-specific states aligned with runtime specification."""
    CREATED = "created"
    PROCESS_ASSIGNED = "process_assigned"
    READY_FOR_AGENT = "ready_for_agent"
    WAITING_ON_DEPENDENCIES = "waiting_on_dependencies"
    AGENT_RESPONDING = "agent_responding"
    TOOL_PROCESSING = "tool_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_HOLD = "manual_hold"


class TaskEntity(Entity):
    """Entity representation of a task."""
    
    def __init__(
        self,
        entity_id: int,
        name: str,
        instruction: str,
        parent_task_id: Optional[int] = None,
        tree_id: Optional[int] = None,
        assigned_agent: Optional[str] = None,
        assigned_process: Optional[str] = None,
        task_state: TaskState = TaskState.CREATED,
        priority: str = "normal",
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        additional_context: Optional[List[str]] = None,
        additional_tools: Optional[List[str]] = None,
        dependencies: Optional[List[int]] = None,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            entity_type=EntityType.TASK,
            version=version,
            state=state,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.instruction = instruction
        self.parent_task_id = parent_task_id
        self.tree_id = tree_id or entity_id  # Root tasks have tree_id = entity_id
        self.assigned_agent = assigned_agent
        self.assigned_process = assigned_process or "neutral_task"
        self.task_state = task_state
        self.priority = priority
        self.result = result
        self.error = error
        self.additional_context = additional_context or []
        self.additional_tools = additional_tools or []
        self.dependencies = dependencies or []
        
        # Task-specific tracking
        self.subtask_ids: List[int] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []
    
    async def validate(self) -> bool:
        """Validate task configuration."""
        # Basic validation
        if not self.name or not self.instruction:
            return False
        
        # Ensure instruction is meaningful
        if len(self.instruction) < 5:
            return False
        
        # Validate priority
        if self.priority not in ["low", "normal", "high", "critical"]:
            return False
        
        # Validate task state
        if not isinstance(self.task_state, TaskState):
            return False
        
        return True
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert task entity to dictionary."""
        base_dict = await super().to_dict()
        base_dict.update({
            "instruction": self.instruction,
            "parent_task_id": self.parent_task_id,
            "tree_id": self.tree_id,
            "assigned_agent": self.assigned_agent,
            "assigned_process": self.assigned_process,
            "task_state": self.task_state.value,
            "priority": self.priority,
            "result": self.result,
            "error": self.error,
            "additional_context": self.additional_context,
            "additional_tools": self.additional_tools,
            "dependencies": self.dependencies,
            "subtask_ids": self.subtask_ids,
            "conversation_history": self.conversation_history,
            "tool_calls": self.tool_calls
        })
        return base_dict
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'TaskEntity':
        """Create task entity from dictionary."""
        entity = cls(
            entity_id=data["entity_id"],
            name=data["name"],
            instruction=data["instruction"],
            parent_task_id=data.get("parent_task_id"),
            tree_id=data.get("tree_id"),
            assigned_agent=data.get("assigned_agent"),
            assigned_process=data.get("assigned_process", "neutral_task"),
            task_state=TaskState(data.get("task_state", "created")),
            priority=data.get("priority", "normal"),
            result=data.get("result"),
            error=data.get("error"),
            additional_context=data.get("additional_context", []),
            additional_tools=data.get("additional_tools", []),
            dependencies=data.get("dependencies", []),
            version=data.get("version", "1.0.0"),
            state=EntityState(data.get("state", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Restore relationships and task-specific data
        entity.relationships = data.get("relationships", {})
        entity.subtask_ids = data.get("subtask_ids", [])
        entity.conversation_history = data.get("conversation_history", [])
        entity.tool_calls = data.get("tool_calls", [])
        
        return entity
    
    async def update_task_state(self, new_state: TaskState) -> bool:
        """Update task state with proper event logging."""
        old_state = self.task_state
        self.task_state = new_state
        self.updated_at = datetime.now()
        
        # Update entity state based on task state
        if new_state == TaskState.COMPLETED:
            self.state = EntityState.INACTIVE
        elif new_state == TaskState.FAILED:
            self.state = EntityState.FAILED
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.TASK_STATE_CHANGED,
                EntityType.TASK,
                self.entity_id,
                old_state=old_state.value,
                new_state=new_state.value
            )
        
        return True
    
    async def add_subtask(self, subtask_id: int) -> bool:
        """Add a subtask to this task."""
        if subtask_id not in self.subtask_ids:
            self.subtask_ids.append(subtask_id)
            self.dependencies.append(subtask_id)
            
            # Add parent-child relationship
            await self.add_relationship("has_subtask", subtask_id)
            
            return True
        return False
    
    async def add_dependency(self, task_id: int) -> bool:
        """Add a dependency to this task."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            
            # Add dependency relationship
            await self.add_relationship("depends_on", task_id)
            
            return True
        return False
    
    async def complete_with_result(self, result: Dict[str, Any]) -> bool:
        """Complete the task with a result."""
        self.result = result
        await self.update_task_state(TaskState.COMPLETED)
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.TASK_COMPLETED,
                EntityType.TASK,
                self.entity_id,
                result=result
            )
        
        return True
    
    async def fail_with_error(self, error: str) -> bool:
        """Fail the task with an error."""
        self.error = error
        await self.update_task_state(TaskState.FAILED)
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.TASK_FAILED,
                EntityType.TASK,
                self.entity_id,
                error=error
            )
        
        return True
    
    async def add_conversation_message(self, message: Dict[str, Any]) -> bool:
        """Add a message to the conversation history."""
        self.conversation_history.append(message)
        self.updated_at = datetime.now()
        return True
    
    async def add_tool_call(self, tool_call: Dict[str, Any]) -> bool:
        """Record a tool call made during task execution."""
        self.tool_calls.append(tool_call)
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.TOOL_EXECUTED,
                EntityType.TASK,
                self.entity_id,
                tool_name=tool_call.get("name"),
                tool_args=tool_call.get("arguments")
            )
        
        return True