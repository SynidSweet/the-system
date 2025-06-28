"""Process triggered when agent calls end_task() tool."""

from typing import Dict, Any
import logging

from ..base_process import BaseProcess, ProcessResult
from ...runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class EndTaskProcess(BaseProcess):
    """Handles task completion - triggered by agent tool call.
    
    This process:
    1. Creates evaluation subtask to assess quality
    2. Creates summary subtask to synthesize results
    3. Determines final task state based on evaluation
    4. May create documentation task if recommended
    """
    
    async def execute(
        self,
        task_id: int,
        result: Dict[str, Any],
        agent_assessment: str = "",
        **kwargs
    ) -> ProcessResult:
        """Execute the task completion process."""
        try:
            task = await self.sys.get_task(task_id)
            if not task:
                return ProcessResult(
                    status="failure",
                    data={},
                    error=f"Task {task_id} not found"
                )
            
            logger.info(f"Processing task completion for {task_id}")
            
            # Create evaluation subtask
            evaluation_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Evaluate completion quality of: {task.instruction}",
                assigned_agent="task_evaluator",
                additional_context=["task_evaluator_guide", "quality_standards"],
                priority="high",
                metadata={
                    "task_result": result,
                    "agent_assessment": agent_assessment,
                    "original_task": task.instruction,
                    "task_context": {
                        "agent": task.assigned_agent,
                        "duration": None,  # Would calculate from timestamps
                        "subtask_count": len(task.subtask_ids)
                    }
                }
            )
            
            # Create summary subtask (parallel with evaluation)
            summary_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Summarize outcomes from: {task.instruction}",
                assigned_agent="summary_agent",
                additional_context=["summary_agent_guide", "summarization_patterns"],
                metadata={
                    "task_result": result,
                    "task_context": task.instruction,
                    "result_type": result.get("type", "general")
                }
            )
            
            # Wait for both evaluation and summary
            results = await self.sys.wait_for_tasks([evaluation_task_id, summary_task_id])
            
            # Extract results
            evaluation_result = None
            summary_result = None
            
            for i, result_obj in enumerate(results):
                if i == 0:  # Evaluation result
                    evaluation_result = result_obj
                else:  # Summary result
                    summary_result = result_obj
            
            # Check evaluation outcome
            if not evaluation_result or evaluation_result.status != "success":
                return ProcessResult(
                    status="failure",
                    data={},
                    error="Task evaluation failed"
                )
            
            evaluation_data = evaluation_result.data
            quality_acceptable = evaluation_data.get("quality_acceptable", False)
            
            # Determine final task state based on evaluation
            if quality_acceptable:
                # Update task state to completed
                await self.sys.update_task_state(task_id, TaskState.COMPLETED)
                
                # Set task result
                final_result = {
                    "result": result,
                    "summary": summary_result.data.get("summary", "") if summary_result else "",
                    "evaluation": evaluation_data,
                    "quality_score": evaluation_data.get("quality_score", 0.0)
                }
                
                await self.sys.mark_task_complete(task_id, final_result)
                
                # Add completion message
                await self.sys.add_system_message(
                    task_id,
                    f"Task completed successfully. Quality score: {evaluation_data.get('quality_score', 'N/A')}"
                )
                
                # Create documentation subtask if recommended
                if evaluation_data.get("suggests_documentation", False):
                    await self._create_documentation_task(task_id, task, final_result)
                
                return ProcessResult(
                    status="success",
                    data={
                        "task_completed": True,
                        "quality_acceptable": True,
                        "final_result": final_result
                    }
                )
            else:
                # Task failed evaluation
                failure_reason = evaluation_data.get("failure_reason", "Quality standards not met")
                
                await self.sys.update_task_state(task_id, TaskState.FAILED)
                await self.sys.mark_task_failed(task_id, failure_reason)
                
                # Add failure message
                await self.sys.add_system_message(
                    task_id,
                    f"Task failed evaluation: {failure_reason}"
                )
                
                # Could trigger recovery process here
                recovery_suggestion = evaluation_data.get("recovery_suggestion")
                if recovery_suggestion:
                    await self._create_recovery_task(task_id, task, recovery_suggestion)
                
                return ProcessResult(
                    status="success",  # Process succeeded even though task failed
                    data={
                        "task_completed": False,
                        "quality_acceptable": False,
                        "failure_reason": failure_reason,
                        "recovery_initiated": bool(recovery_suggestion)
                    }
                )
            
        except Exception as e:
            return await self.handle_error(e, task_id=task_id)
    
    async def _create_documentation_task(
        self,
        task_id: int,
        task,
        result: Dict[str, Any]
    ):
        """Create a documentation task for valuable insights."""
        try:
            doc_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Document insights and learnings from: {task.instruction}",
                assigned_agent="documentation_agent",
                additional_context=["documentation_agent_guide", "documentation_standards"],
                priority="low",
                metadata={
                    "task_result": result,
                    "original_task": task.instruction,
                    "document_type": "insight"
                }
            )
            
            logger.info(f"Created documentation task {doc_task_id} for task {task_id}")
            
        except Exception as e:
            logger.warning(f"Failed to create documentation task: {e}")
    
    async def _create_recovery_task(
        self,
        task_id: int,
        task,
        recovery_suggestion: str
    ):
        """Create a recovery task for failed evaluations."""
        try:
            recovery_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Recover from failure: {recovery_suggestion}",
                assigned_agent="recovery_agent",
                additional_context=["recovery_agent_guide", "error_recovery_patterns"],
                priority="high",
                metadata={
                    "failed_task": task.instruction,
                    "recovery_approach": recovery_suggestion,
                    "original_agent": task.assigned_agent
                }
            )
            
            logger.info(f"Created recovery task {recovery_task_id} for task {task_id}")
            
        except Exception as e:
            logger.warning(f"Failed to create recovery task: {e}")
    
    async def validate_parameters(
        self,
        task_id: int = None,
        result: Dict = None,
        **kwargs
    ) -> bool:
        """Validate process parameters."""
        if task_id is None:
            logger.error("EndTaskProcess requires task_id")
            return False
        
        if result is None:
            logger.error("EndTaskProcess requires result")
            return False
        
        return True