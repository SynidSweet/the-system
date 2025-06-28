"""
User communication MCP tool for agent-to-user messaging.

This tool allows agents to send messages directly to users for:
- Questions requiring user input
- Status updates and progress reports  
- Verification requests
- Error notifications requiring user action
- General communication and feedback
"""

from typing import Dict, Any, Optional
from ..base_tool import SystemMCPTool
from pydantic import BaseModel, Field
from typing import Dict, Any

# Temporary compatibility model
class MCPToolResult(BaseModel):
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None


class SendMessageToUserTool(SystemMCPTool):
    """Send messages directly to the user interface"""
    
    def __init__(self):
        super().__init__(
            name="send_message_to_user",
            description="Send a message directly to the user for questions, updates, verification, or general communication",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message content to send to the user",
                        "minLength": 1,
                        "maxLength": 2000
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["question", "update", "verification", "error", "info", "warning", "success"],
                        "description": "Type of message for appropriate UI styling",
                        "default": "info"
                    },
                    "requires_response": {
                        "type": "boolean",
                        "description": "Whether this message requires a user response",
                        "default": False
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Message priority level",
                        "default": "normal"
                    },
                    "suggested_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Suggested actions or responses for the user",
                        "maxItems": 5
                    }
                },
                "required": ["message"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        message = kwargs.get("message", "").strip()
        message_type = kwargs.get("message_type", "info")
        requires_response = kwargs.get("requires_response", False)
        priority = kwargs.get("priority", "normal")
        suggested_actions = kwargs.get("suggested_actions", [])
        
        if not message:
            return MCPToolResult(
                success=False,
                error_message="Message content cannot be empty"
            )
        
        try:
            # Get current task context
            task_context = self.get_task_context()
            
            # Create user message record
            user_message = {
                "message": message,
                "message_type": message_type,
                "requires_response": requires_response,
                "priority": priority,
                "suggested_actions": suggested_actions,
                "task_id": task_context.get("task_id") if task_context else None,
                "agent_name": task_context.get("agent_name") if task_context else "system",
                "timestamp": self._get_current_timestamp()
            }
            
            # Store in database for persistence
            from agent_system.config.database import DatabaseManager
            database = DatabaseManager()
            message_id = await database.user_messages.create(user_message)
            
            # Send real-time notification via WebSocket
            await self._broadcast_user_message({
                "id": message_id,
                "type": "user_message",
                "data": user_message
            })
            
            # Return success with message ID for potential follow-up
            return MCPToolResult(
                success=True,
                result={
                    "message_sent": True,
                    "message_id": message_id,
                    "message_type": message_type,
                    "requires_response": requires_response,
                    "priority": priority
                },
                metadata={
                    "tool_name": "send_message_to_user",
                    "timestamp": user_message["timestamp"],
                    "task_id": user_message["task_id"]
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to send user message: {str(e)}"
            )
    
    async def _broadcast_user_message(self, message_data: Dict[str, Any]):
        """Broadcast user message via WebSocket"""
        try:
            # Import here to avoid circular imports
            from api.main import manager
            await manager.broadcast_user_message(message_data)
        except Exception as e:
            print(f"Warning: Failed to broadcast user message: {e}")
    
    def get_task_context(self) -> Dict[str, Any]:
        """Get current task context - placeholder implementation"""
        # TODO: Implement proper task context retrieval
        return {
            "task_id": None,
            "agent_name": "system"
        }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


def register_user_communication_tools(registry):
    """Register user communication tools with the registry"""
    tools = [
        SendMessageToUserTool()
    ]
    
    for tool in tools:
        registry.register_tool(tool, "core")
    
    return tools