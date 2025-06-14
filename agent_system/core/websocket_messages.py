"""
WebSocket message types and structures for real-time UI updates.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


class MessageType(Enum):
    """Types of WebSocket messages"""
    # Agent lifecycle
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_TOOL_RESULT = "agent_tool_result"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_SPAWNED = "task_spawned"
    
    # System events
    SYSTEM_MESSAGE = "system_message"
    USER_MESSAGE = "user_message"
    STEP_MODE_PAUSE = "step_mode_pause"
    THREAD_UPDATE = "thread_update"


@dataclass
class WebSocketMessage:
    """Structure for WebSocket messages"""
    type: MessageType
    task_id: int
    tree_id: int
    agent_name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def to_json(self) -> str:
        """Convert to JSON for WebSocket transmission"""
        data = {
            "type": self.type.value,
            "task_id": self.task_id,
            "tree_id": self.tree_id,
            "agent_name": self.agent_name,
            "content": self.content or {},
            "timestamp": (self.timestamp or datetime.utcnow()).isoformat()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, data: str) -> 'WebSocketMessage':
        """Create from JSON string"""
        obj = json.loads(data)
        return cls(
            type=MessageType(obj["type"]),
            task_id=obj["task_id"],
            tree_id=obj["tree_id"],
            agent_name=obj.get("agent_name"),
            content=obj.get("content", {}),
            timestamp=datetime.fromisoformat(obj["timestamp"]) if obj.get("timestamp") else None
        )


class MessageBuilder:
    """Helper class to build common message types"""
    
    @staticmethod
    def agent_started(task_id: int, tree_id: int, agent_name: str, instruction: str) -> WebSocketMessage:
        return WebSocketMessage(
            type=MessageType.AGENT_STARTED,
            task_id=task_id,
            tree_id=tree_id,
            agent_name=agent_name,
            content={
                "instruction": instruction,
                "status": "initializing"
            }
        )
    
    @staticmethod
    def agent_thinking(task_id: int, tree_id: int, agent_name: str, thought: str) -> WebSocketMessage:
        return WebSocketMessage(
            type=MessageType.AGENT_THINKING,
            task_id=task_id,
            tree_id=tree_id,
            agent_name=agent_name,
            content={"thought": thought}
        )
    
    @staticmethod
    def tool_call(task_id: int, tree_id: int, agent_name: str, tool_name: str, 
                  tool_input: Dict[str, Any]) -> WebSocketMessage:
        return WebSocketMessage(
            type=MessageType.AGENT_TOOL_CALL,
            task_id=task_id,
            tree_id=tree_id,
            agent_name=agent_name,
            content={
                "tool_name": tool_name,
                "tool_input": tool_input
            }
        )
    
    @staticmethod
    def tool_result(task_id: int, tree_id: int, agent_name: str, tool_name: str,
                    tool_output: Any, success: bool = True) -> WebSocketMessage:
        return WebSocketMessage(
            type=MessageType.AGENT_TOOL_RESULT,
            task_id=task_id,
            tree_id=tree_id,
            agent_name=agent_name,
            content={
                "tool_name": tool_name,
                "tool_output": tool_output,
                "success": success
            }
        )
    
    @staticmethod
    def step_pause(task_id: int, tree_id: int, agent_name: str, 
                   pause_reason: str = "Step mode active") -> WebSocketMessage:
        return WebSocketMessage(
            type=MessageType.STEP_MODE_PAUSE,
            task_id=task_id,
            tree_id=tree_id,
            agent_name=agent_name,
            content={
                "reason": pause_reason,
                "waiting_for": "user_continue"
            }
        )
    
    @staticmethod
    def task_spawned(parent_task_id: int, tree_id: int, child_task_id: int,
                     child_instruction: str, child_agent: str) -> WebSocketMessage:
        return WebSocketMessage(
            type=MessageType.TASK_SPAWNED,
            task_id=parent_task_id,
            tree_id=tree_id,
            content={
                "child_task_id": child_task_id,
                "child_instruction": child_instruction,
                "child_agent": child_agent
            }
        )