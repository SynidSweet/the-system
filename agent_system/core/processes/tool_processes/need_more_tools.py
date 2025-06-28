"""Process for handling tool requests from agents."""

import logging
from typing import Dict, Any, Optional

from ..base import BaseProcess, ProcessResult
from ...entities.task_entity import TaskEntity
from ...events.event_types import EntityType

logger = logging.getLogger(__name__)


class NeedMoreToolsProcess(BaseProcess):
    """Process to handle agent requests for additional tools."""
    
    # Process metadata defined in class attributes
    # The parent BaseProcess class handles these through the registry
    
    async def execute(self, requesting_task_id: int, tool_request: str, 
                     justification: str, **kwargs) -> ProcessResult:
        """
        Execute the tool request process.
        
        Args:
            requesting_task_id: ID of the task requesting tools
            tool_request: Description of the tool capability needed
            justification: Reason why the tool is necessary
            
        Returns:
            Dict with process results including assigned tools
        """
        try:
            # Get the requesting task
            requesting_task = await self.sys.get_task(requesting_task_id)
            if not requesting_task:
                raise ValueError(f"Requesting task {requesting_task_id} not found")
            
            # Create a task for the tool addition agent to evaluate the request
            tool_eval_task_id = await self.sys.create_task(
                instruction=f"Evaluate tool request: '{tool_request}' with justification: '{justification}'",
                parent_task_id=requesting_task_id,
                assigned_agent="tool_addition",
                metadata={
                    "type": "tool_request_evaluation",
                    "requesting_task_id": requesting_task_id,
                    "tool_request": tool_request,
                    "justification": justification,
                    "current_tools": requesting_task.metadata.get("available_tools", [])
                }
            )
            
            # Create a task for request validation
            validation_task_id = await self.sys.create_task(
                instruction=f"Validate tool request necessity and security: '{tool_request}'",
                parent_task_id=tool_eval_task_id,
                assigned_agent="request_validation",
                metadata={
                    "type": "tool_request_validation",
                    "tool_request": tool_request,
                    "justification": justification
                }
            )
            
            # Log the tool request
            await self.sys.log_event(
                event_type="TOOL_REQUEST",
                entity_type=EntityType.TASK,
                entity_id=requesting_task_id,
                metadata={
                    "tool_request": tool_request,
                    "justification": justification,
                    "evaluation_task_id": tool_eval_task_id,
                    "validation_task_id": validation_task_id
                }
            )
            
            # Note: The actual tool assignment will be done by the tool_addition agent
            # after validation. This process just creates the necessary tasks.
            
            return ProcessResult(
                status="success",
                data={
                    "status": "tool_request_submitted",
                    "evaluation_task_id": tool_eval_task_id,
                    "validation_task_id": validation_task_id,
                    "message": "Tool request submitted for evaluation and validation"
                }
            )
            
        except Exception as e:
            return await self.handle_error(e, requesting_task_id=requesting_task_id, tool_request=tool_request)
    
    async def validate_parameters(
        self,
        requesting_task_id: int = None,
        tool_request: str = None,
        justification: str = None,
        **kwargs
    ) -> bool:
        """Validate process parameters."""
        if requesting_task_id is None:
            logger.error("NeedMoreToolsProcess requires requesting_task_id")
            return False
        
        if not tool_request:
            logger.error("NeedMoreToolsProcess requires tool_request")
            return False
        
        if not justification:
            logger.error("NeedMoreToolsProcess requires justification")
            return False
        
        return True