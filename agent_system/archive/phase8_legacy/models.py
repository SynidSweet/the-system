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


class UserMessageType(str, Enum):
    QUESTION = "question"
    UPDATE = "update"
    VERIFICATION = "verification"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class ToolStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class EventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ModelConfig(BaseModel):
    provider: str = "google"
    model_name: str = "gemini-2.5-flash-preview-05-20"
    temperature: float = 0.1
    max_tokens: int = 4000
    api_key: Optional[str] = None
    
    class Config:
        protected_namespaces = ()


class AgentPermissions(BaseModel):
    web_search: bool = False
    file_system: bool = False
    shell_access: bool = False
    git_operations: bool = False
    database_write: bool = False
    spawn_agents: bool = True


class Agent(BaseModel):
    id: Optional[int] = None
    name: str
    version: str = "1.0.0"
    instruction: str
    context_documents: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    permissions: AgentPermissions = Field(default_factory=AgentPermissions)
    llm_config: ModelConfig = Field(default_factory=ModelConfig)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    status: AgentStatus = AgentStatus.ACTIVE

    class Config:
        from_attributes = True


class ContextDocument(BaseModel):
    id: Optional[int] = None
    name: str
    title: str
    content: str
    format: str = "markdown"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
    category: str
    access_level: str = "internal"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class Task(BaseModel):
    id: Optional[int] = None
    parent_task_id: Optional[int] = None
    tree_id: int
    agent_id: int
    instruction: str
    status: TaskStatus = TaskStatus.CREATED
    result: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    priority: int = 0
    max_execution_time: int = 300
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Message(BaseModel):
    id: Optional[int] = None
    task_id: int
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_message_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    token_count: Optional[int] = None
    execution_time_ms: Optional[int] = None

    class Config:
        from_attributes = True


class UserMessage(BaseModel):
    """Messages sent from agents to users for communication"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    agent_name: str = "system"
    message: str
    message_type: UserMessageType = UserMessageType.INFO
    priority: MessagePriority = MessagePriority.NORMAL
    requires_response: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    read_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    user_response: Optional[str] = None
    
    class Config:
        from_attributes = True


class ToolImplementation(BaseModel):
    type: str  # "python_class", "shell_command", "api_call", "mcp_server"
    module_path: Optional[str] = None
    class_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class Tool(BaseModel):
    id: Optional[int] = None
    name: str
    version: str = "1.0.0"
    description: str
    category: str
    implementation: ToolImplementation
    parameters: Dict[str, Any] = Field(default_factory=dict)  # JSON schema
    permissions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    status: ToolStatus = ToolStatus.ACTIVE

    class Config:
        from_attributes = True


class SystemEvent(BaseModel):
    id: Optional[int] = None
    event_type: str
    source_task_id: Optional[int] = None
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    severity: EventSeverity = EventSeverity.INFO

    class Config:
        from_attributes = True


class TaskTree(BaseModel):
    tree_id: int
    total_tasks: int
    completed_tasks: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MCPToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None


class MCPToolResult(BaseModel):
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None


class AgentExecutionContext(BaseModel):
    task: Task
    agent: Agent
    context_documents: List[ContextDocument] = Field(default_factory=list)
    available_tools: List[Tool] = Field(default_factory=list)
    message_history: List[Message] = Field(default_factory=list)
    recursion_depth: int = 0


class AgentExecutionResult(BaseModel):
    status: TaskStatus
    result: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    spawned_tasks: List[int] = Field(default_factory=list)
    tool_calls_made: int = 0
    execution_time_seconds: float = 0


class TaskSubmission(BaseModel):
    instruction: str
    agent_type: Optional[str] = None
    priority: int = 0
    max_execution_time: int = 300


class TaskResponse(BaseModel):
    task_id: int
    tree_id: int
    status: TaskStatus
    created_at: datetime


class MessageUpdate(BaseModel):
    task_id: int
    message: Message
    task_status: TaskStatus


# Helper functions for JSON serialization
def serialize_for_db(obj: Any) -> str:
    """Serialize object to JSON string for database storage"""
    if isinstance(obj, BaseModel):
        return obj.model_dump_json()
    elif isinstance(obj, (list, dict)):
        return json.dumps(obj)
    else:
        return json.dumps(obj)


def deserialize_from_db(json_str: str, target_type: type = None) -> Any:
    """Deserialize JSON string from database"""
    if not json_str:
        return None
    
    data = json.loads(json_str)
    
    if target_type and issubclass(target_type, BaseModel):
        return target_type(**data)
    
    return data