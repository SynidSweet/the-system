"""Process triggered when agent calls break_down_task() tool."""

from typing import Dict, Any, List
import logging

from ..base_process import BaseProcess, ProcessResult
from ...runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class BreakDownTaskProcess(BaseProcess):
    """Handles task breakdown - triggered by agent tool call, not direct LLM orchestration.
    
    This process:
    1. Creates a planning subtask to determine breakdown
    2. Waits for planning agent to complete
    3. Creates actual subtasks based on planning result
    4. Updates parent task dependencies
    """
    
    async def execute(
        self,
        parent_task_id: int,
        breakdown_request: str,
        **tool_args
    ) -> ProcessResult:
        """Execute the task breakdown process."""
        try:
            parent_task = await self.sys.get_task(parent_task_id)
            if not parent_task:
                return ProcessResult(
                    status="failure",
                    data={},
                    error=f"Parent task {parent_task_id} not found"
                )
            
            logger.info(f"Breaking down task {parent_task_id}: {breakdown_request}")
            
            # Create planning subtask
            planning_task_id = await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=f"Break down this task: {parent_task.instruction}. Approach: {breakdown_request}",
                assigned_agent="planning_agent",
                additional_context=[
                    "planning_agent_guide",
                    "task_breakdown_patterns"
                ],
                priority=tool_args.get("priority", "normal"),
                metadata={
                    "parent_task": parent_task.instruction,
                    "breakdown_approach": breakdown_request,
                    "parent_context": parent_task.additional_context
                }
            )
            
            # Wait for planning to complete
            results = await self.sys.wait_for_tasks([planning_task_id])
            if not results or results[0].status != "success":
                return ProcessResult(
                    status="failure",
                    data={},
                    error="Planning agent failed to break down task"
                )
            
            breakdown_result = results[0].data
            subtask_specs = breakdown_result.get("subtasks", [])
            
            if not subtask_specs:
                return ProcessResult(
                    status="success",
                    data={
                        "subtasks_created": [],
                        "summary": "No subtasks needed based on analysis"
                    }
                )
            
            # Create the actual subtasks based on planning result
            subtask_ids = []
            for subtask_spec in subtask_specs:
                subtask_id = await self._create_subtask_from_spec(
                    parent_task_id,
                    subtask_spec
                )
                if subtask_id:
                    subtask_ids.append(subtask_id)
            
            # Update parent task status - it's now broken down and waiting for subtasks
            if subtask_ids:
                await self.sys.add_task_dependencies(parent_task_id, subtask_ids)
                await self.sys.update_task_state(parent_task_id, TaskState.WAITING_ON_DEPENDENCIES)
            
            # Build summary
            summary = self._build_breakdown_summary(subtask_specs, subtask_ids)
            
            # Add system message to parent task
            await self.sys.add_system_message(parent_task_id, summary)
            
            return ProcessResult(
                status="success",
                data={
                    "subtasks_created": subtask_ids,
                    "summary": summary,
                    "breakdown_plan": breakdown_result
                },
                subtasks_created=subtask_ids
            )
            
        except Exception as e:
            return await self.handle_error(e, parent_task_id=parent_task_id)
    
    async def _create_subtask_from_spec(
        self,
        parent_task_id: int,
        subtask_spec: Dict[str, Any]
    ) -> Optional[int]:
        """Create a subtask from planning specification."""
        try:
            # Extract subtask details
            instruction = subtask_spec.get("instruction", "")
            if not instruction:
                logger.warning("Subtask spec missing instruction")
                return None
            
            # Create the subtask
            subtask_id = await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=instruction,
                assigned_agent=subtask_spec.get("suggested_agent"),
                assigned_process=subtask_spec.get("suggested_process", "neutral_task"),
                priority=subtask_spec.get("priority", "normal"),
                additional_context=subtask_spec.get("context", []),
                additional_tools=subtask_spec.get("tools", []),
                metadata={
                    "dependencies": subtask_spec.get("dependencies", []),
                    "estimated_complexity": subtask_spec.get("complexity", "medium")
                }
            )
            
            return subtask_id
            
        except Exception as e:
            logger.error(f"Failed to create subtask: {e}")
            return None
    
    def _build_breakdown_summary(
        self,
        subtask_specs: List[Dict],
        created_ids: List[int]
    ) -> str:
        """Build a summary of the task breakdown."""
        if not created_ids:
            return "Task breakdown completed, but no subtasks were created."
        
        lines = [f"Task broken down into {len(created_ids)} subtasks:"]
        
        for i, (spec, task_id) in enumerate(zip(subtask_specs, created_ids), 1):
            instruction = spec.get("instruction", "Unknown")
            # Truncate long instructions
            if len(instruction) > 100:
                instruction = instruction[:97] + "..."
            lines.append(f"{i}. [{task_id}] {instruction}")
        
        return "\n".join(lines)
    
    async def validate_parameters(
        self,
        parent_task_id: int = None,
        breakdown_request: str = None,
        **kwargs
    ) -> bool:
        """Validate process parameters."""
        if parent_task_id is None:
            logger.error("BreakDownTaskProcess requires parent_task_id")
            return False
        
        if not breakdown_request:
            logger.error("BreakDownTaskProcess requires breakdown_request")
            return False
        
        return True