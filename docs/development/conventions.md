# Development Conventions & Code Standards

*Last updated: 2025-06-28 | Updated by: /document command (updated import patterns)*

## Overview

This document outlines the coding conventions, design patterns, and development practices used in The System. Following these conventions ensures consistency, maintainability, and alignment with the process-first architecture.

## Code Organization

### Import Conventions

#### Relative Import Pattern (UPDATED: 2025-06-28)
**CRITICAL**: The system now uses relative imports exclusively. All absolute imports have been converted to relative imports for proper module resolution.

```python
# CORRECT: Relative imports within modules
# From API module to core:
from ...core.entities import TaskEntity, AgentEntity, TaskState
from ...config.database import DatabaseManager

# From core entities to events:
from ..events.event_types import EntityType
from ..events.event_manager import EventManager

# From managers to entities:
from ..base import Entity, EntityState
from ...events.event_types import EntityType

# Within same directory:
from .entity_manager import EntityManager
from .managers.agent_manager import AgentManager
```

#### Entity-Based Architecture Imports
The system uses entity-based architecture with modular entity managers:
```python
# CORRECT: Entity manager usage (with relative imports)
entity_manager = EntityManager(db_path, event_manager)

# Access type-specific managers through facade
agents = await entity_manager.agents.find_by_capability("web_search")
tasks = await entity_manager.tasks.find_by_status(TaskState.READY_FOR_AGENT)
```

#### Legacy Compatibility Pattern
When migrating from old models, use type aliases for backward compatibility:
```python
# Type aliases for backward compatibility
Task = TaskEntity
Agent = AgentEntity
Tool = ToolEntity
ContextDocument = ContextEntity
TaskStatus = TaskState

# Temporary compatibility models during migration
class MCPToolResult(BaseModel):
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None
```

#### Import Pattern Guidelines
```python
# WRONG: Absolute imports (causes module resolution issues)
from agent_system.core.entities import TaskEntity
from agent_system.api.main import database

# CORRECT: Relative imports (proper module resolution)
from ..core.entities import TaskEntity
from .main import database

# WRONG: Legacy imports (archived/deprecated)
from .models import Task, Agent, Message  # models.py archived
from core.database_manager import database  # moved to config.database
```

#### Import Fix Methodology (Reference)
When converting absolute imports to relative imports:
1. Calculate module depth from current file to target
2. Use dots (`.`) to navigate up directory levels
3. Append remaining module path after dots
4. Test imports to ensure proper resolution

### Directory Structure
```
agent_system/
├── api/              # FastAPI REST/WebSocket endpoints
├── core/             # Core system components
│   ├── entities/     # Entity implementations (6 types)
│   ├── events/       # Event management system
│   ├── knowledge/    # Knowledge assembly engine
│   ├── permissions/  # Permission management
│   ├── processes/    # Process implementations
│   └── runtime/      # Task execution runtime
├── tools/            # Tool implementations
│   ├── core_mcp/     # Core MCP tools
│   ├── mcp_servers/  # MCP server integrations
│   └── system_tools/ # Internal system tools
├── web/              # React frontend application
├── scripts/          # System management scripts
├── database/         # Database migrations
├── context_documents/# System documentation
└── knowledge/        # Knowledge base storage
```

### Module Organization
- One primary class per file
- Related helper classes in same module
- Clear separation of concerns
- Process-first organization (processes before implementations)

## Naming Conventions

### File Naming Standards (Updated 2025-06-28)

#### Entity Files
Use clear, purpose-driven names without redundant suffixes:
```
# CORRECT: Clean entity file names
core/entities/agent.py      # Not agent_entity.py
core/entities/task.py       # Not task_entity.py
core/entities/tool.py       # Not tool_entity.py
core/entities/context.py    # Not context_entity.py
core/entities/process.py    # Not process_entity.py
core/entities/event.py      # Not event_entity.py
```

#### Process Files
Use specific, descriptive names rather than generic terms:
```
# CORRECT: Specific process file names
core/processes/base_process.py      # Not base.py
core/processes/process_registry.py  # Not registry.py
core/processes/neutral_task_process.py
core/processes/system_initialization_process.py
```

#### Import Pattern Updates
With the new naming conventions, use these import patterns:
```python
# CORRECT: Entity imports with new file names
from agent_system.core.entities.agent import AgentEntity
from agent_system.core.entities.task import TaskEntity, TaskState
from agent_system.core.entities.context import ContextEntity, ContextCategory

# CORRECT: Process imports with new file names  
from agent_system.core.processes.base_process import BaseProcess, ProcessResult
from agent_system.core.processes.process_registry import ProcessRegistry
```

### Python Code Naming
```python
# Classes: PascalCase
class UniversalAgentRuntime:
    pass

# Functions/Methods: snake_case
def execute_with_timeout(timeout: int) -> Any:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_MODEL_PROVIDER = "google"
MAX_CONCURRENT_AGENTS = 3

# Private methods: underscore prefix
def _build_prompt(self) -> str:
    pass

# Enums: PascalCase class, UPPER_SNAKE_CASE values
class EntityType(str, Enum):
    AGENT = "agent"
    TASK = "task"
    PROCESS = "process"
```

### JavaScript/React
```javascript
// Components: PascalCase
function TaskTreeVisualization() {}

// Functions: camelCase
function handleTaskSubmit() {}

// Constants: UPPER_SNAKE_CASE
const MAX_RETRIES = 3;

// CSS classes: kebab-case
className="task-tree-container"
```

## Type Hints & Validation

### Type Safety Framework (NEW: 2025-06-28)

The system uses comprehensive type hints for enhanced code clarity and IDE support. All type definitions are centralized in `agent_system/core/types.py`.

#### TypedDict Library
Use TypedDict for structured data instead of generic dictionaries:
```python
from agent_system.core.types import (
    TaskMetadata, TaskResult, AgentPermissions, ModelConfig,
    EventData, ToolResult, HealthData, ContextPackage,
    APIResponse, ErrorResponse, KnowledgeGap
)

# CORRECT: Use TypedDict for structured data
def process_task_metadata(metadata: TaskMetadata) -> None:
    agent_type = metadata['agent_type']  # Type-safe access
    tools = metadata.get('additional_tools', [])

# WRONG: Generic dictionary
def process_task_metadata(metadata: Dict[str, Any]) -> None:
    agent_type = metadata['agent_type']  # No type safety
```

#### Return Type Annotations (Required)
All functions must have return type annotations:
```python
# CORRECT: Functions with return type annotations
async def init_database() -> bool:
    """Initialize database connection and schema"""
    pass

def test_knowledge_system() -> None:
    """Test the knowledge system after bootstrap."""
    pass

async def health_check() -> bool:
    """Perform system health checks"""
    pass

# WRONG: Missing return type annotations
async def init_database():  # Missing -> bool
    pass

def __init__(self):  # Missing -> None
    pass
```

#### Type Consistency Patterns
Follow these patterns for type imports and usage:
```python
# Standard typing imports
from typing import Dict, List, Optional, Any, Union, Literal
from typing import TYPE_CHECKING  # For consistency in enum files

# Import structured types from central library
from agent_system.core.types import (
    TaskStatus, AgentStatus, EntityType,  # Literal types
    TaskMetadata, ToolResult, EventData,   # TypedDict classes
    EntityID, TaskTreeID, AgentName        # Type aliases
)

# Type-safe function signatures
async def create_task(
    instruction: str,
    metadata: TaskMetadata,
    agent_type: Optional[AgentName] = None
) -> TaskResult:
    pass
```

#### Available TypedDict Classes
The comprehensive type library includes:

**Task Types**:
- `TaskMetadata` - Task configuration and context
- `TaskResult` - Task execution results
- `TaskStatus` - Task state literals

**Agent Types**:
- `AgentPermissions` - Agent capability permissions
- `ModelConfig` - AI model configuration
- `AgentStatus` - Agent state literals

**Event Types**:
- `EventData` - System event information
- `HealthData` - System health check data

**Tool Types**:
- `ToolResult` - Tool execution results
- `ToolConfig` - Tool configuration

**API Types**:
- `APIResponse` - Standard API response format
- `ErrorResponse` - Error response format

**Knowledge Types**:
- `KnowledgeGap` - Knowledge system gaps
- `ContextPackage` - Assembled context data

**Common Aliases**:
- `EntityID`, `TaskTreeID`, `AgentName` - Type-safe identifiers

### Type Hints
Always use type hints for function signatures:
```python
from typing import Dict, List, Optional, Any, Union

async def execute_query(
    self, 
    query: str, 
    params: Optional[tuple] = None
) -> List[Dict[str, Any]]:
    pass
```

### Pydantic Models
Use Pydantic for data validation:
```python
from pydantic import BaseModel, Field

class TaskRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    priority: str = Field(default="normal")
    metadata: Optional[Dict[str, Any]] = None
```

## Async/Await Patterns

### Async by Default
All I/O operations should be async:
```python
async def get_agent(self, agent_id: int) -> Optional[AgentEntity]:
    async with self.db_manager.get_connection() as conn:
        result = await conn.execute(query, (agent_id,))
        row = await result.fetchone()
```

### Context Managers
Use async context managers for resource management:
```python
@asynccontextmanager
async def event_context(self, tree_id: Optional[int] = None):
    context = EventContext(tree_id=tree_id)
    try:
        yield context
    finally:
        await self._process_events(context)
```

### Concurrency Control
Use locks for thread-safe operations:
```python
self._flush_lock = asyncio.Lock()

async def flush_events(self):
    async with self._flush_lock:
        # Thread-safe event flushing
```

## Design Patterns

### Entity Manager Pattern (NEW: 2025-06-28)

The system uses a modular entity manager architecture with facade pattern:

#### Facade Pattern for Backward Compatibility
```python
# Main EntityManager provides unified interface
entity_manager = EntityManager(db_path, event_manager)

# Backward compatible usage
agent = await entity_manager.create_entity(EntityType.AGENT, "test_agent", **data)

# Direct manager access (preferred for new code)
agents = await entity_manager.agents.find_by_capability("web_search")
tasks = await entity_manager.tasks.find_by_status(TaskState.READY_FOR_AGENT)
```

#### Type-Specific Manager Implementation
When creating new entity managers, follow this pattern:
```python
from .base_manager import BaseManager

class MyEntityManager(BaseManager):
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.MY_ENTITY,
            entity_class=MyEntity,
            event_manager=event_manager
        )
    
    # Add type-specific methods
    async def find_by_custom_field(self, value: str) -> List[MyEntity]:
        entities = await self.list(limit=1000)
        return [e for e in entities if e.custom_field == value]
    
    # Implement abstract methods
    async def _create_type_specific_record(self, db, entity_id, name, **kwargs):
        await db.execute("INSERT INTO my_entities ...", (...))
```

#### Manager Usage Patterns
```python
# Accessing specific managers through facade
async def example_usage():
    entity_manager = EntityManager(db_path)
    
    # Agent operations
    agents_with_tool = await entity_manager.agents.find_by_capability("web_search")
    await entity_manager.agents.add_context_document(agent_id, "new_doc")
    
    # Task operations  
    pending_tasks = await entity_manager.tasks.find_by_status(TaskState.READY_FOR_AGENT)
    await entity_manager.tasks.assign_agent(task_id, "agent_name")
    
    # Tool operations
    tools_by_category = await entity_manager.tools.find_by_category(ToolCategory.ANALYSIS)
    await entity_manager.tools.record_execution(tool_id, success=True, execution_time=1.5)
```

### Abstract Base Classes
Define interfaces using ABC:
```python
from abc import ABC, abstractmethod

class Entity(ABC):
    @abstractmethod
    def validate(self) -> None:
        """Validate entity state"""
        pass
```

### Factory Pattern
Use factories for creating complex objects:
```python
class AIModelManager:
    def get_provider(self, provider_name: str) -> AIModelProvider:
        if provider_name == "google":
            return GoogleProvider()
        elif provider_name == "anthropic":
            return AnthropicProvider()
```

### Registry Pattern
Use registries for dynamic component management:
```python
class MCPToolRegistry:
    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
    
    def register_server(self, name: str, server: MCPServer):
        self._servers[name] = server
```

### Repository Pattern (NEW: 2025-06-28)

The system implements a comprehensive repository pattern for data access abstraction, improving testability and separation of concerns.

#### Repository Interface & Implementation
```python
# Use Protocol-based repository interface for type safety
from agent_system.core.repositories import Repository, RepositoryFactory, RepositoryManager
from agent_system.core.events.event_types import EntityType

# Pattern 1: Repository Manager (Recommended)
repo_manager = RepositoryManager(db_path="/path/to/db", event_manager=event_manager)

# Access type-specific repositories
agents = await repo_manager.agents.find_by_capability("web_search")
tasks = await repo_manager.tasks.find_by_status("pending") 
await repo_manager.agents.add_context_document(agent_id, "new_doc")

# Pattern 2: Factory Pattern
agent_repo = RepositoryFactory.create_repository(
    EntityType.AGENT,
    db_path="/path/to/db",
    event_manager=event_manager
)
```

#### Repository Architecture Components
- **`Repository[T]` Protocol**: Type-safe interface defining standard CRUD operations
- **`BaseRepository`**: Abstract base class with common database operations and caching
- **Entity-Specific Repositories**: `AgentRepository`, `TaskRepository` with specialized methods
- **`RepositoryFactory`**: Factory pattern for repository creation and management
- **`RepositoryManager`**: Unified interface providing access to all repositories

#### Testing with In-Memory Repositories
```python
# Create in-memory repositories for testing (no database setup required)
agent_repo = RepositoryFactory.create_repository(
    EntityType.AGENT,
    db_path="memory",  # Not used for in-memory
    use_memory=True
)

# Test agent operations without database
agent = await agent_repo.create({
    'name': 'test_agent',
    'instruction': 'Test instruction',
    'available_tools': ['search']
})

# All repository methods work identically
search_agents = await agent_repo.find_by_capability('search')
assert len(search_agents) == 1
```

#### Repository Implementation Pattern
When creating new repositories, follow this structure:
```python
from agent_system.core.repositories import BaseRepository
from agent_system.core.events.event_types import EntityType

class MyEntityRepository(BaseRepository[MyEntity]):
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.MY_ENTITY,
            entity_class=MyEntity,
            event_manager=event_manager
        )
    
    # Add entity-specific query methods
    async def find_by_custom_field(self, value: str) -> List[MyEntity]:
        entities = await self.list(limit=1000)
        return [e for e in entities if e.custom_field == value]
    
    # Implement required abstract methods for database operations
    async def _insert_type_specific(self, db, entity_id: int, entity_data: Dict[str, Any]):
        await db.execute("INSERT INTO my_entities ...", (...))
    
    async def _get_type_specific(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        cursor = await db.execute("SELECT * FROM my_entities WHERE id = ?", (entity_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
```

#### Repository Benefits Achieved
- **Type Safety**: Protocol-based interfaces with IDE autocomplete support
- **Testability**: Easy swap between database and in-memory implementations
- **Separation of Concerns**: Business logic isolated from data access details
- **Consistency**: Standardized CRUD operations across all entity types
- **Performance**: Built-in caching and optimized database queries
- **Extensibility**: Support for multiple storage backends through interface

#### Repository vs Direct Database Access
```python
# BEFORE: Direct database access (tightly coupled)
async def get_agents_with_tool(tool_name: str):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM agents WHERE available_tools LIKE ?",
            (f"%{tool_name}%",)
        )
        rows = await cursor.fetchall()
        return [AgentEntity.from_dict(dict(row)) for row in rows]

# AFTER: Repository pattern (abstracted and testable)
async def get_agents_with_tool(tool_name: str):
    return await agent_repo.find_by_capability(tool_name)
```

### FastAPI Router Pattern (Modular API)
**NEW**: Organize API endpoints using FastAPI routers for separation of concerns:

```python
# api/routes/tasks.py
from fastapi import APIRouter, Depends
from agent_system.config.database import DatabaseManager

# Dependencies
def get_database():
    """Get database instance for dependency injection"""
    from agent_system.api.main import database
    return database

def get_runtime_integration():
    """Get runtime integration instance"""
    from agent_system.api.startup import get_runtime_integration as _get_runtime
    return _get_runtime()

# Create router
router = APIRouter()

@router.post("")
async def submit_task(
    submission: TaskSubmission,
    database: DatabaseManager = Depends(get_database),
    runtime = Depends(get_runtime_integration)
):
    """Submit a new task for execution"""
    # Clean, focused endpoint logic

# api/main.py - Include routers
from agent_system.api.routes import tasks, entities, admin

app = FastAPI(lifespan=lifespan)
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(entities.router, prefix="", tags=["entities"])
app.include_router(admin.router, prefix="", tags=["admin", "system"])
```

**Module Organization Guidelines**:
- Group related endpoints in logical routers
- Use dependency injection for shared resources
- Keep each router module under 400 lines
- Maintain consistent naming: `routes/{domain}.py`
- Use prefix and tags for API organization

### Result Objects
Return structured results instead of raising exceptions:
```python
@dataclass
class ToolResult:
    success: bool
    result: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

## Error Handling

### Centralized Exception Handling (API Layer)
**NEW**: Use centralized exception handling middleware for API endpoints:

```python
# Import custom exceptions
from agent_system.api.exceptions import (
    EntityNotFoundError, 
    ValidationError, 
    TaskExecutionError, 
    RuntimeError as AgentRuntimeError,
    DatabaseError
)

# API endpoint example - NO try-catch needed
@app.post("/tasks")
async def submit_task(submission: TaskSubmission):
    """Submit a new task - middleware handles exceptions"""
    if not runtime_integration:
        raise AgentRuntimeError("Runtime integration not initialized")
    
    if not submission.instruction.strip():
        raise ValidationError("Task instruction cannot be empty")
    
    # Business logic without exception handling
    task_id = await runtime_integration.create_task(...)
    task = await database.tasks.get_by_id(task_id)
    
    if not task:
        raise EntityNotFoundError(f"Task {task_id} not found after creation")
    
    return TaskResponse(...)
```

**Exception Types Available:**
- `EntityNotFoundError` → 404 responses
- `ValidationError` → 400 responses  
- `TaskExecutionError` → 422 responses
- `AgentRuntimeError` → 503 responses
- `DatabaseError` → 503 responses
- `ConfigurationError` → 500 responses

**Middleware provides:**
- Consistent JSON error format with type, message, code, timestamp
- Comprehensive logging with request context
- Security-conscious error messages
- Proper HTTP status code mapping

### Service Layer Error Handling
For non-API code, use Result objects and comprehensive error handling:
```python
try:
    result = await self.execute_tool(tool_name, params)
except ToolNotFoundError as e:
    logger.error(f"Tool not found: {tool_name}")
    return ToolResult(success=False, error_message=str(e))
except Exception as e:
    logger.exception(f"Unexpected error executing {tool_name}")
    return ToolResult(success=False, error_message=f"Internal error: {str(e)}")
```

### Error Context
Always include context in error messages:
```python
raise ValueError(
    f"Invalid entity state transition: {current_state} -> {new_state} "
    f"for entity {self.entity_type}:{self.entity_id}"
)
```

### Graceful Degradation
Provide fallback mechanisms:
```python
if self.runtime_agent:
    return await self.runtime_agent.call_tool(tool_name, arguments)
else:
    # Fallback to direct execution
    return await self._execute_tool_directly(tool_name, arguments)
```

## Process-First Development

### Framework Establishment
Every feature must establish systematic frameworks:
```python
# WRONG: Direct implementation
async def handle_task(task: str):
    # Immediately starts executing
    result = await execute(task)

# CORRECT: Process-first
async def handle_task(task: str):
    # First establish framework
    process = await discover_process(task)
    framework = await establish_framework(process)
    # Then execute within framework
    result = await execute_within_framework(task, framework)
```

### Isolated Task Success
Design tasks to succeed independently:
```python
class TaskEntity:
    def validate_isolation(self) -> bool:
        """Ensure task has all required context for isolated execution"""
        return all([
            self.has_required_context(),
            self.has_required_tools(),
            self.has_clear_success_criteria()
        ])
```

## Configuration Management

### Configuration-Driven Architecture

**NEW**: The system uses YAML-based configuration to separate data from execution logic:

```python
# CORRECT: Configuration-driven seeding
from scripts.seeders import SystemSeeder, load_configuration

async def seed_system():
    # Load configuration from YAML files
    config = load_configuration("config/seeds")
    
    # Use modular seeders
    seeder = SystemSeeder(database, "config/seeds")
    await seeder.seed_all()

# WRONG: Hardcoded configuration in code
async def seed_system():
    agents = [
        {
            "name": "agent_name",
            "instruction": "Very long hardcoded instruction...",
            # ... 100+ lines of configuration
        }
    ]
```

### Configuration File Structure

Organize configuration files by entity type:
```
agent_system/config/seeds/
├── agents.yaml      # Agent definitions with instructions & permissions
├── tools.yaml       # Tool configurations with implementations
├── documents.yaml   # Context document specifications
└── README.md        # Configuration documentation
```

### Configuration Validation

Use Pydantic models for type-safe configuration:
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class AgentConfig(BaseModel):
    name: str
    instruction: str
    context_documents: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    permissions: AgentPermissions = Field(default_factory=AgentPermissions)

# Validation happens automatically
config = AgentConfig(**yaml_data)  # Raises ValidationError if invalid
```

### Modular Seeder Pattern

Create focused seeder classes for each entity type:
```python
class BaseSeeder(ABC):
    def __init__(self, database_manager):
        self.database = database_manager
    
    @abstractmethod
    async def seed(self, config: SeedConfiguration) -> bool:
        pass

class AgentSeeder(BaseSeeder):
    async def seed(self, config: SeedConfiguration) -> bool:
        # Agent-specific seeding logic
        for agent_config in config.agents:
            # Create and validate agent
            await self.database.agents.create(agent)
```

### Configuration Best Practices

1. **Separation of Concerns**: Keep configuration data separate from execution logic
2. **Type Safety**: Use Pydantic models for validation
3. **Idempotent Operations**: Make seeding safe to run multiple times
4. **Version Control**: Track configuration changes in git
5. **Documentation**: Maintain comprehensive configuration documentation
6. **Validation**: Validate configuration before execution
7. **Rollback Safety**: Preserve legacy versions for rollback capability

## Testing Conventions

### Test Organization
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interactions
├── functional/     # End-to-end functional tests
└── performance/    # Performance and load tests
```

### Test Naming
```python
# Test files: test_<module_name>.py
test_universal_agent_runtime.py

# Test functions: test_<functionality>_<scenario>
async def test_task_execution_with_timeout():
    pass

async def test_agent_selection_no_suitable_agent():
    pass
```

### Async Testing
```python
import asyncio

class TestSystem:
    async def test_async_operation(self):
        result = await async_function()
        assert result.success
```

## Documentation Standards

### Docstrings
Use clear, concise docstrings:
```python
def establish_framework(self, domain: str) -> ProcessFramework:
    """
    Establish systematic framework for domain.
    
    Creates comprehensive process framework including rules,
    regulations, and boundaries for systematic execution.
    """
```

### Inline Comments
Use sparingly, explain "why" not "what":
```python
# Batch events for efficiency - reduces database writes by 90%
if len(self._event_queue) >= self.batch_size:
    await self._flush_events()
```

### Process Documentation
Document all processes in `context_documents/processes/`:
```markdown
# Process: Neutral Task Execution

## Purpose
Transform undefined tasks into systematic execution plans.

## Steps
1. Process discovery
2. Framework establishment
3. Task decomposition
4. Isolated execution
```

### Module-Level Documentation (NEW: 2025-06-28)
Each major module has a comprehensive CLAUDE.md file for AI agent guidance:

#### Available Module Guides
- **`agent_system/core/CLAUDE.md`**: Core system logic, entity management, runtime
- **`agent_system/tools/CLAUDE.md`**: Tool ecosystem, MCP integration, permissions
- **`agent_system/api/CLAUDE.md`**: Web API endpoints, WebSocket, middleware
- **`agent_system/core/processes/CLAUDE.md`**: Process frameworks, domain analysis
- **`agent_system/database/CLAUDE.md`**: Database layer, migrations, relationships

#### CLAUDE.md Structure
Each module guide includes:
```markdown
# CLAUDE.md - [Module Name]

## Module Overview
Brief description and role in system

## Key Components
- Component locations and purposes

## Common Tasks
- Step-by-step guidance for typical operations
- Code examples and patterns

## Architecture & Patterns
- Design patterns used
- Integration points

## Testing
- Testing approaches and examples

## Gotchas & Tips
- Known issues and debugging approaches
```

#### When to Update Module Documentation
- After adding new features to a module
- When architectural patterns change
- When new integration points are created
- When common tasks or patterns evolve
- During major refactoring efforts

## Database Conventions

### Query Safety
Always use parameterized queries:
```python
# WRONG
query = f"SELECT * FROM agents WHERE name = '{name}'"

# CORRECT
query = "SELECT * FROM agents WHERE name = ?"
result = await conn.execute(query, (name,))
```

### Transaction Management
Use explicit transactions for multi-step operations:
```python
async with self.db_manager.transaction() as conn:
    await conn.execute(insert_query, params)
    await conn.execute(update_query, params)
    # Automatically commits or rolls back
```

## Configuration Management

### Environment Variables
Use environment variables for configuration:
```python
import os
from typing import Optional

DEFAULT_MODEL_PROVIDER = os.getenv("DEFAULT_MODEL_PROVIDER", "google")
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "3"))
```

### Settings Validation
Validate configuration on startup:
```python
class Settings:
    def validate(self):
        if not any([self.anthropic_key, self.openai_key, self.google_key]):
            raise ValueError("At least one AI provider API key required")
```

## Security Practices

### Never Hardcode Secrets
```python
# WRONG
api_key = "sk-1234567890abcdef"

# CORRECT
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")
```

### Permission Checking
Always verify permissions before operations:
```python
if not self.has_permission(agent_id, tool_name):
    raise PermissionError(f"Agent {agent_id} lacks permission for {tool_name}")
```

### Input Validation
Validate all external inputs:
```python
def validate_instruction(instruction: str) -> str:
    if len(instruction) < 10:
        raise ValueError("Instruction too short")
    if len(instruction) > 10000:
        raise ValueError("Instruction too long")
    return instruction.strip()
```

## Performance Considerations

### Batch Operations
Batch database operations when possible:
```python
# Instead of individual inserts
events = []
for event in event_queue:
    events.append((event.type, event.data))

# Batch insert
await conn.executemany(
    "INSERT INTO events (type, data) VALUES (?, ?)",
    events
)
```

### Lazy Loading
Load data only when needed:
```python
@property
async def context_documents(self):
    if self._context_documents is None:
        self._context_documents = await self._load_context_documents()
    return self._context_documents
```

### Resource Limits
Enforce resource limits:
```python
MAX_TASK_DEPTH = 10
MAX_EXECUTION_TIME = 1800  # 30 minutes
MAX_CONCURRENT_TASKS = 100
```

## Version Control Practices

### Commit Messages
Use clear, descriptive commit messages:
```
feat: Add process discovery agent for framework establishment
fix: Resolve timeout issue in task execution
docs: Update process-first architecture documentation
refactor: Extract entity validation into base class
```

### Branch Naming
- `feature/process-discovery-agent`
- `fix/timeout-handling`
- `docs/architecture-overview`
- `refactor/entity-base-class`

## Code Review Checklist

Before submitting code:
- [ ] Follows process-first principles
- [ ] Includes type hints
- [ ] Has error handling
- [ ] Includes tests
- [ ] Updates documentation
- [ ] No hardcoded values
- [ ] Async operations used appropriately
- [ ] Resource limits enforced
- [ ] Security considerations addressed

Following these conventions ensures that all development aligns with the system's process-first architecture and maintains high code quality standards.