# Project Context & AI Agent Guide

*Last updated: 2025-06-28 | Updated by: /document command*

## Recent Updates
- **2025-06-28**: Major refactoring work COMMITTED - successfully committed comprehensive architectural improvements (95 files changed, 14,489 insertions) including API modularization, entity management decomposition, repository pattern, type safety, and complete documentation. **Critical follow-up**: Fix 175 absolute imports across 63 files blocking system initialization
- **2025-06-28**: Naming convention standardization completed - eliminated redundant file naming patterns (agent_entity.py → agent.py, registry.py → process_registry.py) and updated all import statements for improved code clarity and maintainability
- **2025-06-28**: Repository pattern implementation completed - created comprehensive data access abstraction with type-safe interfaces, in-memory testing implementations, factory pattern, and repository manager for improved testability and separation of concerns
- **2025-06-28**: Module-level CLAUDE.md documentation completed - created comprehensive AI agent guidance files for all 5 major system modules (core, tools, api, processes, database) with detailed patterns, examples, and cross-references to enhance development velocity
- **2025-06-28**: Comprehensive type hints implementation - added return type annotations to 30+ core functions, created TypedDict library with 15+ type definitions, and established type safety foundation for enhanced IDE support and code clarity
- **2025-06-28**: EntityManager decomposition completed - decomposed 676-line monolithic EntityManager into modular type-specific managers with facade pattern for backward compatibility and enhanced maintainability
- **2025-06-28**: Major seeding system refactoring - extracted hardcoded configuration into YAML-driven architecture with 87% line reduction (1,228 → 161 lines) and modular seeder classes
- **2025-06-28**: Completed major API refactoring - decomposed monolithic 1,155-line main.py into modular FastAPI architecture with 81% line reduction and clear separation of concerns
- **2025-06-28**: Implemented centralized exception handling middleware - eliminated duplicate error handling patterns and established consistent API error responses
- **2025-06-28**: Fixed critical P0 import dependencies - migrated from legacy models.py to entity-based architecture across 25+ files

## 🎯 Project Overview

### Core Purpose
The System is a **process-first recursive agent system** that transforms undefined problems into systematic domains with established frameworks. It ensures every complex task has proper systematic structure before execution, enabling isolated subtask success through comprehensive context.

**Target Users**: AI developers, researchers, and teams building advanced AI orchestration systems
**Business Value**: Eliminates ad-hoc problem solving by establishing systematic frameworks that enable predictable, scalable AI task execution
**Current Status**: Production-ready foundation with 9 specialized agents, complete knowledge system, and web interface. **Major refactoring completed and committed** - comprehensive architectural improvements preserved in git history. **CRITICAL**: 175 absolute imports across 63 files need conversion to relative imports for system initialization.

### Key Success Metrics
- Process framework establishment before all task execution
- 100% isolated subtask success rate with proper context
- Continuous self-improvement through systematic learning
- Zero ad-hoc solutions - all work within established frameworks

## 🏗️ Architecture & Technical Stack

### Quick Overview
**Technology**: Python 3.11+ with FastAPI backend, React 18 frontend
**Architecture**: Process-first entity-based architecture with 6 core entity types
**Database**: SQLite with SQLModel ORM for entity management

📖 **See detailed architecture**: [`/docs/architecture/overview.md`](./docs/architecture/overview.md)
📖 **See data models**: [`/docs/architecture/data-models.md`](./docs/architecture/data-models.md)

## 🔧 Development Patterns & Conventions

### Key Principles
- **Process-First**: Establish systematic frameworks before any execution
- **Isolated Success**: Every subtask must succeed independently with proper context
- **Entity-Based**: All behavior driven by 6 fundamental entity types
- **Repository Pattern**: Clean data access abstraction with type safety and testability
- **Self-Improving**: Continuous optimization through event tracking

📖 **See coding conventions**: [`/docs/development/conventions.md`](./docs/development/conventions.md)
📖 **See development workflow**: [`/docs/development/workflow.md`](./docs/development/workflow.md)

## 🚀 Core Features & User Journeys

### Primary User Flows
1. **System Initialization**: Bootstrap process establishes core agents, tools, and knowledge base
2. **Task Submission**: Process discovery → Framework establishment → Systematic decomposition → Isolated execution
3. **Manual Step Mode**: Interactive debugging with approval at each agent action

### Feature Modules
- **Process Discovery**: `agent_system/core/processes/` - Framework establishment engine
- **Universal Runtime**: `agent_system/core/universal_agent_runtime.py` - Agent execution within boundaries
- **Knowledge System**: `agent_system/core/knowledge/` - Context assembly and gap detection
- **Event System**: `agent_system/core/events/` - Comprehensive tracking for optimization
- **Web Interface**: `agent_system/web/` - Real-time task monitoring and control

### Data Models & Entities
- **Processes**: Primary organizing principle for systematic frameworks
- **Agents**: 9 specialized agents executing within process boundaries
- **Tasks**: Work units designed for isolated success
- **Tools**: MCP-based capabilities with permission management
- **Documents**: Systematic context and knowledge
- **Events**: Enable process optimization through tracking

## 🔌 Integrations & External Dependencies

### APIs & Services
- **Google Gemini 2.0 Flash**: Default AI model (fast, efficient)
- **Anthropic Claude**: Alternative AI provider
- **OpenAI GPT**: Alternative AI provider
- **MCP Protocol**: Tool integration framework

### Third-Party Libraries
- **FastAPI 0.104.1**: Async web framework with WebSocket support
- **SQLModel 0.0.14**: Type-safe database ORM
- **MCP SDK 1.0.0+**: Model Context Protocol for tool integration
- **Pydantic 2.5.0**: Data validation and settings management
- **PyYAML 6.0.1**: YAML parsing for configuration-driven seeding

### Type Safety Framework
- **Comprehensive TypedDict Library**: `core/types.py` with 15+ type definitions for tasks, agents, events, tools, and API responses
- **Return Type Annotations**: All core functions have proper type hints for enhanced IDE support
- **Type Consistency**: Standardized typing imports and patterns across modules

## 🛠️ Development Workflow

### Getting Started
- **Setup steps**: 
  1. Clone repository
  2. Install Python 3.11+
  3. `pip install -r requirements.txt`
  4. Set API keys in `.env`
  5. `python api/main.py`
- **Required tools**: Python 3.11+, Node.js 18+ (for web UI)
- **Common commands**:
  - `python api/main.py` - Start API server
  - `python scripts/seed_system.py` - Initialize with all agents
  - `python scripts/bootstrap_knowledge.py` - Convert docs to knowledge
  - `./svc start/stop/status` - Service management

### Development Practices
- **Branch strategy**: Feature branches → main branch
- **Code review process**: Process-first validation, isolated success verification
- **Testing approach**: Integration tests for process frameworks
- **Debugging approaches**: Manual step mode, comprehensive event logs

## ⚠️ Important Constraints & Gotchas

### Technical Constraints
- **Performance requirements**: Max 3 concurrent agents by default (configurable)
- **Security requirements**: Database-driven permissions, audit trails
- **AI Model limits**: Rate limiting and token constraints per provider

### Development Gotchas
- **Process-first requirement**: Never execute tasks without framework establishment
- **Entity relationships**: All behavior must map to the 6 entity types
- **Tool permissions**: Agents must request tools through proper channels
- **Knowledge gaps**: System will halt if context is insufficient

## 📍 Where to Find Things

### Key Files & Locations
- **Configuration**: 
  - `.env` for API keys, `agent_system/core/config.py` for settings
  - `agent_system/config/seeds/` for system seeding configuration (YAML-driven)
- **Business logic**: `agent_system/core/processes/` for framework establishment
- **API definitions**: 
  - `agent_system/api/main.py` - Core app and static serving (220 lines)
  - `agent_system/api/routes/` - Modular endpoint organization:
    - `tasks.py` - Task management endpoints
    - `entities.py` - Entity CRUD operations  
    - `admin.py` - System administration endpoints
  - `agent_system/api/startup.py` - Application lifecycle management
  - `agent_system/api/websocket/handlers.py` - Real-time communication
- **Exception handling**: `agent_system/api/exceptions.py` for custom exceptions, `agent_system/api/middleware/` for middleware
- **Entity management**: 
  - `agent_system/core/entities/entity_manager.py` - Main facade for entity operations
  - `agent_system/core/entities/managers/` - Type-specific entity managers
  - `agent_system/core/entities/` - Entity model definitions
- **Repository pattern**: 
  - `agent_system/core/repositories/` - Data access abstraction layer with type-safe interfaces
  - `agent_system/core/repositories/repository_factory.py` - Factory for repository creation
  - `agent_system/core/repositories/memory_repository.py` - In-memory implementations for testing
  - `agent_system/examples/repository_pattern_demo.py` - Usage patterns and demonstrations
- **Type definitions**: `agent_system/core/types.py` - Comprehensive TypedDict library for type safety
- **System seeding**: 
  - `agent_system/scripts/seed_system.py` - Configuration-driven seeding (161 lines)
  - `agent_system/scripts/seeders/` - Modular seeder classes
- **Tool implementations**: `agent_system/tools/` (core_mcp, system_tools)

### Documentation Locations
- **API docs**: http://localhost:8000/docs (auto-generated)
- **Architecture decisions**: `/docs/architecture/`
- **Process specifications**: `agent_system/context_documents/processes/`
- **Agent instructions**: `agent_system/context_documents/agents/`

## 🎯 Current Priorities & Roadmap

### Active Development
The process-first foundation is complete with **ALL MAJOR REFACTORING WORK COMMITTED** (2025-06-28). Comprehensive architectural improvements include API modularization (81% line reduction), entity management decomposition, repository pattern implementation, type safety foundation, configuration-driven seeding (87% reduction), centralized exception handling, and complete CLAUDE.md documentation. **IMMEDIATE PRIORITY**: Fix 175 absolute imports blocking system initialization, then leverage system for real-world tasks.

📖 **See refactoring plan**: [`/docs/planning/REFACTORING_PLAN.md`](./docs/planning/REFACTORING_PLAN.md)
📖 **See implementation plan**: [`/docs/planning/IMPLEMENTATION_PLAN.md`](./docs/planning/IMPLEMENTATION_PLAN.md)

### Next Steps
- **Knowledge Graph Migration**: Evolve from file-based to graph database
- **Pattern Recognition Engine**: Extract successful patterns automatically
- **Framework Effectiveness Tracking**: Monitor and optimize process frameworks
- **Automated Gap Resolution**: System identifies and fills knowledge gaps

## 💡 AI Agent Guidelines

### Essential Workflow
1. Read this PROJECT_CONTEXT.md first
2. Check relevant `/docs/` modules for detailed information
3. Follow process-first principles - establish frameworks before execution
4. Update documentation after significant changes

### Quick Reference
- **Most modified files**: Task implementations, knowledge entities, process frameworks
- **Key directories**: 
  - `agent_system/core/` - Core system logic
  - `agent_system/context_documents/` - Agent/process definitions
  - `knowledge/` - Structured knowledge entities
- **Common tasks**:
  - Submit task: `POST /tasks` with instruction
  - Check status: `GET /tasks/tree/{tree_id}`
  - Add knowledge: Create JSON in `knowledge/` directory
  - Update agent: Edit in `context_documents/agents/`