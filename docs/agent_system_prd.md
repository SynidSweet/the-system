# Self-Improving Agent System - Minimal MVP PRD

## Core Concept

A single, universal agent runtime that executes tasks by recursively spawning specialized instances of itself. All agents share the same core instruction set and MCP toolkit, but receive different task-specific instructions, context documents, and available tools from a SQLite database.

## System Architecture

### Universal Agent Runtime
Every agent instance has identical structure:
- **AI Model**: Configurable (e.g., Claude, GPT-4)
- **Core Instruction**: Universal system instruction (same for all agents)
- **Task Instruction**: Specific instruction for this agent's task
- **Context Documents**: Markdown documents attached to this agent type
- **Available Tools**: Core MCP toolkit + subset of optional tools
- **Web Search Permission**: Boolean flag

### Core MCP Toolkit (Always Available)
1. `break_down_task()` - Spawn breakdown agent for current task
2. `start_subtask(task, agent_type)` - Create isolated subtask with specific agent
3. `request_context()` - Spawn context addition agent
4. `request_tools()` - Spawn tool discovery/creation agent  
5. `end_task(status, result)` - Mark task complete (success/failure)
6. `flag_for_review(issue)` - Queue item for manual review
7. `think_out_loud()` - Log reasoning and planning thoughts

### Database Schema (SQLite)

```sql
-- Agent Configurations
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    instruction TEXT NOT NULL,
    context_documents TEXT, -- JSON array of document IDs
    available_tools TEXT,   -- JSON array of tool names
    web_search_allowed BOOLEAN DEFAULT FALSE
);

-- Context Documents  
CREATE TABLE context_documents (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL -- Markdown format
);

-- Task Management
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    parent_task_id INTEGER,
    tree_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, running, complete, failed
    result TEXT,
    summary TEXT, -- Concise summary for parent agent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 0,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Message History (All agent communications)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    message_type TEXT NOT NULL, -- 'user_input', 'agent_response', 'tool_call', 'tool_response', 'system'
    content TEXT NOT NULL,
    metadata TEXT, -- JSON for tool names, parameters, etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Optional Tools Registry
CREATE TABLE tools (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    mcp_config TEXT -- JSON MCP tool configuration
);
```

## Required Agents (Initial Database Seed)

### 1. Agent Selector (`agent_selector`)
- **Instruction**: "Analyze the given task and select the most appropriate agent type to handle it. If no suitable agent exists, create a new agent configuration."
- **Context**: System architecture documentation, available agents list
- **Tools**: Core toolkit + database access

### 2. Task Breakdown Agent (`task_breakdown`)  
- **Instruction**: "Break down the given task into sequential subtasks that can be handled by individual agents."
- **Context**: Task breakdown best practices
- **Tools**: Core toolkit

### 3. Context Addition Agent (`context_addition`)
- **Instruction**: "Determine what additional context documents are needed for the requesting agent to complete its task."
- **Context**: Available context documents, system documentation
- **Tools**: Core toolkit + web search

### 4. Tool Addition Agent (`tool_addition`)
- **Instruction**: "Find, create, or configure the MCP tools needed for the requesting agent's task."
- **Context**: Available tools registry, MCP documentation
- **Tools**: Core toolkit + web search + code generation

### 5. Task Evaluator Agent (`task_evaluator`)
- **Instruction**: "Evaluate the completed task result and determine if it meets the requirements. Always triggered when task ends."
- **Context**: Task evaluation criteria
- **Tools**: Core toolkit

### 6. Supervisor Agent (`supervisor`)
- **Instruction**: "Monitor long-running or potentially stuck agents and determine if intervention is needed."
- **Context**: System monitoring guidelines
- **Tools**: Core toolkit + system monitoring

### 7. Documentation Agent (`documentation_agent`)
- **Instruction**: "Document any system changes, new procedures, or important discoveries from the completed task. Always triggered in parallel with task evaluator."
- **Context**: Documentation standards, existing system documentation
- **Tools**: Core toolkit + database access

### 8. Summary Agent (`summary_agent`)
- **Instruction**: "Create a concise summary of task execution and results for the parent agent, filtering out redundant details."
- **Context**: Summarization guidelines
- **Tools**: Core toolkit + message history access

### 9. Review Agent (`review_agent`)
- **Instruction**: "Analyze flagged issues and determine system improvements needed."
- **Context**: System improvement guidelines
- **Tools**: Core toolkit + code modification + git operations

## Core System Documentation (Initial Context Documents)

These documents will be seeded into the database at system launch:

### 1. System Overview
- What this system is and how it works
- Core principles and design philosophy
- Universal agent architecture explanation

### 2. System Architecture  
- Database schema and relationships
- Agent lifecycle and communication
- Task tree isolation principles
- File structure and component organization

### 3. Environment Details
- Hosting environment specifications (cloud VM setup)
- Available system resources and permissions
- Docker container structure and restart procedures
- Git repository access and commit procedures

### 4. System Improvement Guide
- Steps for self-modification: create branch → modify code → test → restart → validate
- Git workflow and commit practices
- Database modification guidelines
- Manual override and debugging procedures

### 5. MCP Tool Development Guide
- How to create new MCP tools
- Tool registration and permission management
- Testing and validation procedures for new tools

*Note: Additional context documents will be created by agents as needed through the context_addition agent.*

## Required MCP Tools

### Core System Tools
- **Terminal Access**: Full shell access for system operations
- **Git Operations**: Complete git control including branch, commit, push to core project
- **Repository Management**: Create new private repositories for projects
- **Database Access**: SQLite read/write operations
- **File System**: Read/write access to system files
- **Process Control**: Ability to restart system services

### Initially Optional Tools (MVP Seed)
- **list_agents**: Query available agent configurations
- **list_documents**: Query available context documents  
- **list_optional_tools**: Query tools registry
- **use_terminal**: Execute shell commands with full system access
- **github_operations**: Git clone, branch, commit, push, create repositories
- **query_database**: Direct SQLite database queries for system introspection

## Web Interface Requirements

### Main Dashboard
- **Task Input**: Simple text area for new task entry
- **Active Trees**: List of running task trees with status
- **System Controls**: 
  - Concurrent agent limit (default: 3)
  - Execution mode: Automatic / Manual stepping
  - System restart button

### Task Tree Viewer
- **Hierarchical Display**: Show parent/child task relationships
- **Agent Status**: Current agent type and status for each task
- **Message History**: Expandable view of all messages, tool calls, and responses for each task
- **Real-time Updates**: WebSocket updates for task progress

### Review Queue
- **Flagged Items**: List of items flagged for manual review
- **System Logs**: Recent agent outputs and system events

## Success Criteria

### Core Functionality
1. **Task Processing**: Accept user input and route to appropriate agent
2. **Recursive Breakdown**: Complex tasks get broken down automatically  
3. **Tool Discovery**: Agents can find/create tools they need
4. **Self-Modification**: System can improve its own code
5. **Supervision**: Long-running tasks are monitored and managed

### Technical Requirements
1. **Task Isolation**: Multiple task trees run independently
2. **Agent Concurrency**: Configurable number of simultaneous agents
3. **Failure Recovery**: Supervisor agents handle stuck/failed tasks
4. **System Restart**: Clean restart capability after self-modifications
5. **Data Persistence**: All task history and configurations persist across restarts

## MVP Limitations

### Deliberately Excluded
- Multi-user support
- Authentication/authorization  
- Complex UI features
- Performance optimization
- External integrations beyond git/web

### Technical Constraints
- Single-instance deployment
- SQLite database only
- Local file system persistence
- Basic error handling
- Simple logging only

The MVP focuses entirely on proving the core recursive agent concept and self-improvement loop work reliably.