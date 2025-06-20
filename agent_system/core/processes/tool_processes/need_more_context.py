"""Process triggered when agent calls need_more_context() tool."""

from typing import Dict, Any, List
import logging

from agent_system.core.processes.base import BaseProcess, ProcessResult
from agent_system.core.runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class NeedMoreContextProcess(BaseProcess):
    """Handles agent requests for additional context during task execution.
    
    This process:
    1. Validates the context request
    2. Creates context provision subtask if approved
    3. May create investigation subtask for complex requests
    4. Updates parent task with new context
    """
    
    async def execute(
        self,
        requesting_task_id: int,
        context_request: str,
        justification: str = "",
        **kwargs
    ) -> ProcessResult:
        """Execute the context request process."""
        try:
            requesting_task = await self.sys.get_task(requesting_task_id)
            if not requesting_task:
                return ProcessResult(
                    status="failure",
                    data={},
                    error=f"Requesting task {requesting_task_id} not found"
                )
            
            logger.info(f"Processing context request for task {requesting_task_id}: {context_request}")
            
            # Create validation subtask first
            validation_result = await self._validate_request(
                requesting_task_id,
                requesting_task,
                context_request,
                justification
            )
            
            if not validation_result.get("approved", False):
                # Add denial message to requesting task conversation
                denial_message = f"Context request denied: {validation_result.get('feedback', 'Request not justified')}"
                await self.sys.add_system_message(requesting_task_id, denial_message)
                
                # Parent task can continue without additional context
                await self.sys.update_task_state(requesting_task_id, TaskState.READY_FOR_AGENT)
                
                return ProcessResult(
                    status="success",
                    data={
                        "request_approved": False,
                        "feedback": validation_result.get("feedback")
                    }
                )
            
            # Request approved - create context provision subtask
            subtask_ids = []
            
            context_task_id = await self.sys.create_subtask(
                parent_id=requesting_task_id,
                instruction=f"Provide context for: {context_request}",
                assigned_agent="context_addition",
                additional_context=["context_addition_guide", "context_optimization_guide"],
                priority="high",
                metadata={
                    "context_request": context_request,
                    "task_context": requesting_task.instruction,
                    "current_context": requesting_task.additional_context,
                    "justification": justification
                }
            )
            subtask_ids.append(context_task_id)
            
            # Create investigation subtask if validation says it's needed
            if validation_result.get("requires_investigation", False):
                investigation_task_id = await self.sys.create_subtask(
                    parent_id=requesting_task_id,
                    instruction=f"Investigate and gather information: {context_request}",
                    assigned_agent="investigator_agent",
                    additional_context=["investigator_agent_guide", "investigation_patterns"],
                    priority="high",
                    metadata={
                        "investigation_request": context_request,
                        "investigation_scope": validation_result.get("investigation_scope", "general")
                    }
                )
                subtask_ids.append(investigation_task_id)
            
            # Parent task waits for context provision
            await self.sys.add_task_dependencies(requesting_task_id, subtask_ids)
            await self.sys.update_task_state(requesting_task_id, TaskState.WAITING_ON_DEPENDENCIES)
            
            # Add system message about context provision
            message = f"Context provision initiated for: {context_request}"
            if len(subtask_ids) > 1:
                message += " (including investigation)"
            await self.sys.add_system_message(requesting_task_id, message)
            
            return ProcessResult(
                status="success",
                data={
                    "request_approved": True,
                    "subtasks_created": subtask_ids,
                    "includes_investigation": len(subtask_ids) > 1
                },
                subtasks_created=subtask_ids
            )
            
        except Exception as e:
            return await self.handle_error(e, requesting_task_id=requesting_task_id)
    
    async def _validate_request(
        self,
        task_id: int,
        task,
        request: str,
        justification: str
    ) -> Dict[str, Any]:
        """Validate the context request."""
        # For now, use simple heuristics
        # In full implementation, this could be a subtask
        
        # Check if task already has extensive context
        if len(task.additional_context) > 10:
            return {
                "approved": False,
                "feedback": "Task already has extensive context. Please be more specific about what's missing."
            }
        
        # Check if request is specific enough
        if len(request.split()) < 5:
            return {
                "approved": False,
                "feedback": "Context request too vague. Please provide more specific details about what context is needed."
            }
        
        # Check for investigation needs
        investigation_keywords = ["research", "investigate", "explore", "find out", "discover", "analyze"]
        requires_investigation = any(
            keyword in request.lower() 
            for keyword in investigation_keywords
        )
        
        # Generally approve with justification
        if justification and len(justification) > 20:
            return {
                "approved": True,
                "requires_investigation": requires_investigation,
                "investigation_scope": "targeted" if len(request.split()) < 20 else "broad"
            }
        
        # Approve simple requests
        return {
            "approved": True,
            "requires_investigation": requires_investigation
        }
    
    async def _process_context_results(
        self,
        task_id: int,
        context_results: List[ProcessResult]
    ) -> List[str]:
        """Process results from context provision subtasks."""
        new_context_docs = []
        
        for result in context_results:
            if result.status == "success":
                docs = result.data.get("context_documents", [])
                new_context_docs.extend(docs)
                
                # Also check for investigation findings
                findings = result.data.get("investigation_findings")
                if findings:
                    # Create a new context document from findings
                    doc_name = await self.sys.create_context_document(
                        name=f"investigation_findings_{task_id}",
                        content=findings,
                        title="Investigation Findings",
                        category="knowledge"
                    )
                    new_context_docs.append(doc_name)
        
        return new_context_docs
    
    async def validate_parameters(
        self,
        requesting_task_id: int = None,
        context_request: str = None,
        **kwargs
    ) -> bool:
        """Validate process parameters."""
        if requesting_task_id is None:
            logger.error("NeedMoreContextProcess requires requesting_task_id")
            return False
        
        if not context_request:
            logger.error("NeedMoreContextProcess requires context_request")
            return False
        
        return True