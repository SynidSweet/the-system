# System Architecture Overview

*Last updated: 2025-06-28 | Updated by: /document command*

## 🎉 Major Architectural Milestone Reached

**ALL MAJOR REFACTORING COMPLETED** (2025-06-28) - The system architecture has undergone comprehensive transformation with 95 files changed and 14,489 insertions, establishing a robust foundation for process-first development. **CRITICAL**: 175 absolute imports across 63 files require immediate attention for system initialization.

## Introduction

The System is a **process-first recursive agent architecture** that transforms undefined problems into systematic domains with established frameworks before execution. This document provides a comprehensive overview of the system's architecture, design decisions, and implementation details.

## Core Architecture Principles

### 1. Process-First Foundation
Every task entering the system undergoes systematic structural analysis before execution:
- **Process Discovery**: Analyzes domain requirements and establishes frameworks
- **Framework Validation**: Ensures completeness before decomposition
- **Isolated Execution**: Each subtask succeeds independently within boundaries
- **No Ad-Hoc Solutions**: All work happens within systematic frameworks

### 2. Entity-Based Design
The system is built on 6 fundamental entity types that drive all behavior:

```
Entity (Abstract Base)
├── AgentEntity     - AI agents with specialized capabilities
├── ProcessEntity   - Systematic frameworks and workflows  
├── TaskEntity      - Work units designed for isolation
├── ToolEntity      - Capabilities with permission boundaries
├── ContextEntity   - Knowledge and documentation
└── EventEntity     - System events for optimization
```

### 3. Event-Driven Architecture
All system operations generate events for tracking, learning, and optimization:
- Hierarchical event chains track causality
- Resource usage monitoring for efficiency
- Automatic optimization opportunity detection
- Rolling review triggers based on usage patterns

## System Components

### Universal Agent Runtime
**Location**: `agent_system/core/universal_agent_runtime.py`

The runtime executes all agents within systematic frameworks:
- Process discovery and framework establishment
- AI model integration (Gemini, Claude, GPT)
- Tool execution with permission checking
- Comprehensive message and event logging
- State management and error handling

### Entity Management System
**Location**: `agent_system/core/entities/`

**Modular Entity Management Architecture** (Refactored 2025-06-28):
```
entities/
├── entity_manager.py - Main facade for backward compatibility
├── managers/ - Type-specific entity managers:
│   ├── base_manager.py (249 lines) - Abstract base with common CRUD operations
│   ├── db_operations.py (124 lines) - Shared database operations helper
│   ├── agent_manager.py (164 lines) - Agent-specific operations & queries
│   ├── task_manager.py (208 lines) - Task lifecycle & tree management
│   ├── tool_manager.py (209 lines) - Tool permissions & categories
│   ├── context_manager.py (207 lines) - Document search & tagging
│   ├── process_manager.py (189 lines) - Process triggers & requirements
│   └── event_manager.py (123 lines) - Event entity queries
└── [entity_type]_entity.py - Entity model definitions
```

**Key Features**:
- **Facade Pattern**: Main EntityManager provides backward compatibility while enabling direct manager access
- **Type-Specific Operations**: Each manager offers specialized methods (e.g., `find_by_capability`, `find_by_status`)
- **Clean Separation**: Each entity type has focused, isolated management logic
- **Improved Testability**: Individual managers can be tested independently
- **Performance Optimization**: Smaller, focused caches per entity type
- **Enhanced Maintainability**: Changes to one entity type don't affect others

**Common Operations** (available on all managers):
- Entity creation with validation
- Relationship tracking (uses, depends_on, creates)
- State transitions with event generation
- Version management for updates
- Effectiveness tracking for optimization

**Specialized Operations** (examples):
- **AgentManager**: `find_by_capability()`, `add_context_document()`
- **TaskManager**: `find_by_status()`, `find_by_tree()`, `assign_agent()`
- **ToolManager**: `find_by_category()`, `record_execution()`
- **ContextManager**: `find_by_tag()`, `clone_document()`

### Repository Pattern (NEW: 2025-06-28)
**Location**: `agent_system/core/repositories/`

**Data Access Abstraction Layer** for clean separation of concerns and enhanced testability:
```
repositories/
├── repository_interface.py - Protocol-based type-safe interfaces
├── base_repository.py - Abstract base with common database operations
├── repository_factory.py - Factory pattern for repository creation
├── memory_repository.py - In-memory implementations for testing
├── agent_repository.py - Agent-specific data access methods
├── task_repository.py - Task-specific data access methods
└── __init__.py - Unified export interface
```

**Key Benefits**:
- **Type Safety**: Protocol-based interfaces with IDE autocomplete support
- **Testability**: Easy swap between database and in-memory implementations  
- **Separation of Concerns**: Business logic isolated from data access details
- **Consistency**: Standardized CRUD operations across all entity types
- **Performance**: Built-in caching and optimized database queries
- **Extensibility**: Support for multiple storage backends

**Usage Patterns**:
```python
# Repository Manager (Recommended)
repo_manager = RepositoryManager(db_path, event_manager)
agents = await repo_manager.agents.find_by_capability("web_search")

# Factory Pattern
agent_repo = RepositoryFactory.create_repository(EntityType.AGENT, db_path)

# In-Memory for Testing
test_repo = RepositoryFactory.create_repository(EntityType.AGENT, use_memory=True)
```

**Repository Interface**:
- Standard CRUD operations: `create()`, `get()`, `update()`, `delete()`, `list()`
- Search capabilities: `search()`, `count()`
- Entity-specific methods: `find_by_capability()`, `find_by_status()`, etc.
- Transaction support and automatic event logging

### Process Engine
**Location**: `agent_system/core/processes/`

Implements the process-first architecture:
- **Neutral Task Process**: Main entry point for all tasks
- **Tool-Triggered Processes**: Respond to specific tool calls
- **Process Discovery**: Establishes systematic frameworks
- **Framework Validation**: Ensures completeness
- **Isolation Verification**: Validates independent success capability

### Runtime Engine
**Location**: `agent_system/core/runtime/`

Manages task execution lifecycle:
```
Task States:
CREATED → READY_FOR_AGENT → AGENT_RESPONDING → 
WAITING_ON_DEPENDENCIES → COMPLETED/FAILED
```

Key features:
- Concurrent agent execution management
- Dependency graph resolution
- Manual stepping support for debugging
- Real-time state tracking via WebSocket
- Task timeout and depth limit enforcement

### Event System
**Location**: `agent_system/core/events/`

Comprehensive tracking and optimization system:
- Event types: entity, task, tool, system, optimization
- Hierarchical event chains for causality tracking
- Resource usage monitoring (tokens, time, memory)
- Batch processing for performance
- Automatic optimization trigger detection

### Knowledge System
**Location**: `agent_system/core/knowledge/`

MVP implementation for context assembly:
- File-based JSON storage (`knowledge/` directory)
- Context assembly engine for isolated task success
- Knowledge gap detection and reporting
- Usage tracking for effectiveness
- Bootstrap conversion from documentation

### API Layer
**Location**: `agent_system/api/`

**Modular FastAPI Architecture** (Refactored 2025-06-28):
```
api/
├── main.py (220 lines) - Core app, static serving, health checks
├── startup.py (155 lines) - Application lifecycle management
├── routes/ - Organized endpoint modules:
│   ├── tasks.py (287 lines) - Task management endpoints
│   ├── entities.py (243 lines) - Entity CRUD operations
│   └── admin.py (359 lines) - System administration endpoints
├── websocket/
│   └── handlers.py (159 lines) - Real-time communication
└── middleware/
    └── exception_handler.py - Centralized error processing
```

**Key Features**:
- **Router-Based Organization**: Clean separation by functional domain
- **Dependency Injection**: Shared resources (database, runtime, WebSocket manager)
- **Exception Handling Middleware**: Centralized error processing with custom exception types
- **CORS Configuration**: Cross-origin resource sharing for web clients
- **Request Validation**: Pydantic models for input validation
- **Real-time Communication**: WebSocket connections for live task updates
- **Lifecycle Management**: Proper startup/shutdown sequencing
- **Static Serving**: React web interface support

**Exception Types**:
- `EntityNotFoundError` → 404 responses
- `ValidationError` → 400 responses  
- `TaskExecutionError` → 422 responses
- `RuntimeError` → 503 responses
- `DatabaseError` → 503 responses
- `ConfigurationError` → 500 responses

### Tool Integration (MCP)
**Location**: `agent_system/tools/`

Model Context Protocol implementation:
```
MCPServerRegistry
├── Core Tools (always available)
│   ├── break_down_task
│   ├── create_subtask
│   ├── end_task
│   └── need_more_context/tools
├── System Tools (on request)
│   ├── entity_manager
│   ├── file_system
│   └── terminal
└── External Tools
    ├── github
    └── sql_lite
```

## Data Flow Architecture

### Task Submission Flow
```
User Request → API Endpoint → Neutral Task Process →
Process Discovery → Framework Establishment →
Agent Selection → Task Decomposition →
Isolated Execution → Result Assembly → User Response
```

### Agent Collaboration Flow
```
Parent Agent → Tool Call → Process Instance →
Create Subtask → Child Agent Assignment →
Context Inheritance → Isolated Execution →
Event Generation → Parent Notification
```

### Knowledge Assembly Flow
```
Task Analysis → Context Requirements →
Knowledge Query → Gap Detection →
Context Package Assembly → Agent Execution →
Usage Tracking → Effectiveness Measurement
```

## Technology Stack

### Backend Infrastructure
- **Python 3.11+**: Core runtime language
- **FastAPI 0.104.1**: Async web framework
- **SQLModel/SQLite**: Type-safe ORM with embedded database
- **Pydantic 2.5.0**: Data validation
- **AsyncIO**: Asynchronous execution throughout

### AI Model Integration
- **Google Gemini 2.0 Flash**: Default model (fast, efficient)
- **Anthropic Claude**: Alternative provider
- **OpenAI GPT**: Alternative provider
- **Flexible Provider System**: Easy to add new models

### Frontend Stack
- **React 18**: Modern UI framework
- **Socket.io**: Real-time WebSocket communication
- **React Markdown**: Documentation rendering
- **React Tree Graph**: Task visualization
- **Axios**: HTTP client

## Database Architecture

### Entity Tables
```sql
-- Master entity registry
CREATE TABLE entities (
    entity_id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    state TEXT DEFAULT 'active',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Entity relationships
CREATE TABLE entity_relationships (
    source_entity_id INTEGER,
    relationship_type TEXT,
    target_entity_id INTEGER,
    metadata JSON
);

-- Process tracking
CREATE TABLE process_instances (
    instance_id INTEGER PRIMARY KEY,
    process_entity_id INTEGER,
    initiating_entity_id INTEGER,
    state TEXT,
    parameters JSON,
    created_at TIMESTAMP
);
```

### Event Tracking
```sql
-- Comprehensive event log
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    event_type TEXT,
    entity_id INTEGER,
    parent_event_id INTEGER,
    timestamp TIMESTAMP,
    data JSON,
    resource_usage JSON
);

-- Optimization tracking
CREATE TABLE optimization_opportunities (
    opportunity_id INTEGER PRIMARY KEY,
    entity_id INTEGER,
    opportunity_type TEXT,
    confidence REAL,
    potential_impact TEXT
);
```

## Security Architecture

### Permission System
- Database-driven permission management
- Tool access controlled per agent
- Audit trail for all operations
- Request-based capability expansion

### API Security
- API key authentication for AI providers
- Rate limiting per endpoint
- Request validation with Pydantic
- **Centralized exception handling middleware** with security-conscious error responses
- Custom exception types with proper HTTP status code mapping
- Comprehensive error logging without sensitive data exposure

## Performance Optimizations

### Concurrency Management
- Configurable max concurrent agents (default: 3)
- Async/await throughout the stack
- Database connection pooling
- WebSocket connection management

### Caching Strategy
- Entity relationship caching
- Context document caching
- Tool definition caching
- AI response caching for similar queries

### Monitoring & Metrics
- Request/response timing
- Token usage tracking
- Memory usage monitoring
- Error rate tracking
- Optimization opportunity detection

## Deployment Architecture

### Service Management
- SystemD service definitions
- Docker containerization support
- Health check endpoints
- Graceful shutdown handling

### Configuration Management
- Environment-based configuration
- Runtime configuration updates
- Feature flags for gradual rollout
- A/B testing support

## Future Architecture Considerations

### Scalability Path
1. **Distributed Execution**: Multiple runtime instances
2. **Message Queue**: Task distribution via queue
3. **Graph Database**: Neo4j for complex relationships
4. **Microservices**: Split into specialized services

### Enhancement Opportunities
1. **Federated Learning**: Cross-deployment optimization
2. **Plugin Architecture**: Third-party agent/tool support
3. **Multi-tenancy**: Isolated execution contexts
4. **Real-time Collaboration**: Multiple users per task

The architecture is designed to be self-improving, with every execution potentially leading to better processes, more effective agents, and accumulated domain expertise through the process-first approach.