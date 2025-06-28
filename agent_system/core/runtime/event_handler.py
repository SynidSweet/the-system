"""Event handler for the runtime engine."""

import logging
from typing import Dict, Any, TYPE_CHECKING

from .state_machine import TaskState
from ..events.event_types import EventType, EntityType

if TYPE_CHECKING:
    from .engine import RuntimeEngine, RuntimeEvent


logger = logging.getLogger(__name__)


class RuntimeEventHandler:
    """Handles events for the runtime engine."""
    
    def __init__(self, runtime: 'RuntimeEngine'):
        self.runtime = runtime
        
        # Map event types to handler methods
        self.handlers = {
            "task_created": self.on_task_created,
            "task_state_changed": self.on_task_state_changed,
            "execute_process": self.on_execute_process,
            "process_completed": self.on_process_completed,
            "agent_response_received": self.on_agent_response,
            "tool_call_made": self.on_tool_call,
            "subtask_completed": self.on_subtask_completed,
            "dependency_resolved": self.on_dependency_resolved,
            "dependency_failed": self.on_dependency_failed,
            "end_task_requested": self.on_end_task_requested
        }
    
    async def handle_event(self, event: 'RuntimeEvent'):
        """Route event to appropriate handler."""
        handler = self.handlers.get(event.event_type)
        
        if handler:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}", exc_info=True)
                raise
        else:
            logger.warning(f"No handler for event type: {event.event_type}")
    
    async def on_task_created(self, event: 'RuntimeEvent'):
        """Handle task creation event."""
        task_id = event.task_id
        process_name = event.data.get("process", "neutral_task")
        
        logger.debug(f"Task {task_id} created with process {process_name}")
        
        # Assign process to task
        await self.runtime.update_task_state(task_id, TaskState.PROCESS_ASSIGNED)
        
        # Trigger process execution (this will be implemented with process system)
        from .engine import RuntimeEvent
        await self.runtime.queue_event(RuntimeEvent(
            event_type="execute_process",
            task_id=task_id,
            data={"process": process_name},
            timestamp=event.timestamp
        ))
    
    async def on_execute_process(self, event: 'RuntimeEvent'):
        """Handle process execution event."""
        task_id = event.task_id
        process_name = event.data.get("process", "neutral_task")
        
        logger.debug(f"Executing process {process_name} for task {task_id}")
        
        # For now, just move the task to READY_FOR_AGENT state
        # In a full implementation, this would execute the actual process
        await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_task_state_changed(self, event: 'RuntimeEvent'):
        """Handle task state change event."""
        task_id = event.task_id
        new_state = TaskState(event.data["new_state"])
        
        logger.debug(f"Task {task_id} state changed to {new_state.value}")
        
        # Handle state-specific actions
        if new_state == TaskState.READY_FOR_AGENT:
            # Check if we should trigger agent call
            if self.runtime.settings.auto_trigger_enabled:
                await self.runtime.trigger_agent_call(task_id)
        
        elif new_state == TaskState.COMPLETED:
            # Check for parent task to notify
            task_entity = await self.runtime.entity_manager.get_entity(EntityType.TASK, task_id)
            if task_entity and task_entity.parent_task_id:
                await self.runtime.queue_event({
                    "event_type": "subtask_completed",
                    "task_id": task_entity.parent_task_id,
                    "data": {"subtask_id": task_id},
                    "timestamp": event.timestamp
                })
    
    async def on_process_completed(self, event: 'RuntimeEvent'):
        """Handle process completion event."""
        task_id = event.task_id
        
        logger.debug(f"Process completed for task {task_id}")
        
        # Process assigns agent and sets up task, so move to ready state
        await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_agent_response(self, event: 'RuntimeEvent'):
        """Handle agent response event."""
        task_id = event.task_id
        response = event.data.get("response", {})
        
        logger.debug(f"Agent response received for task {task_id}")
        
        # Check for tool calls
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            await self.runtime.update_task_state(task_id, TaskState.TOOL_PROCESSING)
            
            # Queue tool processing events
            for tool_call in tool_calls:
                await self.runtime.queue_event({
                    "event_type": "tool_call_made",
                    "task_id": task_id,
                    "data": {"tool_call": tool_call},
                    "timestamp": event.timestamp
                })
        else:
            # No tools, agent continues or completes
            if response.get("task_complete", False):
                await self.runtime.complete_task(task_id, response.get("result", {}))
            else:
                # Agent wants to continue
                await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_tool_call(self, event: 'RuntimeEvent'):
        """Handle tool call event."""
        task_id = event.task_id
        tool_call = event.data["tool_call"]
        tool_name = tool_call.get("name")
        
        logger.debug(f"Tool call {tool_name} for task {task_id}")
        
        # Check if tool triggers a process
        process_triggers = {
            "break_down_task": self._handle_break_down_task,
            "start_subtask": self._handle_start_subtask,
            "end_task": self._handle_end_task,
            "request_context": self._handle_request_context,
            "request_tools": self._handle_request_tools,
            "flag_for_review": self._handle_flag_for_review
        }
        
        handler = process_triggers.get(tool_name)
        if handler:
            await handler(task_id, tool_call)
        else:
            # Regular tool execution
            await self._execute_regular_tool(task_id, tool_call)
    
    async def _handle_break_down_task(self, task_id: int, tool_call: Dict):
        """Handle break_down_task tool call."""
        # This will trigger the BreakDownTaskProcess
        subtask_ids = []  # Will be populated by process
        
        # For now, simulate creating subtasks
        breakdown_request = tool_call.get("arguments", {}).get("breakdown", "")
        
        # Add dependencies
        if subtask_ids:
            await self.runtime.add_task_dependencies(task_id, subtask_ids)
            await self.runtime.update_task_state(task_id, TaskState.WAITING_ON_DEPENDENCIES)
    
    async def _handle_start_subtask(self, task_id: int, tool_call: Dict):
        """Handle start_subtask tool call."""
        instruction = tool_call.get("arguments", {}).get("instruction", "")
        
        # Create subtask
        subtask_id = await self.runtime.create_task(
            instruction=instruction,
            parent_task_id=task_id
        )
        
        # Add as dependency
        await self.runtime.add_task_dependency(task_id, subtask_id)
        await self.runtime.update_task_state(task_id, TaskState.WAITING_ON_DEPENDENCIES)
    
    async def _handle_end_task(self, task_id: int, tool_call: Dict):
        """Handle end_task tool call."""
        result = tool_call.get("arguments", {}).get("result", {})
        
        # Queue end task event
        await self.runtime.queue_event({
            "event_type": "end_task_requested",
            "task_id": task_id,
            "data": {"result": result},
            "timestamp": tool_call.get("timestamp", 0)
        })
    
    async def _handle_request_context(self, task_id: int, tool_call: Dict):
        """Handle request_context tool call."""
        # This will trigger the NeedMoreContextProcess
        context_request = tool_call.get("arguments", {}).get("request", "")
        
        # For now, add context and continue
        await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def _handle_request_tools(self, task_id: int, tool_call: Dict):
        """Handle request_tools tool call."""
        # This will trigger the NeedMoreToolsProcess
        tool_request = tool_call.get("arguments", {}).get("request", "")
        
        # For now, add tools and continue
        await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def _handle_flag_for_review(self, task_id: int, tool_call: Dict):
        """Handle flag_for_review tool call."""
        # This will trigger the FlagForReviewProcess
        flag_reason = tool_call.get("arguments", {}).get("reason", "")
        severity = tool_call.get("arguments", {}).get("severity", "normal")
        
        # Create review subtask
        review_task_id = await self.runtime.create_task(
            instruction=f"Review flagged issue: {flag_reason}",
            parent_task_id=task_id,
            process="review_process"
        )
        
        # Continue parent task while review happens
        await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def _execute_regular_tool(self, task_id: int, tool_call: Dict):
        """Execute a regular tool that doesn't trigger a process."""
        # This would execute the tool and add result to conversation
        tool_name = tool_call.get("name")
        tool_result = f"Tool {tool_name} executed"
        
        # Add tool result to task conversation (would be implemented)
        
        # Continue agent execution
        await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_subtask_completed(self, event: 'RuntimeEvent'):
        """Handle subtask completion event."""
        parent_task_id = event.task_id
        subtask_id = event.data["subtask_id"]
        
        logger.debug(f"Subtask {subtask_id} completed for parent {parent_task_id}")
        
        # Check if all dependencies are resolved
        if await self.runtime.dependency_graph.all_dependencies_resolved(parent_task_id):
            # Add completion message to parent task conversation
            # (would be implemented to add system message)
            
            # Parent can continue
            await self.runtime.update_task_state(parent_task_id, TaskState.READY_FOR_AGENT)
    
    async def on_dependency_resolved(self, event: 'RuntimeEvent'):
        """Handle dependency resolution event."""
        task_id = event.task_id
        
        logger.debug(f"Dependency resolved for task {task_id}")
        
        # Check if all dependencies are resolved
        if await self.runtime.dependency_graph.all_dependencies_resolved(task_id):
            # Task can proceed
            current_state = self.runtime.task_states.get(task_id)
            if current_state == TaskState.WAITING_ON_DEPENDENCIES:
                await self.runtime.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_dependency_failed(self, event: 'RuntimeEvent'):
        """Handle dependency failure event."""
        task_id = event.task_id
        failed_dep = event.data["failed_dependency"]
        reason = event.data["reason"]
        
        logger.warning(f"Dependency {failed_dep} failed for task {task_id}: {reason}")
        
        # Determine if task should fail or try recovery
        # For now, fail the dependent task
        await self.runtime.fail_task(task_id, f"Dependency {failed_dep} failed: {reason}")
    
    async def on_end_task_requested(self, event: 'RuntimeEvent'):
        """Handle end task request."""
        task_id = event.task_id
        result = event.data["result"]
        
        logger.debug(f"End task requested for task {task_id}")
        
        # This would trigger EndTaskProcess for quality evaluation
        # For now, complete the task
        await self.runtime.complete_task(task_id, result)