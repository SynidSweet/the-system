# Agent System - Architectural & Programmatic Schemas

## 1. MCP Tool Definition Schema

### Custom MCP Tool Interface
```python
# tools/mcp_tool_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class MCPToolConfig(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    permissions: List[str] = []
    timeout_seconds: int = 300
    retry_count: int = 0

class MCPToolResult(BaseModel):
    success: bool
    result: Any = None
    error_message: str = None
    metadata: Dict[str, Any] = {}

class BaseMCPTool(ABC):
    def __init__(self, config: MCPToolConfig):
        self.config = config
        
    @abstractmethod
    async def execute(self, **kwargs) -> MCPToolResult:
        """Execute the tool with given parameters"""
        pass
        
    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters"""
        pass
        
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this tool"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "parameters": self.config.parameters
        }
```

### MCP Tool Registry Schema
```json
{
  "tool_registry_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*$"},
      "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
      "description": {"type": "string", "maxLength": 500},
      "category": {"type": "string", "enum": ["core", "system", "external", "generated"]},
      "implementation": {
        "type": "object",
        "properties": {
          "type": {"type": "string", "enum": ["python_class", "shell_command", "api_call", "mcp_server"]},
          "module_path": {"type": "string"},
          "class_name": {"type": "string"},
          "config": {"type": "object"}
        }
      },
      "parameters": {
        "type": "object",
        "properties": {
          "type": {"const": "object"},
          "properties": {"type": "object"},
          "required": {"type": "array", "items": {"type": "string"}}
        }
      },
      "permissions": {
        "type": "array",
        "items": {"type": "string", "enum": ["file_read", "file_write", "shell_exec", "network", "database", "git"]}
      },
      "dependencies": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["name", "description", "implementation", "parameters"]
  }
}
```

## 2. Agent Configuration Schema

### Agent Definition Schema
```json
{
  "agent_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*$"},
      "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
      "model": {
        "type": "object",
        "properties": {
          "provider": {"type": "string", "enum": ["anthropic", "openai", "local"]},
          "model_name": {"type": "string"},
          "temperature": {"type": "number", "minimum": 0, "maximum": 2},
          "max_tokens": {"type": "integer", "minimum": 1, "maximum": 200000}
        },
        "required": ["provider", "model_name"]
      },
      "instruction": {"type": "string", "maxLength": 10000},
      "context_documents": {
        "type": "array",
        "items": {"type": "string"}
      },
      "available_tools": {
        "type": "array",
        "items": {"type": "string"}
      },
      "permissions": {
        "type": "object",
        "properties": {
          "web_search": {"type": "boolean"},
          "file_system": {"type": "boolean"},
          "shell_access": {"type": "boolean"},
          "git_operations": {"type": "boolean"},
          "database_write": {"type": "boolean"},
          "spawn_agents": {"type": "boolean"}
        }
      },
      "constraints": {
        "type": "object",
        "properties": {
          "max_execution_time": {"type": "integer"},
          "max_tool_calls": {"type": "integer"},
          "max_recursion_depth": {"type": "integer"},
          "memory_limit_mb": {"type": "integer"}
        }
      }
    },
    "required": ["name", "model", "instruction"]
  }
}
```

### Agent Runtime Interface
```python
# core/agent_interface.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum

class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"

class AgentMessage(BaseModel):
    id: str
    task_id: int
    message_type: str  # 'system', 'user', 'assistant', 'tool_call', 'tool_result'
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: float

class AgentContext(BaseModel):
    task_id: int
    agent_config: Dict[str, Any]
    context_documents: List[Dict[str, str]]
    available_tools: List[Dict[str, Any]]
    conversation_history: List[AgentMessage]
    parent_task_id: Optional[int] = None
    tree_id: int

class AgentExecutionResult(BaseModel):
    status: AgentStatus
    result: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    messages: List[AgentMessage] = []
    spawned_tasks: List[int] = []
    tool_calls_made: int = 0
    execution_time_seconds: float = 0
```

## 3. Task Execution Schema

### Task Flow State Machine
```python
# core/task_states.py
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

class TaskStatus(Enum):
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

class TaskTransition(BaseModel):
    from_status: TaskStatus
    to_status: TaskStatus
    condition: str
    action: Optional[str] = None

# Valid state transitions
TASK_TRANSITIONS = [
    TaskTransition(TaskStatus.CREATED, TaskStatus.QUEUED, "task_created"),
    TaskTransition(TaskStatus.QUEUED, TaskStatus.AGENT_SELECTED, "agent_available"),
    TaskTransition(TaskStatus.AGENT_SELECTED, TaskStatus.RUNNING, "agent_started"),
    TaskTransition(TaskStatus.RUNNING, TaskStatus.WAITING_SUBTASKS, "subtasks_spawned"),
    TaskTransition(TaskStatus.RUNNING, TaskStatus.EVALUATING, "task_completed"),
    TaskTransition(TaskStatus.WAITING_SUBTASKS, TaskStatus.EVALUATING, "all_subtasks_complete"),
    TaskTransition(TaskStatus.EVALUATING, TaskStatus.DOCUMENTING, "evaluation_complete"),
    TaskTransition(TaskStatus.DOCUMENTING, TaskStatus.SUMMARIZING, "documentation_complete"),
    TaskTransition(TaskStatus.SUMMARIZING, TaskStatus.COMPLETE, "summary_complete"),
    TaskTransition(TaskStatus.RUNNING, TaskStatus.FAILED, "execution_failed"),
    TaskTransition(TaskStatus.RUNNING, TaskStatus.REVIEW_FLAGGED, "review_requested")
]
```

### Task Message Protocol
```json
{
  "task_message_schema": {
    "type": "object",
    "properties": {
      "message_id": {"type": "string", "format": "uuid"},
      "task_id": {"type": "integer"},
      "message_type": {
        "type": "string",
        "enum": ["user_input", "agent_response", "tool_call", "tool_response", "system_event", "error"]
      },
      "content": {"type": "string"},
      "metadata": {
        "type": "object",
        "properties": {
          "tool_name": {"type": "string"},
          "tool_parameters": {"type": "object"},
          "execution_time": {"type": "number"},
          "token_count": {"type": "integer"},
          "model_used": {"type": "string"}
        }
      },
      "timestamp": {"type": "string", "format": "date-time"},
      "parent_message_id": {"type": "string", "format": "uuid"}
    },
    "required": ["message_id", "task_id", "message_type", "content", "timestamp"]
  }
}
```

## 4. File Structure Schema

### Project Directory Structure
```
agent_system/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .gitignore
├── restart.sh
├── config/
│   ├── __init__.py
│   ├── settings.py          # Environment configuration
│   ├── database.py          # Database connection setup
│   └── logging.py           # Logging configuration
├── core/
│   ├── __init__.py
│   ├── agent.py             # Universal agent runtime
│   ├── task_manager.py      # Task queue and lifecycle
│   ├── message_handler.py   # Message protocol implementation
│   ├── tool_registry.py     # MCP tool management
│   └── supervisor.py        # Agent supervision and monitoring
├── agents/
│   ├── __init__.py
│   ├── base.py              # Base agent configuration loader
│   └── configs/             # Agent configuration files
│       ├── agent_selector.json
│       ├── task_breakdown.json
│       └── ...
├── tools/
│   ├── __init__.py
│   ├── core_mcp.py          # Core MCP toolkit
│   ├── base_tool.py         # Base tool interface
│   ├── system_tools/        # Built-in system tools
│   │   ├── terminal.py
│   │   ├── git_operations.py
│   │   └── database_query.py
│   └── custom_tools/        # Generated/added tools
├── context/
│   ├── system_overview.md
│   ├── architecture.md
│   ├── improvement_guide.md
│   └── templates/           # Document templates
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   ├── tasks.py
│   │   ├── agents.py
│   │   └── websockets.py
│   └── models/              # Pydantic models
├── web/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   └── public/
├── data/
│   ├── agent_system.db      # SQLite database
│   ├── logs/                # System logs
│   └── backups/             # Automated backups
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_tasks.py
│   └── integration/
└── scripts/
    ├── init_database.py     # Database initialization
    ├── seed_agents.py       # Seed initial agents
    └── backup.py            # Backup utilities
```

## 5. Context Document Schema

### Document Structure Standard
```json
{
  "context_document_schema": {
    "type": "object",
    "properties": {
      "metadata": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "version": {"type": "string"},
          "last_updated": {"type": "string", "format": "date-time"},
          "updated_by": {"type": "string"},
          "tags": {"type": "array", "items": {"type": "string"}},
          "category": {"type": "string", "enum": ["system", "process", "reference", "guide"]},
          "access_level": {"type": "string", "enum": ["public", "internal", "restricted"]}
        },
        "required": ["title", "version", "last_updated"]
      },
      "content": {
        "type": "object",
        "properties": {
          "format": {"type": "string", "enum": ["markdown", "json", "yaml", "text"]},
          "body": {"type": "string"},
          "sections": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "subsections": {"type": "array"}
              }
            }
          }
        },
        "required": ["format", "body"]
      },
      "references": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": {"type": "string", "enum": ["document", "tool", "agent", "external"]},
            "id": {"type": "string"},
            "description": {"type": "string"}
          }
        }
      }
    },
    "required": ["metadata", "content"]
  }
}
```

### Context Injection Interface
```python
# core/context_manager.py
from typing import List, Dict, Any
from pydantic import BaseModel

class ContextSection(BaseModel):
    id: str
    title: str
    content: str
    relevance_score: float = 1.0

class ContextDocument(BaseModel):
    id: str
    name: str
    sections: List[ContextSection]
    metadata: Dict[str, Any]

class ContextManager:
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def get_context_for_agent(self, agent_id: int, task_context: str = "") -> List[ContextDocument]:
        """Get relevant context documents for an agent"""
        pass
        
    async def search_context(self, query: str, max_results: int = 5) -> List[ContextSection]:
        """Search for relevant context sections"""
        pass
        
    async def update_context(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update context document"""
        pass
        
    def format_context_for_prompt(self, documents: List[ContextDocument]) -> str:
        """Format context documents for inclusion in agent prompt"""
        pass
```

## 6. Inter-Agent Communication Schema

### Agent Message Queue
```python
# core/message_queue.py
from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class AgentMessage(BaseModel):
    id: str
    from_agent: int  # task_id of sending agent
    to_agent: Optional[int] = None  # task_id of receiving agent, None for broadcast
    message_type: str
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    expires_at: Optional[float] = None
    created_at: float

class MessageQueue:
    async def send_message(self, message: AgentMessage) -> bool:
        """Send message to another agent or broadcast"""
        pass
        
    async def get_messages(self, agent_id: int) -> List[AgentMessage]:
        """Get pending messages for an agent"""
        pass
        
    async def subscribe_to_events(self, agent_id: int, event_types: List[str]) -> None:
        """Subscribe to system events"""
        pass
```

## 7. Self-Modification Schema

### Code Modification Interface
```python
# core/self_modification.py
from typing import List, Dict, Any
from pydantic import BaseModel

class ModificationRequest(BaseModel):
    type: str  # "file_edit", "file_create", "file_delete", "config_update"
    target_path: str
    changes: Dict[str, Any]
    reason: str
    risk_level: str  # "low", "medium", "high", "critical"
    rollback_plan: str

class ModificationResult(BaseModel):
    success: bool
    changes_applied: List[str]
    backup_created: str
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None

class SelfModificationManager:
    def __init__(self, git_manager, backup_manager):
        self.git = git_manager
        self.backup = backup_manager
        
    async def request_modification(self, request: ModificationRequest) -> ModificationResult:
        """Request system modification with safety checks"""
        # 1. Validate modification request
        # 2. Create backup
        # 3. Create git branch
        # 4. Apply changes
        # 5. Run tests
        # 6. Commit if successful
        pass
        
    async def rollback_modification(self, commit_hash: str) -> bool:
        """Rollback a previous modification"""
        pass
        
    async def validate_changes(self, changes: List[str]) -> Dict[str, Any]:
        """Validate proposed changes before applying"""
        pass
```

## 8. Database Extended Schema

### Complete Database Schema with Indexes and Constraints
```sql
-- Enhanced database schema with proper indexes and constraints

CREATE TABLE agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    instruction TEXT NOT NULL,
    context_documents TEXT, -- JSON array
    available_tools TEXT,   -- JSON array  
    permissions TEXT,       -- JSON object
    constraints TEXT,       -- JSON object
    model_config TEXT,      -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,     -- task_id that created this agent
    status TEXT DEFAULT 'active' -- active, deprecated, testing
);

CREATE TABLE context_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    metadata TEXT,          -- JSON object
    version TEXT NOT NULL DEFAULT '1.0.0',
    category TEXT NOT NULL,
    access_level TEXT DEFAULT 'internal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER      -- task_id that updated this document
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_task_id INTEGER,
    tree_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    status TEXT DEFAULT 'created',
    result TEXT,
    summary TEXT,
    error_message TEXT,
    priority INTEGER DEFAULT 0,
    max_execution_time INTEGER DEFAULT 300,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,          -- JSON object
    parent_message_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_count INTEGER,
    execution_time_ms INTEGER,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id)
);

CREATE TABLE tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    description TEXT,
    category TEXT NOT NULL,
    implementation TEXT NOT NULL, -- JSON object
    parameters TEXT NOT NULL,     -- JSON schema
    permissions TEXT,             -- JSON array
    dependencies TEXT,            -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,           -- task_id that created this tool
    status TEXT DEFAULT 'active'  -- active, deprecated, testing
);

CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    source_task_id INTEGER,
    event_data TEXT,        -- JSON object
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity TEXT DEFAULT 'info' -- debug, info, warning, error, critical
);

-- Indexes for performance
CREATE INDEX idx_tasks_tree_id ON tasks(tree_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX idx_messages_task_id ON messages(task_id);
CREATE INDEX idx_messages_type ON messages(message_type);
CREATE INDEX idx_events_type ON system_events(event_type);
CREATE INDEX idx_events_timestamp ON system_events(timestamp);

-- Views for common queries
CREATE VIEW active_tasks AS
SELECT * FROM tasks WHERE status IN ('created', 'queued', 'running', 'waiting_subtasks');

CREATE VIEW task_trees AS
SELECT 
    tree_id,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'complete' THEN 1 END) as completed_tasks,
    MIN(created_at) as started_at,
    MAX(completed_at) as finished_at
FROM tasks GROUP BY tree_id;
```

## 9. Error Handling and Recovery Schema

### Error Classification and Recovery
```python
# core/error_handling.py
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ErrorSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"

class ErrorCategory(Enum):
    AGENT_EXECUTION = "agent_execution"
    TOOL_FAILURE = "tool_failure"
    SYSTEM_ERROR = "system_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"

class SystemError(BaseModel):
    id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    task_id: Optional[int] = None
    agent_id: Optional[int] = None
    timestamp: float
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None

class ErrorRecoveryStrategy(BaseModel):
    error_pattern: str
    recovery_actions: List[str]
    max_retry_count: int = 3
    escalation_path: Optional[str] = None

ERROR_RECOVERY_STRATEGIES = [
    ErrorRecoveryStrategy(
        error_pattern="timeout",
        recovery_actions=["increase_timeout", "retry_with_supervisor"],
        max_retry_count=2
    ),
    ErrorRecoveryStrategy(
        error_pattern="tool_not_found",
        recovery_actions=["discover_alternative_tool", "request_tool_creation"],
        max_retry_count=1
    ),
    ErrorRecoveryStrategy(
        error_pattern="permission_denied",
        recovery_actions=["escalate_permissions", "use_alternative_approach"],
        max_retry_count=1
    )
]
```

## 10. Configuration Management Schema

### System Configuration Interface
```yaml
# config/system_config.yaml
system:
  environment: "development" # development, staging, production
  debug_mode: true
  max_concurrent_agents: 3
  default_timeout_seconds: 300
  auto_restart_on_modification: true

database:
  type: "sqlite"
  path: "data/agent_system.db"
  backup_interval_hours: 1
  max_backup_count: 24

agents:
  default_model:
    provider: "anthropic"
    model_name: "claude-3-5-sonnet-20241022"
    temperature: 0.1
    max_tokens: 4000
  
  execution_limits:
    max_tool_calls_per_task: 50
    max_recursion_depth: 10
    memory_limit_mb: 1024

tools:
  discovery:
    enabled: true
    auto_install: false
    trusted_sources: ["github.com/your-org", "internal-registry"]
  
  security:
    sandbox_mode: false
    allowed_permissions: ["file_read", "file_write", "shell_exec", "network", "database", "git"]

monitoring:
  metrics_enabled: true
  log_level: "INFO"
  performance_tracking: true
  error_alerting: true

self_modification:
  enabled: true
  require_approval: false
  auto_backup: true
  git_auto_commit: true
  testing_required: true
```

This comprehensive schema framework provides the technical foundation needed to implement the agent system with proper interfaces, data structures, and safety mechanisms. Each schema defines clear contracts between system components while maintaining the flexibility for agents to extend and modify the system as needed.
