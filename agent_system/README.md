# Self-Improving Agent System - Entity-Based Architecture

A **recursive agent system** with entity-based architecture that continuously evolves through automated self-improvement.

## 🎯 Core Philosophy: Entity-Driven, Event-Sourced, Self-Improving

This system has been fully migrated to an advanced entity-based architecture:

1. **Entity Framework** - Unified polymorphic entity system
2. **Event-Driven Architecture** - Comprehensive tracking and analysis
3. **Process Framework** - Hybrid Python/LLM execution engine
4. **Runtime Engine** - State machine with automatic progression
5. **MCP Tool System** - Dynamic permission-based capabilities
6. **13 Specialized Agents** - Original 8 + 5 new Phase 6 agents
7. **Self-Improvement Engine** - Automated optimization with safety
8. **Web Interface + API** - Real-time monitoring and control

**Migration Complete: The system now features unlimited self-improvement capabilities.**

## 🎉 Migration Complete!

The 8-phase migration from agent-based to entity-based architecture is now complete:

- ✅ **Phase 1**: Database Foundation
- ✅ **Phase 2**: Event System Implementation 
- ✅ **Phase 3**: Entity Management Layer
- ✅ **Phase 4**: Process Framework & Runtime Engine
- ✅ **Phase 5**: Optional Tooling System (MCP)
- ✅ **Phase 6**: New Agent Integration (5 agents)
- ✅ **Phase 7**: Self-Improvement Activation
- ✅ **Phase 8**: Legacy Cleanup

See the [Migration Completion Guide](../docs/migration_completion_guide.md) for details.

## 🆕 Architecture Highlights

- **Entity-Based**: Everything is an entity with polymorphic behavior
- **Event-Sourced**: Complete audit trail and pattern analysis
- **Process-Driven**: Deterministic workflows with strategic AI
- **Self-Improving**: Automatic optimization with safety mechanisms
- **Permission-Based**: Dynamic tool access and security
- **Real-time Monitoring**: WebSocket updates and dashboards

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- API key for Google Gemini 2.5 series (default), Anthropic Claude, or OpenAI GPT
- Node.js (for React frontend)

### 1. Setup
```bash
cd agent_system

# Backend setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd web
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY (or ANTHROPIC_API_KEY/OPENAI_API_KEY)
```

### 2. Initialize Complete System
```bash
python scripts/seed_system.py
```

### 3. Start the System
```bash
# Quick start with service manager
./svc start  # Starts both backend and frontend

# Or manually in separate terminals:
# Terminal 1: Start backend
python -m api.main

# Terminal 2: Start frontend (optional)
cd web && npm start

# Check service status
./svc status

# View logs
./svc logs
```

### 4. Submit Tasks
- **Web**: http://localhost:3000
  - **Tasks Tab**: Submit and monitor tasks
  - **Agents Tab**: Browse and edit agent configurations
  - **Tools Tab**: Explore available tools and parameters
  - **Documents Tab**: View and edit context documents
- **API**: http://localhost:8000/docs

## 🤖 What You Get (Complete Foundation)

### Universal Agent Runtime
- Single agent class that can execute any task configuration
- AI model integration (Anthropic/OpenAI)
- Tool execution and message logging
- Permission and constraint enforcement

### Core MCP Tools
1. `break_down_task()` - Recursive problem decomposition
2. `start_subtask()` - Spawn specialized agents
3. `request_context()` - Knowledge expansion
4. `request_tools()` - Capability discovery
5. `end_task()` - Task completion
6. `flag_for_review()` - Human oversight

### Complete Agent Suite (8 Agents)
- **agent_selector** - Task routing and agent selection
- **task_breakdown** - Complex problem decomposition
- **context_addition** - Knowledge and context management
- **tool_addition** - Capability expansion and tool development
- **task_evaluator** - Quality assessment and validation
- **documentation_agent** - System documentation and knowledge capture
- **summary_agent** - Information synthesis and reporting
- **review_agent** - System improvement and optimization

### Full Context Documentation
- System architecture and principles
- Process guidelines and best practices
- Agent registry and capabilities
- Tool documentation and MCP integration guides
- Quality standards and evaluation criteria

### Comprehensive Database
```sql
-- Complete schema:
agents (id, name, instruction, context_documents, available_tools, permissions)
tasks (id, parent_task_id, tree_id, agent_id, instruction, status, metadata)
messages (id, task_id, message_type, content, metadata)
context_documents (id, name, title, category, content, format, version)
tools (id, name, description, category, implementation, parameters, permissions)
```

### Advanced Toolset
- **Internal Tools**: list_agents, list_documents, list_optional_tools, query_database
- **External Integrations**: GitHub MCP server, shell command MCP
- **System Tools**: Terminal access, git operations
- **Optional Tools**: send_message_to_user (for agent-user communication)

### Web Interface
- Task submission form with real-time status updates
- Task tree visualization with thread-based UI
- Agent Browser - View and edit agent configurations
- Tool Browser - Explore available tools and parameters
- Document Browser - View and edit context documents
- WebSocket integration for live updates
- Step mode debugging with pause/continue functionality

## 🔄 Self-Modification System

The system includes comprehensive self-improvement capabilities with proper safety measures:

### Available Scripts
- **`scripts/self_modify.py`** - Complete self-modification workflow with branch management
- **`scripts/test_system.py`** - Comprehensive system testing (health, functional, performance)
- **`scripts/backup_system.py`** - Full system backup and restore capabilities
- **`scripts/monitor_health.py`** - Real-time health monitoring and alerting

### Self-Modification Workflow
```bash
# Complete self-improvement with safety checks
python scripts/self_modify.py --task-description "Implement new feature X"

# Run comprehensive tests after changes
python scripts/test_system.py

# Create system backup before major changes
python scripts/backup_system.py backup --description "Before major update"

# Monitor system health during changes
python scripts/monitor_health.py --duration 300
```

### Safety Features
- **Branch Isolation**: All changes made in separate git branches
- **Automatic Backups**: Current state preserved before any modifications
- **Comprehensive Testing**: Health, functional, performance, and integration tests
- **Real-time Monitoring**: Continuous health checks during modifications
- **Rollback Capability**: Automatic emergency rollback on failures
- **User Communication**: Agents can request approval for major changes

See `docs/self_improvement_guide.md` for complete procedures.

## 🛠️ What Agents Should Build Next

With the complete foundation in place, submit these advanced tasks:

```
Build advanced performance monitoring and analytics dashboard

Create sophisticated testing frameworks with automated quality gates

Implement advanced UI components for complex task visualization

Develop machine learning capabilities for pattern recognition

Build advanced security and safety monitoring systems

Create deployment automation and CI/CD pipelines

Implement advanced error recovery and self-healing mechanisms

Develop integration with external services and APIs
```

## 🔧 Example Advanced Tasks

### Performance Analytics
```
"Build a comprehensive performance monitoring system that tracks agent execution times, resource usage, success rates, and identifies optimization opportunities across the entire system."
```

### Advanced Testing Framework
```
"Create an advanced testing framework that can automatically generate test cases, perform regression testing, and validate system changes before deployment."
```

### Machine Learning Integration
```
"Implement machine learning capabilities that can learn from task patterns, predict optimal agent selection, and improve system performance over time."
```

## 🏗️ System Architecture

### Complete System Flow
1. User submits task → agent_selector
2. Agent_selector analyzes task and selects appropriate specialist agent
3. If complex → routes to task_breakdown for decomposition
4. Specialized agents (context_addition, tool_addition, etc.) handle specific needs
5. Task_evaluator validates results, documentation_agent captures knowledge
6. Summary_agent synthesizes results for parent tasks
7. Supervisor monitors system health, review_agent implements improvements
8. All interactions logged and learned from

### Self-Improvement Loop
1. Agent identifies missing capability
2. Uses `request_tools()` to get it built
3. System becomes more capable
4. Process repeats recursively

### Safety Limits
- Max recursion depth: 10
- Task timeout: 5 minutes  
- Concurrency limit: 3 agents
- Memory limit: 512MB per agent

## 📊 Success Metrics

The complete foundation is working when:
- ✅ You can submit tasks via API/web
- ✅ All 9 agents are operational and accessible
- ✅ Complex tasks are automatically decomposed and distributed
- ✅ Agents collaborate effectively through the MCP toolkit
- ✅ Context and knowledge are accumulated and shared
- ✅ System continuously improves through review_agent
- ✅ All interactions are logged and monitored

## 🔮 Vision

This complete foundation enables advanced self-improving capabilities where:
- Agents build sophisticated problem-solving capabilities
- The system evolves faster than manual development
- Human role shifts from coding to task direction
- Complex problems get solved through recursive decomposition

## 📝 Development Notes

### Foundation Complete - What's Built
- ✅ Complete agent suite (9 specialized agents)
- ✅ Full context documentation and knowledge base
- ✅ Comprehensive MCP toolkit and integrations
- ✅ Database-driven architecture with all schemas
- ✅ Web interface with real-time updates
- ✅ Git integration and system tools
- ✅ Quality standards and evaluation frameworks

### Core Files
- `core/universal_agent.py` - Universal agent runtime
- `core/task_manager.py` - Task queue and execution engine
- `tools/core_mcp/core_tools.py` - 7 essential MCP tools
- `tools/system_tools/internal_tools.py` - Internal system tools
- `scripts/seed_system.py` - Complete system seeding
- `scripts/self_modify.py` - Self-modification workflow with safety checks
- `scripts/test_system.py` - Comprehensive system testing framework
- `scripts/backup_system.py` - System backup and restore utilities
- `scripts/monitor_health.py` - Real-time health monitoring
- `api/main.py` - Full-featured FastAPI server
- `web/src/App.js` - React frontend with WebSocket integration

### Key Principles
- **Universal Agent Design**: One agent class, infinite configurations
- **Database-Driven**: All behavior comes from database, not code
- **Recursive Self-Improvement**: System builds missing capabilities
- **Transparent**: All reasoning and actions logged
- **Complete Foundation**: Full seed set enables unlimited growth

## 🎉 Ready to Start

The complete foundation is ready. Now submit advanced tasks and watch the system evolve!

```bash
# Initialize and start
python scripts/seed_system.py
python -m api.main

# Submit advanced tasks at http://localhost:8000/app
# Example: "Build a comprehensive performance monitoring dashboard with real-time analytics"
```

**The agents will build advanced capabilities on top of the complete foundation through recursive self-improvement.**