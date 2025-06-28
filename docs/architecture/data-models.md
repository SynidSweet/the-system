# Data Models & Database Architecture

*Last updated: 2025-06-28 | Updated by: /document command*

## Overview

The System employs a **dual-architecture approach** combining a legacy relational model with a modern entity-based architecture. This design enables gradual migration while maintaining system stability.

## Type Safety Framework (NEW: 2025-06-28)

### Comprehensive TypedDict Library

The system includes a centralized type definition library at `agent_system/core/types.py` providing type-safe data structures for all major system components:

#### Core Type Categories

**Task-Related Types:**
```python
class TaskMetadata(TypedDict, total=False):
    assigned_agent: str
    additional_context: List[str]
    additional_tools: List[str]
    agent_type: str
    execution_time_ms: int
    parent_task_id: Optional[int]
    tree_id: str
    priority: str

class TaskResult(TypedDict):
    success: bool
    result: Any
    error_message: Optional[str]
    metadata: Dict[str, Any]
```

**Agent-Related Types:**
```python
class AgentPermissions(TypedDict, total=False):
    web_search: bool
    file_system: bool
    shell_access: bool
    git_operations: bool
    database_write: bool
    spawn_agents: bool

class ModelConfig(TypedDict):
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    api_key: Optional[str]
```

**Event and Health Types:**
```python
class EventData(TypedDict, total=False):
    task_instruction: str
    agent_name: str
    error: str
    execution_time_ms: float
    outcome: str
    task_id: int
    agent_id: int
    tool_name: str

class HealthData(TypedDict, total=False):
    active_agents: int
    database: str
    task_manager: Dict[str, int]
    running_agents: int
    queued_tasks: int
    system_status: str
```

**API and Tool Types:**
```python
class APIResponse(TypedDict):
    success: bool
    data: Any
    error: Optional[str]
    timestamp: str

class ToolResult(TypedDict):
    tool: str
    success: bool
    result: Any
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    metadata: Dict[str, Any]
```

#### Type Literals and Aliases

```python
# Status literals for type safety
TaskStatus = Literal["pending", "in_progress", "completed", "failed", "cancelled"]
AgentStatus = Literal["active", "deprecated", "testing", "disabled"]
EntityType = Literal["agent", "task", "tool", "context_document", "process", "event"]

# Common type aliases
EntityID = int
TaskTreeID = str
AgentName = str
ToolName = str
```

#### Usage Patterns

**Import and Use TypedDict:**
```python
from agent_system.core.types import TaskMetadata, ToolResult, HealthData

def process_task(metadata: TaskMetadata) -> ToolResult:
    """Type-safe task processing with structured data"""
    agent_type = metadata['agent_type']  # IDE autocomplete
    tools = metadata.get('additional_tools', [])  # Optional field
    
    return {
        'tool': 'task_processor',
        'success': True,
        'result': processed_data,
        'error_message': None,
        'execution_time_ms': 1250,
        'metadata': {'agent': agent_type}
    }
```

### Benefits

1. **Enhanced IDE Support** - Full autocomplete and error detection
2. **Type Safety** - Catch type errors at development time
3. **Documentation** - Type definitions serve as living documentation
4. **Consistency** - Standardized data structures across modules
5. **Maintainability** - Centralized type definitions for easy updates

## Entity-Based Architecture (Primary)

### Base Entity Model

All entities inherit from a common base class providing:

```python
class Entity:
    entity_id: int              # Unique within entity type
    name: str                   # Human-readable identifier
    entity_type: EntityType     # AGENT|TASK|PROCESS|TOOL|DOCUMENT|EVENT
    version: str                # Semantic versioning (1.0.0)
    state: EntityState          # ACTIVE|INACTIVE|DEPRECATED|ARCHIVED|FAILED
    metadata: Dict[str, Any]    # Flexible additional properties
    created_at: datetime        # Creation timestamp
    updated_at: datetime        # Last modification
    relationships: Dict[str, List[int]]  # Graph connections
```

### Core Entity Types

#### 1. AgentEntity
Represents AI agents with specialized capabilities.

**Key Attributes:**
- `instruction`: Core directive defining agent behavior
- `context_documents`: Required documentation for operation
- `available_tools`: Permitted tool access list
- `permissions`: Security access levels
- `constraints`: Operational limitations
- `specializations`: Areas of expertise
- `dependencies`: Required entities

**Validation Rules:**
- Instruction must be meaningful (min 10 chars)
- Tools must reference valid ToolEntity IDs
- Permissions follow security hierarchy

#### 2. TaskEntity
Work units designed for isolated execution within process frameworks.

**Key Attributes:**
- `instruction`: Task description
- `parent_task_id`: Hierarchical parent reference
- `tree_id`: Common identifier for task trees
- `task_state`: Lifecycle state management
- `priority`: Execution priority (low|normal|high|critical)
- `assigned_agent`: Executing AgentEntity
- `assigned_process`: Governing ProcessEntity
- `result`/`error`: Execution outcomes
- `dependencies`: Required task completions
- `subtask_ids`: Child task references
- `conversation_history`: Agent interaction log
- `tool_calls`: Tool usage tracking

**State Machine:**
```
CREATED → PROCESS_ASSIGNED → READY_FOR_AGENT → 
AGENT_RESPONDING → TOOL_PROCESSING → COMPLETED/FAILED

Special States:
- WAITING_ON_DEPENDENCIES: Blocked on other tasks
- MANUAL_HOLD: Awaiting human approval
- MANUAL_STEP_REQUIRED: Step mode active
```

#### 3. ProcessEntity
Systematic frameworks governing task execution.

**Key Attributes:**
- `description`: Process purpose and overview
- `process_type`: Classification
  - DEFAULT: General purpose
  - TOOL_TRIGGERED: Responds to tool calls
  - EVENT_TRIGGERED: Responds to events
  - SYSTEM: Core system processes
  - RECOVERY: Error handling
- `implementation_path`: Python module location
- `parameters_schema`: JSON Schema for inputs
- `triggers`: Activation conditions
- `required_tools`/`required_context`: Dependencies
- `can_rollback`: Undo capability
- Performance metrics: execution counts, success rates

**Business Rules:**
- Tool-triggered processes must define triggers
- Implementation must be valid Python module
- Version increments on logic changes

#### 4. ToolEntity
Capabilities operating within process boundaries.

**Key Attributes:**
- `description`: Tool functionality
- `category`: Classification
  - CORE: Essential system tools
  - ANALYSIS: Data processing
  - COMMUNICATION: External interaction
  - DEVELOPMENT: Code operations
  - RESEARCH: Information gathering
  - SYSTEM: Internal operations
  - EXTERNAL: Third-party integrations
- `implementation`: Type (mcp|internal|process|external)
- `parameters`: JSON Schema for inputs
- `permissions`: Required security levels
- `requires_validation`: Manual approval flag
- `triggers_process`: Post-execution process
- Usage metrics: call counts, success rates

**Security Levels:**
- MINIMAL: Read-only operations
- STANDARD: Typical operations
- ELEVATED: System modifications

#### 5. ContextEntity
Knowledge and documentation resources.

**Key Attributes:**
- `title`: Document name
- `content`: Document body
- `category`: Classification
  - SYSTEM: Core documentation
  - GUIDE: How-to instructions
  - REFERENCE: API/technical docs
  - EXAMPLE: Code samples
  - PATTERN: Design patterns
  - SPECIFICATION: Requirements
  - KNOWLEDGE: Domain expertise
  - USER: User-provided content
- `format`: Content type (MARKDOWN|JSON|TEXT|YAML|CODE)
- `tags`: Searchable labels
- `parent_document_id`: Document hierarchy
- `access_count`: Usage tracking
- `referenced_by`: Entity references

#### 6. EventEntity
System events for tracking and optimization.

**Key Attributes:**
- `event_type`: Event classification
- `primary_entity_type`/`id`: Main entity involved
- `secondary_entity_type`/`id`: Related entity
- `outcome`: Result (SUCCESS|FAILURE|PARTIAL|ERROR|TIMEOUT)
- `data`: Flexible event details
- `analyzed`: Processing flag
- `patterns_detected`: Identified patterns
- `triggered_actions`: Resulting actions

**Event Types:**
- Entity lifecycle (created, updated, deleted)
- Task execution (started, completed, failed)
- Tool usage (called, completed, error)
- System events (optimization, review, error)

## Database Schema

### Entity Framework Tables

```sql
-- Central entity registry
CREATE TABLE entities (
    entity_id INTEGER,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT DEFAULT '1.0.0',
    state TEXT DEFAULT 'active',
    metadata JSON,
    created_by_task_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_type, entity_id)
);

-- Entity relationship graph
CREATE TABLE entity_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_type TEXT NOT NULL,
    source_entity_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,
    target_entity_type TEXT NOT NULL,
    target_entity_id INTEGER NOT NULL,
    strength REAL DEFAULT 1.0,
    context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_entity_type, source_entity_id, 
           relationship_type, target_entity_type, target_entity_id)
);

-- Process definitions
CREATE TABLE processes (
    process_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    template JSON NOT NULL,
    parameters_schema JSON,
    success_criteria JSON,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Process execution instances
CREATE TABLE process_instances (
    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_entity_id INTEGER NOT NULL,
    task_entity_id INTEGER NOT NULL,
    initiating_entity_type TEXT,
    initiating_entity_id INTEGER,
    state TEXT DEFAULT 'running',
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER,
    parameters JSON,
    execution_data JSON,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Comprehensive event log
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    parent_event_id INTEGER,
    task_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    outcome TEXT,
    data JSON,
    resource_usage JSON,
    error TEXT,
    user_id TEXT
);
```

### Optimization Tables

```sql
-- Usage-based review triggers
CREATE TABLE rolling_review_counters (
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    review_threshold INTEGER DEFAULT 100,
    usage_count INTEGER DEFAULT 0,
    last_review_date TIMESTAMP,
    next_review_threshold INTEGER,
    PRIMARY KEY (entity_type, entity_id)
);

-- Identified improvement opportunities
CREATE TABLE optimization_opportunities (
    opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    opportunity_type TEXT NOT NULL,
    description TEXT,
    confidence REAL,
    potential_impact TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Entity performance metrics
CREATE TABLE entity_effectiveness (
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    sample_size INTEGER,
    confidence_interval REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_type, entity_id, metric_name)
);
```

### Legacy Tables (Being Migrated)

```sql
-- Original agent definitions
CREATE TABLE agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    instruction TEXT NOT NULL,
    version TEXT DEFAULT '1.0.0',
    context_documents JSON,
    available_tools JSON,
    permissions JSON DEFAULT '{}',
    model_provider TEXT,
    model_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Original task tracking
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_task_id INTEGER,
    tree_id TEXT NOT NULL,
    agent_id INTEGER,
    instruction TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'normal',
    result TEXT,
    error TEXT,
    metadata JSON,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    depth INTEGER DEFAULT 0,
    max_depth INTEGER DEFAULT 10,
    timeout_seconds INTEGER DEFAULT 1800
);

-- Communication history
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parent_message_id INTEGER,
    tokens_used INTEGER,
    execution_time_ms INTEGER
);

-- Knowledge base
CREATE TABLE context_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    version TEXT DEFAULT '1.0.0',
    access_level TEXT DEFAULT 'standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool registry
CREATE TABLE tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    implementation JSON NOT NULL,
    parameters JSON,
    permissions JSON DEFAULT '{"security_level": "standard"}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Relationship Types

The system supports various relationship types between entities:

- **uses**: Entity requires another for operation
- **depends_on**: Hard dependency requirement
- **creates**: Entity generates another
- **optimizes**: Entity improves another
- **triggers**: Entity initiates another
- **references**: Documentation reference
- **contains**: Parent-child relationship
- **inherits**: Derives properties from another
- **specializes**: More specific version
- **generalizes**: More abstract version

## State Management

### Entity States
```
ACTIVE → INACTIVE → DEPRECATED → ARCHIVED
         ↓
       FAILED
```

### Task States
```
CREATED → PROCESS_ASSIGNED → CONTEXT_ASSIGNED → 
TOOLS_ASSIGNED → READY_FOR_AGENT → AGENT_RESPONDING →
TOOL_PROCESSING → COMPLETED/FAILED

Blocking States:
- WAITING_ON_DEPENDENCIES
- MANUAL_HOLD
- MANUAL_STEP_REQUIRED
```

### Process Instance States
```
running → completed/failed/cancelled
```

## Validation Rules

1. **Entity Validation**
   - Names must be unique within entity type
   - Instructions/descriptions must be meaningful
   - References must point to existing entities
   - State transitions must follow defined paths

2. **Relationship Validation**
   - Both entities must exist
   - Relationship type must be valid
   - Circular dependencies prevented
   - Strength values between 0.0 and 1.0

3. **Task Validation**
   - Parent tasks must exist in same tree
   - Depth limits enforced (default: 10)
   - Timeout limits enforced (default: 30 min)
   - Priority must be valid level

4. **Process Validation**
   - Implementation path must exist
   - Parameters must match schema
   - Triggers must reference valid entities
   - Tool requirements must be satisfiable

## Performance Considerations

1. **Indexing Strategy**
   - Primary keys on all entity tables
   - Composite indexes for relationships
   - Indexes on frequently queried fields (state, type)
   - Full-text search on content fields

2. **Query Optimization**
   - Relationship queries use covering indexes
   - Event queries filtered by timestamp ranges
   - Batch operations for bulk updates
   - Connection pooling for concurrent access

3. **Data Retention**
   - Events older than 90 days archived
   - Completed tasks compressed after 30 days
   - Optimization data aggregated monthly
   - Inactive entities archived quarterly

The data model supports a self-improving system where every operation generates trackable events, relationships evolve based on usage, and optimization opportunities emerge from patterns in the data.