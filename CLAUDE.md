# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Philosophy: Process-First Architecture for Systematic Self-Improvement

This is a **process-first recursive agent system** where systematic structure establishment precedes all task execution. The system transforms undefined problems into systematic domains with rules, regulations, and isolated puzzle pieces that can be solved independently with proper context.

## Core Principle: Process-First, Never Task-First

The system operates on the principle that **every task requires systematic structural analysis before execution**:

1. **Process Discovery First**: Every incoming task triggers comprehensive process framework analysis
2. **Structure Establishment**: Missing processes, rules, and systematic frameworks are created before task breakdown
3. **Isolated Task Success**: All subtasks become puzzle pieces that succeed independently within established frameworks
4. **No Ad-Hoc Solutions**: Elimination of improvised approaches in favor of systematic process-driven execution

The foundation has been **fully implemented** and includes:

1. Universal Agent Runtime (executes tasks within systematic frameworks)
2. Complete Agent Suite (9 specialized agents including process_discovery)
3. Process-First Architecture (systematic framework establishment before execution)
4. Comprehensive Database Schema (agents, tasks, processes, tools, documents, events)
5. Core MCP Toolkit (6 essential tools for systematic execution)
6. Advanced Toolset (internal + external integrations with process boundaries)
7. Web Interface + API (real-time updates, process visualization)

**All development must follow process-first principles - establish systematic frameworks before execution.**

## Process-First Foundation Components (FULLY IMPLEMENTED)

### 1. Process-First Universal Agent Runtime
- Single agent class that executes tasks within systematic frameworks
- Process discovery and establishment before execution
- AI model integration with framework boundaries
- Tool execution within process-defined limits
- Systematic message logging for process optimization

### 2. Complete Process-First Agent Suite (9 Agents)
All agents operate with process-first principles:
- `process_discovery` - **PRIMARY AGENT** - Establishes systematic frameworks before execution
- `agent_selector` - Framework-aware task routing and agent selection
- `planning_agent` - Process-driven task decomposition for isolated success
- `context_addition` - Framework-appropriate knowledge management
- `tool_addition` - Process-compliant capability expansion
- `task_evaluator` - Framework-aware quality assessment
- `documentation_agent` - Systematic process documentation
- `summary_agent` - Process-contextualized synthesis
- `review_agent` - Systematic framework optimization

### 3. Full Database Schema
```sql
-- Complete schema implemented:
CREATE TABLE agents (id, name, instruction, context_documents, available_tools, permissions, constraints);
CREATE TABLE tasks (id, parent_task_id, tree_id, agent_id, instruction, status, result, metadata);
CREATE TABLE messages (id, task_id, message_type, content, metadata, timestamp);
CREATE TABLE context_documents (id, name, title, category, content, format, version);
CREATE TABLE tools (id, name, description, category, implementation, parameters, permissions);
```

### 4. Core MCP Toolkit (6 Tools)
1. `break_down_task()` - Recursive decomposition
2. `start_subtask()` - Agent spawning
3. `request_context()` - Knowledge expansion
4. `request_tools()` - Capability discovery
5. `end_task()` - Task completion
6. `flag_for_review()` - Human oversight

### 5. Advanced Toolset
- **Internal Tools**: `list_agents`, `list_documents`, `list_optional_tools`, `query_database`
- **External Integrations**: GitHub MCP server, shell command MCP
- **System Tools**: Terminal access, git operations
- **Optional Tools**: `send_message_to_user` (agents can request for user communication)

### 6. Full Context Documentation
Complete knowledge base including:
- System architecture and principles
- Process guidelines and best practices
- Agent registry and capabilities
- Tool documentation and MCP integration guides
- Quality standards and evaluation criteria
- Monitoring guidelines and system limits
- Improvement procedures and safety mechanisms

### 7. Web Interface + API
- Task submission with real-time status updates
- Task tree visualization with WebSocket integration
- Complete FastAPI server with full documentation
- React frontend with modern UI components

### 8. MVP Knowledge System (NEW)
- **File-Based Knowledge Storage**: JSON entities organized by type (domains, processes, agents, tools, patterns, system)
- **Context Assembly Engine**: Assembles complete context packages for isolated task success
- **Knowledge Gap Detection**: Identifies missing knowledge preventing task completion
- **Bootstrap Conversion**: Converts existing documentation to structured knowledge entities
- **Usage-Driven Evolution**: Knowledge effectiveness tracked and improved through usage
- **Simple Migration Path**: Designed to evolve into graph database when needed

## Process-First Development Approach

When working with this system, ALWAYS follow the process-first approach:

1. **Never Start with Task Execution** - Always verify systematic frameworks exist first
2. **Request Process Establishment** - If frameworks are missing, create them before proceeding
3. **Work Within Frameworks** - All execution must happen within established systematic boundaries
4. **Enable Isolated Success** - Ensure every subtask can succeed independently with proper context

## What to Build Next with Process-First Architecture

With the process-first foundation and knowledge system in place, submit tasks that leverage systematic frameworks:

1. **Knowledge-Driven Development** - Use knowledge system to provide complete context for all tasks
2. **Systematic Framework Library** - Build comprehensive process frameworks through task execution
3. **Knowledge Evolution Pipeline** - Automatically create knowledge from successful executions
4. **Context Completeness Validation** - Ensure all tasks have sufficient context for isolated success
5. **Knowledge Graph Migration** - Evolve from file-based to graph database when complexity requires
6. **Pattern Recognition Engine** - Extract successful patterns into reusable knowledge entities
7. **Automated Gap Resolution** - System identifies and fills its own knowledge gaps
8. **Framework Effectiveness Tracking** - Monitor and optimize process frameworks through usage

## Current System Status

**Process-First Foundation Deployed:**
- ✅ Process-first universal agent runtime
- ✅ Process discovery agent for systematic framework establishment
- ✅ All 9 specialized agents with process-first principles
- ✅ Systematic neutral task process with framework validation
- ✅ Domain analysis and framework establishment processes
- ✅ Complete entity-based architecture (6 entity types)
- ✅ Process-driven MCP toolkit and integrations
- ✅ Web interface with process visualization
- ✅ Systematic initialization with framework checks
- ✅ MVP Knowledge System for context assembly and gap detection

**System Ready For Process-First Development:**
The process-first foundation is operational. Every task now goes through systematic framework establishment before execution, ensuring isolated subtask success and comprehensive domain coverage.

## Key Implementation Guidelines

### Process-First Development
The system operates on systematic framework establishment. When building capabilities:
- ALWAYS establish process frameworks before execution
- Verify systematic structure completeness
- Ensure isolated subtask success capability
- Work within established process boundaries
- Never use ad-hoc approaches

### Entity-Based Process Architecture
All behavior driven by 6 entity types:
- **Processes** - Primary organizing principle for systematic frameworks
- **Agents** - Execute within process boundaries
- **Tasks** - Work units that succeed in isolation
- **Tools** - Capabilities within process limits
- **Documents** - Systematic context and knowledge
- **Events** - Enable process optimization

### Process-First Agent Collaboration
The 9 agents collaborate systematically:
1. `process_discovery` establishes frameworks (ALWAYS FIRST)
2. `agent_selector` routes within frameworks
3. `planning_agent` decomposes using process patterns
4. Specialist agents execute within boundaries
5. `task_evaluator` validates framework compliance
6. `documentation_agent` captures systematic patterns
7. `review_agent` optimizes frameworks

## Process-First Development Workflow

1. **Submit task** → Process discovery analyzes domain requirements
2. **Knowledge assembly** → Context engine provides complete knowledge for task
3. **Framework establishment** → Missing systematic structures created
4. **Systematic breakdown** → Tasks decomposed using process patterns
5. **Isolated execution** → Subtasks succeed independently with full context
6. **Knowledge evolution** → New patterns captured as knowledge entities
7. **Process optimization** → Frameworks improve through usage analysis

## Architecture Highlights

- **Process-First Foundation**: Systematic framework establishment before execution
- **9 Specialized Agents**: Including primary process_discovery agent
- **Entity-Based Design**: 6 fundamental entity types supporting systematic operation
- **Isolated Task Success**: Every subtask succeeds independently within frameworks
- **Systematic Documentation**: Comprehensive process patterns and frameworks
- **Framework-Driven Tools**: All capabilities operate within process boundaries
- **Self-Optimizing**: Continuous framework improvement through usage analysis

## Success Criteria

The process-first foundation is operational when:
1. ✅ Process discovery establishes frameworks before all execution
2. ✅ Complex domains transformed into systematic frameworks
3. ✅ Tasks decomposed for isolated success within boundaries
4. ✅ Agents collaborate within established process frameworks
5. ✅ System continuously optimizes systematic approaches
6. ✅ Framework compliance maintained and validated
7. ✅ All operations generate learning for process improvement

**The process-first foundation transforms "how to solve" into "what framework enables systematic success"!**

## Knowledge System Usage

### Bootstrap Knowledge Base
```bash
# Convert existing documentation to knowledge entities
python scripts/bootstrap_knowledge.py
```

### Using Knowledge in Development
When implementing new features:
1. **Check Knowledge Gaps**: System identifies what knowledge is missing
2. **Assemble Context**: Context engine provides complete knowledge packages
3. **Validate Completeness**: Ensure context enables isolated task success
4. **Track Usage**: System learns from knowledge effectiveness
5. **Evolve Knowledge**: Successful patterns become new knowledge entities

### Knowledge System Architecture
- **Storage**: `knowledge/` directory with JSON entities
- **Engine**: `core/knowledge/` module for context assembly
- **Tracking**: Database tables for usage, gaps, and evolution
- **Bootstrap**: Converts docs → structured knowledge on first run

The knowledge system ensures every task has the context needed for isolated success!

## Module-Specific Documentation

For detailed module documentation, see the CLAUDE.md files in each major directory:

- **[Core System Logic](./agent_system/core/CLAUDE.md)**: Entity management, agent runtime, processes, knowledge system
- **[Tool Ecosystem](./agent_system/tools/CLAUDE.md)**: MCP tools, system tools, external integrations
- **[Web API Interface](./agent_system/api/CLAUDE.md)**: REST endpoints, WebSocket communication, middleware
- **[Process Framework](./agent_system/core/processes/CLAUDE.md)**: Process-first architecture, domain analysis, framework establishment
- **[Database Layer](./agent_system/database/CLAUDE.md)**: Entity persistence, migrations, relationships, performance