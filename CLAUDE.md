# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Philosophy: Complete Foundation for Self-Improvement

This is a **self-improving recursive agent system** with a **complete foundation** as specified in the launch plan. The system includes all 8 core agents, full context documentation, and comprehensive tooling to enable unlimited self-improvement.

## Core Principle: Complete Foundation, Unlimited Growth

The foundation has been **fully implemented** and includes:

1. Universal Agent Runtime (executes any task configuration)
2. Complete Agent Suite (8 specialized agents with detailed instructions)
3. Full Context Documentation (system docs + process guides) 
4. Comprehensive Database Schema (agents, tasks, messages, context, tools)
5. Core MCP Toolkit (6 essential tools for recursion)
6. Advanced Toolset (internal + external integrations)
7. Web Interface + API (real-time updates, task visualization)

**Agents now build advanced capabilities on top of this complete foundation.**

## Complete Foundation Components (FULLY IMPLEMENTED)

### 1. Universal Agent Runtime
- Single agent class that executes any task configuration
- AI model integration (Anthropic/OpenAI)  
- Tool execution and message logging
- Permission and constraint enforcement

### 2. Complete Agent Suite (8 Agents)
All agents implemented with detailed instructions:
- `agent_selector` - Task routing and agent selection
- `task_breakdown` - Complex problem decomposition
- `context_addition` - Knowledge and context management
- `tool_addition` - Capability expansion and tool development
- `task_evaluator` - Quality assessment and validation
- `documentation_agent` - System documentation and knowledge capture
- `summary_agent` - Information synthesis and reporting
- `review_agent` - System improvement and optimization

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

## What Agents Should Build Next

With the complete foundation in place, submit these **advanced** tasks:

1. **Performance Analytics Dashboard** - Real-time monitoring and optimization insights
2. **Advanced Testing Framework** - Automated quality gates and regression testing
3. **Machine Learning Integration** - Pattern recognition and predictive capabilities
4. **Advanced UI Components** - Sophisticated visualization and interaction tools
5. **Security Monitoring** - Advanced safety and threat detection systems
6. **Deployment Automation** - CI/CD pipelines and infrastructure management
7. **Self-Healing Mechanisms** - Advanced error recovery and system resilience
8. **External Service Integration** - APIs, databases, and third-party tools

## Current System Status

**Complete Foundation Deployed:**
- ✅ Universal agent runtime with all capabilities
- ✅ All 8 specialized agents with detailed instructions
- ✅ Full context documentation and knowledge base
- ✅ Comprehensive database schema and models
- ✅ Complete MCP toolkit and integrations
- ✅ Advanced internal and external tools
- ✅ Web interface with real-time updates
- ✅ System initialization and health checks

**System Ready For Advanced Tasks:**
The foundation is complete and operational. All basic capabilities exist. The system can now tackle sophisticated, advanced challenges that build upon this foundation.

## Key Implementation Guidelines

### Foundation-Based Development
The system now has a complete foundation. When agents build new capabilities:
- Build on existing agents and tools
- Leverage the full context documentation
- Use existing quality standards and processes
- Integrate with the comprehensive monitoring system

### Database-Driven Architecture
All behavior comes from the database:
- Agents can create new agent types
- Tools can be dynamically added
- Context can be expanded
- Quality standards can evolve

### Collaborative Agent Ecosystem
The 8 agents work together:
1. `agent_selector` routes tasks to specialists
2. `task_breakdown` decomposes complex problems
3. Specialist agents handle specific domains
4. `task_evaluator` ensures quality
5. `documentation_agent` captures knowledge
6. `summary_agent` synthesizes results
7. `review_agent` implements improvements

## Development Workflow

1. **Submit advanced tasks** to leverage the complete foundation
2. **Agents collaborate** using established patterns and tools
3. **System improves** through the review_agent and established processes
4. **Knowledge accumulates** in the comprehensive documentation system
5. **Capabilities expand** while maintaining quality and safety standards

## Architecture Highlights

- **Complete Foundation**: All 8 agents with specialized capabilities
- **Universal Agent Design**: One runtime, infinite configurations
- **Full Documentation**: Comprehensive knowledge base and processes
- **Advanced Tooling**: Internal and external integrations
- **Quality Systems**: Evaluation, monitoring, and improvement processes
- **Database-Driven**: Everything configurable, nothing hardcoded
- **Self-Improving**: Continuous enhancement through agent collaboration

## Success Criteria

The complete foundation is operational when:
1. ✅ All 8 agents are accessible and functional
2. ✅ Complex tasks are automatically decomposed and distributed
3. ✅ Agents collaborate effectively using the MCP toolkit
4. ✅ Context and knowledge are accumulated and shared
5. ✅ System continuously improves through established processes
6. ✅ Quality standards are maintained and evolved
7. ✅ All interactions are logged, monitored, and learned from

**The complete foundation is ready - submit advanced tasks and watch unlimited growth!**