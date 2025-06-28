"""
Core models for the agent system.
This provides compatibility layer for the universal agent runtime.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    AGENT_SELECTED = "agent_selected"
    RUNNING = "running"
    WAITING_SUBTASKS = "waiting_subtasks"
    EVALUATING = "evaluating"
    DOCUMENTING = "documenting"
    SUMMARIZING = "summarizing"
    COMPLETE = "complete"
    FAILED = "failed"
    REVIEW_FLAGGED = "review_flagged"


class MessageType(str, Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


class AgentPermissions(BaseModel):
    """Agent permission configuration"""
    web_search: bool = False
    database_write: bool = False
    file_system: bool = False
    shell_access: bool = False
    spawn_agents: bool = False
    git_operations: bool = False
    self_modify: bool = False


class AIModelConfig(BaseModel):
    """AI model configuration"""
    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None


class Agent(BaseModel):
    """Agent model"""
    id: Optional[int] = None
    name: str
    instruction: str
    context_documents: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    permissions: Union[List[str], AgentPermissions] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ai_model_config: Optional[AIModelConfig] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Task(BaseModel):
    """Task model"""
    id: Optional[int] = None
    parent_task_id: Optional[int] = None
    tree_id: Optional[int] = None
    agent_id: Optional[int] = None
    instruction: str
    status: TaskStatus = TaskStatus.CREATED
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Message(BaseModel):
    """Message model"""
    id: Optional[int] = None
    task_id: int
    message_type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class ContextDocument(BaseModel):
    """Context document model"""
    id: Optional[int] = None
    name: str
    title: str
    category: str = "general"
    content: str
    format: str = "markdown"
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Tool(BaseModel):
    """Tool model"""
    id: Optional[int] = None
    name: str
    description: str
    category: str = "system"
    implementation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AgentExecutionContext(BaseModel):
    """Context for agent execution"""
    task: Task
    agent: Agent
    context_documents: List[ContextDocument]
    available_tools: List[Tool]
    parent_context: Optional[Dict[str, Any]] = None
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPToolCall(BaseModel):
    """MCP tool call request"""
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None


class MCPToolResult(BaseModel):
    """MCP tool call result"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None


class AgentExecutionResult(BaseModel):
    """Result of agent execution"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    messages_logged: int = 0
    tool_calls_made: int = 0
    execution_time: float = 0.0
    task_complete: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)