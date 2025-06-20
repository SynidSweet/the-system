"""Process triggered when agent calls create_subtask() tool."""

from typing import Dict, Any, Optional
import logging

from agent_system.core.processes.base import BaseProcess, ProcessResult
from agent_system.core.runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class CreateSubtaskProcess(BaseProcess):
    """Handles individual subtask creation requests from agents.
    
    This process:
    1. Creates the requested subtask
    2. Adds it as a dependency to parent task
    3. Updates parent task state to waiting
    """
    
    async def execute(
        self,
        parent_task_id: int,
        subtask_instruction: str,
        **kwargs
    ) -> ProcessResult:
        """Execute the subtask creation process."""
        try:
            parent_task = await self.sys.get_task(parent_task_id)
            if not parent_task:
                return ProcessResult(
                    status="failure",
                    data={},
                    error=f"Parent task {parent_task_id} not found"
                )
            
            logger.info(f"Creating subtask for task {parent_task_id}: {subtask_instruction}")
            
            # Extract optional parameters
            process = kwargs.get("process", "neutral_task")
            priority = kwargs.get("priority", "normal")
            assigned_agent = kwargs.get("assigned_agent")
            context = kwargs.get("context", [])
            tools = kwargs.get("tools", [])
            metadata = kwargs.get("metadata", {})
            
            # Inherit some properties from parent if not specified
            if not assigned_agent and parent_task.assigned_agent:
                # Consider using same agent type for related work
                metadata["parent_agent"] = parent_task.assigned_agent
            
            if not context and parent_task.additional_context:
                # Consider inheriting some context
                relevant_context = self._filter_relevant_context(
                    parent_task.additional_context,
                    subtask_instruction
                )
                if relevant_context:
                    context.extend(relevant_context)
            
            # Create the subtask
            subtask_id = await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=subtask_instruction,
                assigned_process=process,
                priority=priority,
                assigned_agent=assigned_agent,
                additional_context=context,
                additional_tools=tools,
                metadata=metadata
            )
            
            # Add as dependency to parent task
            await self.sys.add_task_dependencies(parent_task_id, [subtask_id])
            
            # Update parent task state
            current_state = parent_task.task_state
            if current_state not in [TaskState.WAITING_ON_DEPENDENCIES, TaskState.COMPLETED, TaskState.FAILED]:
                await self.sys.update_task_state(parent_task_id, TaskState.WAITING_ON_DEPENDENCIES)
            
            # Add system message to parent task
            await self.sys.add_system_message(
                parent_task_id,
                f"Created subtask [{subtask_id}]: {subtask_instruction[:100]}..."
            )
            
            return ProcessResult(
                status="success",
                data={
                    "subtask_id": subtask_id,
                    "instruction": subtask_instruction,
                    "parent_updated": True
                },
                subtasks_created=[subtask_id]
            )
            
        except Exception as e:
            return await self.handle_error(e, parent_task_id=parent_task_id)
    
    def _filter_relevant_context(
        self,
        parent_context: List[str],
        subtask_instruction: str
    ) -> List[str]:
        """Filter parent context for relevance to subtask."""
        # Simple heuristic - include general guides and patterns
        relevant = []
        
        general_patterns = ["guide", "pattern", "standard", "reference"]
        instruction_lower = subtask_instruction.lower()
        
        for context_doc in parent_context:
            doc_lower = context_doc.lower()
            
            # Include if it's a general guide
            if any(pattern in doc_lower for pattern in general_patterns):
                relevant.append(context_doc)
            
            # Include if it mentions something in the instruction
            elif any(word in doc_lower for word in instruction_lower.split() if len(word) > 4):
                relevant.append(context_doc)
        
        return relevant[:3]  # Limit to avoid context overload
    
    async def validate_parameters(
        self,
        parent_task_id: int = None,
        subtask_instruction: str = None,
        **kwargs
    ) -> bool:
        """Validate process parameters."""
        if parent_task_id is None:
            logger.error("CreateSubtaskProcess requires parent_task_id")
            return False
        
        if not subtask_instruction:
            logger.error("CreateSubtaskProcess requires subtask_instruction")
            return False
        
        return True