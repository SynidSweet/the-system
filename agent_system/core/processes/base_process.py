"""Base process class for all Python-based processes."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass

from ..entities.entity_manager import EntityManager
from ..entities.task import TaskEntity, TaskState
from ..events.event_manager import EventManager
from ..events.event_types import EventType, EntityType


logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of process execution."""
    status: str  # "success", "failure", "partial"
    data: Dict[str, Any]
    error: Optional[str] = None
    subtasks_created: List[int] = None
    rollback_needed: bool = False


@dataclass
class AgentResult:
    """Result from agent LLM call."""
    content: str
    tool_calls: List[Dict[str, Any]] = None
    completed: bool = False
    result_data: Optional[Dict[str, Any]] = None


class SystemFunctions:
    """System functions available to all processes."""
    
    def __init__(
        self,
        entity_manager: EntityManager,
        event_manager: EventManager
    ):
        self.entity_manager = entity_manager
        self.event_manager = event_manager
    
    # Task Lifecycle Management
    
    async def create_task(
        self,
        instruction: str,
        process: str = "neutral_task",
        parent_id: Optional[int] = None,
        **kwargs
    ) -> int:
        """Create task and immediately apply specified process."""
        task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"Task: {instruction[:50]}...",
            instruction=instruction,
            parent_task_id=parent_id,
            assigned_process=process,
            task_state=TaskState.CREATED,
            **kwargs
        )
        
        # Log task creation
        await self.event_manager.log_event(
            EventType.TASK_CREATED,
            EntityType.TASK,
            task.entity_id,
            process=process,
            parent_id=parent_id
        )
        
        return task.entity_id
    
    async def create_subtask(
        self,
        parent_id: int,
        instruction: str,
        **kwargs
    ) -> int:
        """Create subtask with parent relationship and dependency tracking."""
        # Get parent task to inherit some properties
        parent_task = await self.entity_manager.get_entity(EntityType.TASK, parent_id)
        if not parent_task:
            raise ValueError(f"Parent task {parent_id} not found")
        
        # Create subtask
        subtask_id = await self.create_task(
            instruction=instruction,
            parent_id=parent_id,
            tree_id=parent_task.tree_id,
            **kwargs
        )
        
        # Add parent-child relationship
        subtask = await self.entity_manager.get_entity(EntityType.TASK, subtask_id)
        await parent_task.add_subtask(subtask_id)
        await self.entity_manager.update_entity(parent_task)
        
        return subtask_id
    
    async def get_task(self, task_id: int) -> Optional[TaskEntity]:
        """Retrieve complete task entity with current status."""
        return await self.entity_manager.get_entity(EntityType.TASK, task_id)
    
    async def update_task(self, task_id: int, **updates) -> bool:
        """Update task entity fields and log change event."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        return await self.entity_manager.update_entity(task, **updates)
    
    async def update_task_state(self, task_id: int, new_state: TaskState) -> bool:
        """Update task state."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await task.update_task_state(new_state)
        return await self.entity_manager.update_entity(task)
    
    async def mark_task_complete(self, task_id: int, result: Dict[str, Any]) -> bool:
        """Mark task complete and trigger dependent task processing."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await task.complete_with_result(result)
        return await self.entity_manager.update_entity(task)
    
    async def mark_task_failed(self, task_id: int, error: str) -> bool:
        """Mark task failed and trigger recovery processes if configured."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await task.fail_with_error(error)
        return await self.entity_manager.update_entity(task)
    
    # Process Orchestration
    
    async def execute_process(
        self,
        process_name: str,
        **parameters
    ) -> ProcessResult:
        """Execute named process with parameters."""
        # This will be implemented to actually execute processes
        # For now, return placeholder
        return ProcessResult(
            status="success",
            data={"process": process_name, "parameters": parameters}
        )
    
    async def call_agent(
        self,
        agent_type: str,
        instruction: str,
        context: List[str] = None,
        parameters: Dict = None
    ) -> AgentResult:
        """Make strategic LLM call to specified agent type."""
        # This will be implemented to actually call agents
        # For now, return placeholder
        return AgentResult(
            content=f"Agent {agent_type} response for: {instruction}",
            completed=False
        )
    
    async def wait_for_tasks(
        self,
        task_ids: List[int],
        timeout: Optional[int] = None
    ) -> List[ProcessResult]:
        """Wait for completion of specified tasks."""
        results = []
        
        # Set up timeout if specified
        start_time = datetime.now()
        
        while task_ids:
            remaining_tasks = []
            
            for task_id in task_ids:
                task = await self.get_task(task_id)
                if task and task.task_state in [TaskState.COMPLETED, TaskState.FAILED]:
                    # Task is done
                    if task.task_state == TaskState.COMPLETED:
                        results.append(ProcessResult(
                            status="success",
                            data=task.result or {}
                        ))
                    else:
                        results.append(ProcessResult(
                            status="failure",
                            data={},
                            error=task.error
                        ))
                else:
                    remaining_tasks.append(task_id)
            
            task_ids = remaining_tasks
            
            if task_ids:
                # Check timeout
                if timeout and (datetime.now() - start_time).seconds > timeout:
                    # Timeout reached
                    for task_id in task_ids:
                        results.append(ProcessResult(
                            status="failure",
                            data={},
                            error="Timeout waiting for task completion"
                        ))
                    break
                
                # Wait before checking again
                await asyncio.sleep(0.5)
        
        return results
    
    async def get_task_result(self, task_id: int) -> Optional[ProcessResult]:
        """Get result of a completed task."""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        if task.task_state == TaskState.COMPLETED:
            return ProcessResult(
                status="success",
                data=task.result or {}
            )
        elif task.task_state == TaskState.FAILED:
            return ProcessResult(
                status="failure",
                data={},
                error=task.error
            )
        else:
            return None
    
    # Resource Management
    
    async def add_context_to_task(
        self,
        task_id: int,
        context_docs: List[str]
    ) -> bool:
        """Add context documents to task entity."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        task.additional_context.extend(context_docs)
        return await self.entity_manager.update_entity(task)
    
    async def add_tools_to_task(
        self,
        task_id: int,
        tools: List[str]
    ) -> bool:
        """Add tools to task entity."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        task.additional_tools.extend(tools)
        return await self.entity_manager.update_entity(task)
    
    async def create_context_document(
        self,
        name: str,
        content: str,
        **metadata
    ) -> str:
        """Create new context document entity."""
        from ..entities.context import ContextCategory, ContextFormat
        
        doc = await self.entity_manager.create_entity(
            EntityType.DOCUMENT,
            name=name,
            title=metadata.get('title', name),
            content=content,
            category=metadata.get('category', ContextCategory.KNOWLEDGE),
            format=metadata.get('format', ContextFormat.MARKDOWN),
            **metadata
        )
        
        return doc.name
    
    # Dependency and Event Management
    
    async def add_task_dependencies(
        self,
        task_id: int,
        dependency_ids: List[int]
    ) -> bool:
        """Add dependencies to a task."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        for dep_id in dependency_ids:
            await task.add_dependency(dep_id)
        
        return await self.entity_manager.update_entity(task)
    
    async def log_event(
        self,
        event_type: str,
        entity_id: int,
        **data
    ) -> bool:
        """Log system event for optimization analysis."""
        await self.event_manager.log_event(
            EventType(event_type),
            EntityType.PROCESS,
            entity_id,
            **data
        )
        return True
    
    async def add_system_message(
        self,
        task_id: int,
        message: str
    ) -> bool:
        """Add system message to task conversation."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await task.add_conversation_message({
            "role": "system",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        return await self.entity_manager.update_entity(task)
    
    # Performance and Optimization
    
    async def get_entity_performance_data(
        self,
        entity_type: str,
        entity_id: int
    ) -> Dict[str, Any]:
        """Retrieve performance analytics for entity optimization."""
        # This would aggregate performance data
        # For now, return placeholder
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "execution_count": 0,
            "success_rate": 0.0,
            "average_duration": 0.0
        }


class BaseProcess(ABC):
    """Abstract base class for all processes."""
    
    def __init__(
        self,
        entity_manager: EntityManager,
        event_manager: EventManager
    ):
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        self.sys = SystemFunctions(entity_manager, event_manager)
        
        # Process metadata
        self.name = self.__class__.__name__
        self.can_rollback = False
        self.rollback_data: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ProcessResult:
        """Execute the process with given parameters."""
        pass
    
    async def validate_parameters(self, **kwargs) -> bool:
        """Validate process parameters before execution."""
        return True
    
    async def rollback(self) -> bool:
        """Rollback process changes if supported."""
        if not self.can_rollback:
            logger.warning(f"Process {self.name} does not support rollback")
            return False
        
        # Implement rollback logic in subclasses
        return False
    
    async def log_start(self, **kwargs):
        """Log process start event."""
        await self.event_manager.log_event(
            EventType.PROCESS_STARTED,
            EntityType.PROCESS,
            0,  # Process entity ID would be retrieved
            process_name=self.name,
            parameters=kwargs
        )
    
    async def log_completion(self, result: ProcessResult):
        """Log process completion event."""
        await self.event_manager.log_event(
            EventType.PROCESS_COMPLETED,
            EntityType.PROCESS,
            0,  # Process entity ID would be retrieved
            process_name=self.name,
            status=result.status,
            error=result.error
        )
    
    async def handle_error(self, error: Exception, **kwargs) -> ProcessResult:
        """Handle process execution error."""
        error_str = str(error)
        logger.error(f"Process {self.name} failed: {error_str}", exc_info=True)
        
        await self.event_manager.log_event(
            EventType.PROCESS_FAILED,
            EntityType.PROCESS,
            0,  # Process entity ID would be retrieved
            process_name=self.name,
            error=error_str,
            parameters=kwargs
        )
        
        return ProcessResult(
            status="failure",
            data={},
            error=error_str,
            rollback_needed=self.can_rollback
        )