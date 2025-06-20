"""Message User MCP Server - User communication capabilities."""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent_system.tools.mcp_servers.base import MCPServer
from agent_system.core.permissions.manager import DatabasePermissionManager
from agent_system.core.websocket_messages import send_websocket_message

logger = logging.getLogger(__name__)


class UserInterface:
    """Interface for user communication."""
    
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.message_history = []
        
    async def send_message(self, content: str, message_type: str = "info",
                          source_agent: str = None, source_task: int = None) -> bool:
        """Send a message to the user."""
        message = {
            "content": content,
            "type": message_type,
            "source_agent": source_agent,
            "source_task": source_task,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to history
        self.message_history.append(message)
        
        # Send via WebSocket if available
        try:
            await send_websocket_message({
                "type": "user_message",
                "data": message
            })
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")
        
        # Add to queue for other consumers
        await self.message_queue.put(message)
        
        logger.info(f"Sent {message_type} message from {source_agent}")
        return True
    
    async def send_structured_message(self, structured_content: Dict[str, Any]) -> bool:
        """Send a structured message with sections."""
        # Send via WebSocket if available
        try:
            await send_websocket_message({
                "type": "structured_message",
                "data": structured_content
            })
        except Exception as e:
            logger.warning(f"Failed to send structured WebSocket message: {e}")
        
        # Add to history
        self.message_history.append({
            "type": "structured",
            "content": structured_content,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Sent structured message: {structured_content.get('title', 'Untitled')}")
        return True


class MessageUserMCP(MCPServer):
    """MCP server for user communication."""
    
    def __init__(self, permission_manager: DatabasePermissionManager, 
                 user_interface: Optional[UserInterface] = None):
        super().__init__("message_user", permission_manager)
        self.user_interface = user_interface or UserInterface()
        
    def register_tools(self):
        """Register message tools."""
        self.register_tool("send_message", self.send_message)
        self.register_tool("send_structured_message", self.send_structured_message)
        self.register_tool("send_progress_update", self.send_progress_update)
        self.register_tool("send_error_notification", self.send_error_notification)
        self.register_tool("send_completion_report", self.send_completion_report)
    
    async def send_message(self, message: str, message_type: str = "info",
                          agent_type: str = None, task_id: int = None) -> bool:
        """Send simple message to user."""
        # Message user is a minimal permission tool - all agents can use it
        # No permission check needed beyond base tool access
        
        # Validate message type
        valid_types = ["info", "success", "warning", "error", "progress", "debug"]
        if message_type not in valid_types:
            logger.warning(f"Invalid message type '{message_type}', using 'info'")
            message_type = "info"
        
        # Send the message
        success = await self.user_interface.send_message(
            content=message,
            message_type=message_type,
            source_agent=agent_type,
            source_task=task_id
        )
        
        return success
    
    async def send_structured_message(self, title: str, content: str, 
                                    sections: Optional[List[Dict[str, str]]] = None,
                                    metadata: Optional[Dict[str, Any]] = None,
                                    agent_type: str = None, task_id: int = None) -> bool:
        """Send structured message with sections."""
        structured_content = {
            "title": title,
            "content": content,
            "sections": sections or [],
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "source": {
                "agent_type": agent_type,
                "task_id": task_id
            }
        }
        
        # Validate sections
        for section in structured_content["sections"]:
            if not isinstance(section, dict) or "title" not in section or "content" not in section:
                raise ValueError("Each section must have 'title' and 'content' fields")
        
        success = await self.user_interface.send_structured_message(structured_content)
        
        return success
    
    async def send_progress_update(self, current_step: int, total_steps: int,
                                  step_description: str, percentage: Optional[float] = None,
                                  agent_type: str = None, task_id: int = None) -> bool:
        """Send progress update with step information."""
        if percentage is None:
            percentage = (current_step / total_steps * 100) if total_steps > 0 else 0
        
        progress_data = {
            "type": "progress_update",
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": round(percentage, 2),
            "description": step_description,
            "timestamp": datetime.now().isoformat(),
            "source": {
                "agent_type": agent_type,
                "task_id": task_id
            }
        }
        
        # Send via WebSocket for real-time updates
        try:
            await send_websocket_message({
                "type": "progress_update",
                "data": progress_data
            })
        except Exception as e:
            logger.warning(f"Failed to send progress WebSocket message: {e}")
        
        # Also send as regular message
        message = f"Progress: {current_step}/{total_steps} ({percentage:.1f}%) - {step_description}"
        await self.send_message(message, "progress", agent_type, task_id)
        
        return True
    
    async def send_error_notification(self, error_message: str, error_type: str = "error",
                                    suggestions: Optional[List[str]] = None,
                                    recoverable: bool = True,
                                    agent_type: str = None, task_id: int = None) -> bool:
        """Send error notification with recovery suggestions."""
        error_data = {
            "type": "error_notification",
            "error_message": error_message,
            "error_type": error_type,
            "recoverable": recoverable,
            "suggestions": suggestions or [],
            "timestamp": datetime.now().isoformat(),
            "source": {
                "agent_type": agent_type,
                "task_id": task_id
            }
        }
        
        # Send structured error message
        sections = []
        if suggestions:
            sections.append({
                "title": "Suggested Actions",
                "content": "\n".join(f"• {s}" for s in suggestions)
            })
        
        await self.send_structured_message(
            title=f"{'Recoverable' if recoverable else 'Critical'} Error",
            content=error_message,
            sections=sections,
            metadata={"error": True, "recoverable": recoverable},
            agent_type=agent_type,
            task_id=task_id
        )
        
        return True
    
    async def send_completion_report(self, task_description: str, results: Dict[str, Any],
                                   duration_seconds: Optional[float] = None,
                                   quality_score: Optional[float] = None,
                                   next_steps: Optional[List[str]] = None,
                                   agent_type: str = None, task_id: int = None) -> bool:
        """Send task completion report."""
        sections = []
        
        # Results section
        if results:
            result_lines = []
            for key, value in results.items():
                result_lines.append(f"• {key}: {value}")
            sections.append({
                "title": "Results",
                "content": "\n".join(result_lines)
            })
        
        # Performance section
        if duration_seconds is not None or quality_score is not None:
            perf_lines = []
            if duration_seconds:
                perf_lines.append(f"• Duration: {duration_seconds:.2f} seconds")
            if quality_score:
                perf_lines.append(f"• Quality Score: {quality_score:.2f}/10")
            sections.append({
                "title": "Performance",
                "content": "\n".join(perf_lines)
            })
        
        # Next steps section
        if next_steps:
            sections.append({
                "title": "Next Steps",
                "content": "\n".join(f"• {step}" for step in next_steps)
            })
        
        # Send completion report
        await self.send_structured_message(
            title="Task Completion Report",
            content=f"Successfully completed: {task_description}",
            sections=sections,
            metadata={
                "completion": True,
                "duration": duration_seconds,
                "quality": quality_score
            },
            agent_type=agent_type,
            task_id=task_id
        )
        
        return True
    
    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history."""
        return self.user_interface.message_history[-limit:]
    
    async def wait_for_messages(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Wait for new messages (for testing/monitoring)."""
        try:
            return await asyncio.wait_for(
                self.user_interface.message_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None