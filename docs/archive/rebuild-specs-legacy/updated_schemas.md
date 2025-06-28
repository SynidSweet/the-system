# Agent System - Entity-Based Architectural Schemas

## 1. Entity Framework Schema

### Core Entity Interface
```python
# core/entities/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum

class EntityType(Enum):
    AGENT = "agent"
    TASK = "task"
    PROCESS = "process"
    TOOL = "tool"
    DOCUMENT = "document"
    EVENT = "event"

class EntityStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"

class BaseEntity(BaseModel):
    """Base class for all system entities"""
    id: int
    name: str
    version: str = "1.0.0"
    created_at: float
    updated_at: float
    created_by_task_id: Optional[int] = None
    status: EntityStatus = EntityStatus.ACTIVE
    metadata: Dict[str, Any] = {}

    def get_entity_type(self) -> EntityType:
        """Return the entity type"""
        return self.__class__.ENTITY_TYPE

    @abstractmethod
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        """Return related entities by type and ID"""
        pass

    @abstractmethod
    def validate_entity(self) -> bool:
        """Validate entity configuration"""
        pass

class EntityManager:
    """Manages entity lifecycle and relationships"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def create_entity(self, entity_type: EntityType, entity_data: Dict[str, Any]) -> BaseEntity:
        """Create new entity and log creation event"""
        pass
        
    async def update_entity(self, entity_id: int, entity_type: EntityType, updates: Dict[str, Any]) -> BaseEntity:
        """Update entity and log modification event"""
        pass
        
    async def get_entity(self, entity_id: int, entity_type: EntityType) -> BaseEntity:
        """Retrieve entity by ID and type"""
        pass
        
    async def get_related_entities(self, entity_id: int, entity_type: EntityType) -> Dict[EntityType, List[BaseEntity]]:
        """Get all entities related to this entity"""
        pass
        
    async def track_entity_usage(self, entity_id: int, entity_type: EntityType, usage_context: Dict[str, Any]):
        """Track entity usage for rolling review counters"""
        pass
```

### Entity Relationship Schema
```json
{
  "entity_relationship_schema": {
    "type": "object",
    "properties": {
      "source_type": {"type": "string", "enum": ["agent", "task", "process", "tool", "document", "event"]},
      "source_id": {"type": "integer"},
      "target_type": {"type": "string", "enum": ["agent", "task", "process", "tool", "document", "event"]},
      "target_id": {"type": "integer"},
      "relationship_type": {
        "type": "string",
        "enum": ["uses", "depends_on", "creates", "optimizes", "triggers", "references", "contains", "inherits"]
      },
      "strength": {"type": "number", "minimum": 0, "maximum": 1},
      "context": {"type": "object"},
      "created_by_event_id": {"type": "integer"}
    },
    "required": ["source_type", "source_id", "target_type", "target_id", "relationship_type"]
  }
}
```

## 2. Agent Entity Schema

### Agent Configuration Schema
```python
# core/entities/agent.py
from core.entities.base import BaseEntity, EntityType
from typing import List, Dict, Any, Optional

class ModelConfig(BaseModel):
    provider: str  # anthropic, openai, google
    model_name: str
    model_type: str  # default, budget, complex_reasoning, coding
    temperature: float = 0.1
    max_tokens: int = 4000
    api_key: Optional[str] = None

class AgentPermissions(BaseModel):
    web_search: bool = False
    file_system: bool = False
    shell_access: bool = False
    git_operations: bool = False
    database_write: bool = False
    spawn_agents: bool = True
    create_processes: bool = False
    modify_system: bool = False

class Agent(BaseEntity):
    ENTITY_TYPE = EntityType.AGENT
    
    instruction: str
    context_documents: List[str] = []
    available_tools: List[str] = []
    permissions: AgentPermissions
    model_config: ModelConfig
    specialization: str
    success_rate: float = 0.0
    usage_count: int = 0
    
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        return {
            EntityType.DOCUMENT: self.context_documents,
            EntityType.TOOL: self.available_tools
        }
    
    def validate_entity(self) -> bool:
        return bool(self.instruction and self.specialization)

class AgentFactory:
    """Factory for creating and configuring agents"""
    
    @classmethod
    def create_agent(cls, name: str, instruction: str, specialization: str, **kwargs) -> Agent:
        """Create agent with default configuration"""
        pass
        
    @classmethod
    def clone_agent(cls, source_agent: Agent, modifications: Dict[str, Any]) -> Agent:
        """Clone existing agent with modifications"""
        pass
```

## 3. Task Entity Schema

### Task Configuration Schema
```python
# core/entities/task.py
from core.entities.base import BaseEntity, EntityType
from typing import List, Dict, Any, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class Task(BaseEntity):
    ENTITY_TYPE = EntityType.TASK
    
    parent_task_id: Optional[int] = None
    tree_id: int
    instruction: str
    dependencies: List[int] = []
    assigned_agent_id: int
    additional_context: List[str] = []
    additional_tools: List[str] = []
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    result: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[float] = None
    execution_time_seconds: float = 0
    
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        entities = {
            EntityType.AGENT: [self.assigned_agent_id],
            EntityType.DOCUMENT: self.additional_context,
            EntityType.TOOL: self.additional_tools,
            EntityType.TASK: self.dependencies
        }
        if self.parent_task_id:
            entities[EntityType.TASK].append(self.parent_task_id)
        return entities
    
    def validate_entity(self) -> bool:
        return bool(self.instruction and self.assigned_agent_id and self.tree_id)

class TaskDependencyGraph:
    """Manages task dependencies and execution order"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def check_dependencies_met(self, task_id: int) -> bool:
        """Check if all task dependencies are completed"""
        pass
        
    async def get_next_ready_tasks(self, tree_id: int) -> List[Task]:
        """Get tasks ready for execution (no pending dependencies)"""
        pass
        
    async def detect_circular_dependencies(self, tree_id: int) -> List[List[int]]:
        """Detect circular dependency chains"""
        pass
```

## 4. Process Entity Schema

### Process Template Schema
```python
# core/entities/process.py
from core.entities.base import BaseEntity, EntityType
from typing import List, Dict, Any, Optional
from enum import Enum

class ProcessStepType(Enum):
    AGENT_PROMPT = "agent_prompt"
    TOOL_CALL = "tool_call"
    SUBTASK_SPAWN = "subtask_spawn"
    CONDITION_CHECK = "condition_check"
    LOOP = "loop"
    PARALLEL_EXECUTION = "parallel_execution"
    WAIT_FOR_COMPLETION = "wait_for_completion"

class ProcessStep(BaseModel):
    step_id: str
    step_type: ProcessStepType
    parameters: Dict[str, Any] = {}
    conditions: List[str] = []  # Condition expressions
    next_steps: List[str] = []  # Next step IDs
    error_handler: Optional[str] = None  # Error handler step ID

class Process(BaseEntity):
    ENTITY_TYPE = EntityType.PROCESS
    
    description: str
    category: str  # breakdown, context_addition, tool_creation, evaluation, etc.
    template: List[ProcessStep]
    parameters_schema: Dict[str, Any] = {}
    success_criteria: List[str] = []
    usage_count: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0
    
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        # Extract entity references from process steps
        entities = {entity_type: [] for entity_type in EntityType}
        for step in self.template:
            # Parse step parameters for entity references
            pass
        return entities
    
    def validate_entity(self) -> bool:
        return bool(self.description and self.template and self.category)

class ProcessEngine:
    """Executes process templates with parameter substitution"""
    
    def __init__(self, entity_manager, task_manager):
        self.entity_manager = entity_manager
        self.task_manager = task_manager
        
    async def execute_process(self, process_id: int, parameters: Dict[str, Any], context_task_id: int) -> Dict[str, Any]:
        """Execute process template with parameters"""
        pass
        
    async def validate_parameters(self, process_id: int, parameters: Dict[str, Any]) -> bool:
        """Validate parameters against process schema"""
        pass
        
    def substitute_parameters(self, template: List[ProcessStep], parameters: Dict[str, Any]) -> List[ProcessStep]:
        """Substitute parameters in process template"""
        pass
```

### Process Template Examples
```json
{
  "task_breakdown_process": {
    "name": "standard_task_breakdown",
    "description": "Standard process for breaking down complex tasks",
    "category": "breakdown",
    "template": [
      {
        "step_id": "analyze_task",
        "step_type": "agent_prompt",
        "parameters": {
          "agent_type": "planning_agent",
          "prompt_template": "Analyze this task and identify major components: {{task_instruction}}",
          "expected_output": "component_analysis"
        },
        "next_steps": ["create_subtasks"]
      },
      {
        "step_id": "create_subtasks",
        "step_type": "parallel_execution",
        "parameters": {
          "subtasks": "{{component_analysis.subtasks}}",
          "agent_selection": "auto"
        },
        "next_steps": ["validate_breakdown"]
      },
      {
        "step_id": "validate_breakdown",
        "step_type": "agent_prompt",
        "parameters": {
          "agent_type": "task_evaluator",
          "validation_criteria": "completeness, feasibility, independence"
        }
      }
    ],
    "parameters_schema": {
      "task_instruction": {"type": "string", "required": true},
      "complexity_level": {"type": "string", "enum": ["simple", "moderate", "complex"], "default": "moderate"}
    },
    "success_criteria": ["all_subtasks_created", "dependencies_identified", "validation_passed"]
  }
}
```

## 5. Tool Entity Schema

### Tool Configuration Schema
```python
# core/entities/tool.py
from core.entities.base import BaseEntity, EntityType
from typing import List, Dict, Any, Optional
from enum import Enum

class ToolCategory(Enum):
    CORE = "core"
    SYSTEM = "system"
    EXTERNAL = "external"
    GENERATED = "generated"
    COMPOSED = "composed"

class ToolImplementationType(Enum):
    PYTHON_CLASS = "python_class"
    SHELL_COMMAND = "shell_command"
    API_CALL = "api_call"
    MCP_SERVER = "mcp_server"
    PROCESS_TEMPLATE = "process_template"

class ToolImplementation(BaseModel):
    type: ToolImplementationType
    module_path: Optional[str] = None
    class_name: Optional[str] = None
    command_template: Optional[str] = None
    api_endpoint: Optional[str] = None
    process_id: Optional[int] = None
    config: Dict[str, Any] = {}

class Tool(BaseEntity):
    ENTITY_TYPE = EntityType.TOOL
    
    description: str
    category: ToolCategory
    implementation: ToolImplementation
    parameters_schema: Dict[str, Any]
    permissions_required: List[str] = []
    dependencies: List[str] = []
    usage_count: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0
    
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        entities = {entity_type: [] for entity_type in EntityType}
        if self.implementation.process_id:
            entities[EntityType.PROCESS].append(self.implementation.process_id)
        return entities
    
    def validate_entity(self) -> bool:
        return bool(self.description and self.implementation and self.parameters_schema)

class ToolRegistry:
    """Manages tool discovery, creation, and composition"""
    
    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        
    async def discover_tools(self, capability_description: str) -> List[Tool]:
        """Find tools matching capability description"""
        pass
        
    async def compose_tools(self, tool_ids: List[int], composition_logic: Dict[str, Any]) -> Tool:
        """Create composite tool from existing tools"""
        pass
        
    async def create_tool_from_process(self, process_id: int, tool_config: Dict[str, Any]) -> Tool:
        """Create tool that executes a process template"""
        pass
```

## 6. Document Entity Schema

### Document Configuration Schema
```python
# core/entities/document.py
from core.entities.base import BaseEntity, EntityType
from typing import List, Dict, Any, Optional
from enum import Enum

class DocumentFormat(Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    HTML = "html"

class DocumentCategory(Enum):
    SYSTEM = "system"
    PROCESS = "process"
    REFERENCE = "reference"
    GUIDE = "guide"
    AGENT = "agent"
    TECHNICAL = "technical"

class DocumentAccessLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"

class Document(BaseEntity):
    ENTITY_TYPE = EntityType.DOCUMENT
    
    title: str
    content: str
    format: DocumentFormat = DocumentFormat.MARKDOWN
    category: DocumentCategory
    access_level: DocumentAccessLevel = DocumentAccessLevel.INTERNAL
    tags: List[str] = []
    updated_by_task_id: Optional[int] = None
    usage_count: int = 0
    effectiveness_score: float = 0.0
    
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        entities = {entity_type: [] for entity_type in EntityType}
        if self.updated_by_task_id:
            entities[EntityType.TASK].append(self.updated_by_task_id)
        return entities
    
    def validate_entity(self) -> bool:
        return bool(self.title and self.content and self.category)

class DocumentManager:
    """Manages document lifecycle and content"""
    
    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        
    async def search_documents(self, query: str, category: Optional[DocumentCategory] = None) -> List[Document]:
        """Search documents by content and metadata"""
        pass
        
    async def get_related_documents(self, entity_id: int, entity_type: EntityType) -> List[Document]:
        """Get documents related to an entity"""
        pass
        
    async def update_effectiveness_score(self, document_id: int, usage_outcome: str):
        """Update document effectiveness based on usage outcomes"""
        pass
```

## 7. Event Entity Schema

### Event Configuration Schema
```python
# core/entities/event.py
from core.entities.base import BaseEntity, EntityType
from typing import List, Dict, Any, Optional
from enum import Enum

class EventType(Enum):
    # Entity lifecycle events
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SPAWNED = "task_spawned"
    
    # Process events
    PROCESS_EXECUTED = "process_executed"
    PROCESS_STEP_COMPLETED = "process_step_completed"
    
    # Tool events
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"
    
    # Agent events
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_PROMPT_SENT = "agent_prompt_sent"
    AGENT_RESPONSE_RECEIVED = "agent_response_received"
    
    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_OPTIMIZATION = "system_optimization"
    REVIEW_TRIGGERED = "review_triggered"

class EventOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"

class Event(BaseEntity):
    ENTITY_TYPE = EntityType.EVENT
    
    event_type: EventType
    primary_entity_type: EntityType
    primary_entity_id: int
    related_entities: Dict[str, List[int]] = {}  # {entity_type: [entity_ids]}
    event_data: Dict[str, Any] = {}
    outcome: Optional[EventOutcome] = None
    tree_id: Optional[int] = None
    parent_event_id: Optional[int] = None
    duration_seconds: float = 0
    
    def get_related_entities(self) -> Dict[EntityType, List[int]]:
        entities = {entity_type: [] for entity_type in EntityType}
        entities[self.primary_entity_type].append(self.primary_entity_id)
        
        for entity_type_str, entity_ids in self.related_entities.items():
            entity_type = EntityType(entity_type_str)
            entities[entity_type].extend(entity_ids)
            
        if self.parent_event_id:
            entities[EntityType.EVENT].append(self.parent_event_id)
            
        return entities
    
    def validate_entity(self) -> bool:
        return bool(self.event_type and self.primary_entity_type and self.primary_entity_id)

class EventLogger:
    """Logs all system events for analysis and optimization"""
    
    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        
    async def log_event(self, event_type: EventType, primary_entity_type: EntityType, 
                       primary_entity_id: int, **kwargs) -> Event:
        """Log system event with related entities"""
        pass
        
    async def get_event_chain(self, root_event_id: int) -> List[Event]:
        """Get complete event chain from root event"""
        pass
        
    async def analyze_events(self, entity_type: EntityType, entity_id: int, 
                           time_window: Optional[int] = None) -> Dict[str, Any]:
        """Analyze events for optimization opportunities"""
        pass
```

## 8. Rolling Review Counter Schema

### Review Counter Configuration
```python
# core/review/counter.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class CounterType(Enum):
    USAGE = "usage"
    CREATION = "creation"
    MODIFICATION = "modification"
    ERROR = "error"
    SUCCESS = "success"
    FAILURE = "failure"

class ReviewFrequency(Enum):
    THRESHOLD = "threshold"  # Review when counter hits threshold
    PERIODIC = "periodic"    # Review on time schedule
    HYBRID = "hybrid"        # Both threshold and periodic

class ReviewCounter(BaseModel):
    entity_type: EntityType
    entity_id: int
    counter_type: CounterType
    count: int = 0
    threshold: int
    last_review_at: Optional[float] = None
    next_review_due: Optional[float] = None
    review_frequency: ReviewFrequency = ReviewFrequency.THRESHOLD

class ReviewManager:
    """Manages rolling review counters and triggers optimization reviews"""
    
    def __init__(self, entity_manager, task_manager):
        self.entity_manager = entity_manager
        self.task_manager = task_manager
        
    async def increment_counter(self, entity_type: EntityType, entity_id: int, 
                               counter_type: CounterType) -> bool:
        """Increment counter and check if review is needed"""
        pass
        
    async def check_review_triggers(self) -> List[Dict[str, Any]]:
        """Check all counters for review triggers"""
        pass
        
    async def trigger_optimization_review(self, entity_type: EntityType, entity_id: int, 
                                        trigger_reason: str) -> int:
        """Trigger optimization review task"""
        pass
        
    async def schedule_periodic_reviews(self):
        """Schedule periodic reviews based on time-based triggers"""
        pass
```

## 9. System Integration Schema

### Entity Communication Protocol
```python
# core/communication/protocol.py
from typing import Dict, Any, Optional
from enum import Enum

class MessageType(Enum):
    ENTITY_REQUEST = "entity_request"
    ENTITY_RESPONSE = "entity_response"
    EVENT_NOTIFICATION = "event_notification"
    REVIEW_REQUEST = "review_request"
    OPTIMIZATION_SUGGESTION = "optimization_suggestion"

class EntityMessage(BaseModel):
    message_id: str
    message_type: MessageType
    source_entity_type: EntityType
    source_entity_id: int
    target_entity_type: Optional[EntityType] = None
    target_entity_id: Optional[int] = None
    content: Dict[str, Any]
    priority: int = 1
    expires_at: Optional[float] = None
    created_at: float

class EntityCommunicationHub:
    """Manages communication between entities"""
    
    def __init__(self, entity_manager, event_logger):
        self.entity_manager = entity_manager
        self.event_logger = event_logger
        
    async def send_message(self, message: EntityMessage) -> bool:
        """Send message between entities"""
        pass
        
    async def broadcast_event(self, event: Event) -> List[int]:
        """Broadcast event to interested entities"""
        pass
        
    async def register_interest(self, entity_type: EntityType, entity_id: int, 
                               interest_patterns: List[str]):
        """Register entity interest in specific event patterns"""
        pass
```

## 10. Database Optimization Schema

### Entity Query Optimization
```sql
-- Performance indexes for entity operations
CREATE INDEX idx_entity_type_id ON events(primary_entity_type, primary_entity_id);
CREATE INDEX idx_event_type_timestamp ON events(event_type, timestamp);
CREATE INDEX idx_task_tree_status ON tasks(tree_id, status);
CREATE INDEX idx_entity_relationships_source ON entity_relationships(source_type, source_id);
CREATE INDEX idx_entity_relationships_target ON entity_relationships(target_type, target_id);
CREATE INDEX idx_review_counters_due ON review_counters(entity_type, next_review_due);

-- Entity usage tracking views
CREATE VIEW entity_usage_stats AS
SELECT 
    entity_type,
    entity_id,
    COUNT(*) as total_events,
    AVG(CASE WHEN outcome = 'success' THEN 1.0 ELSE 0.0 END) as success_rate,
    MAX(timestamp) as last_used
FROM events 
WHERE timestamp > datetime('now', '-30 days')
GROUP BY entity_type, entity_id;

-- Process effectiveness view
CREATE VIEW process_effectiveness AS
SELECT 
    p.id,
    p.name,
    p.usage_count,
    p.success_rate,
    AVG(e.duration_seconds) as avg_duration,
    COUNT(e.id) as recent_executions
FROM processes p
LEFT JOIN events e ON e.primary_entity_type = 'process' 
    AND e.primary_entity_id = p.id 
    AND e.timestamp > datetime('now', '-7 days')
GROUP BY p.id, p.name;
```

This entity-based architectural schema provides the foundation for a systematic, self-improving agent system that learns through structured processes and continuous event-driven optimization.