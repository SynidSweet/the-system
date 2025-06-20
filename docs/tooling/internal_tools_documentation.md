# System Tools Reference - Internal Documentation

## Overview

This document describes all available tools in the MVP system, their capabilities, usage patterns, and how to request additional tools when needed. All agents should reference this document to understand their tool ecosystem.

## Tool Architecture

### Permission System
- **Base Tools**: Every agent type has minimal default tools assigned in the database
- **Dynamic Assignment**: Additional tools assigned by Tool Addition Agent based on task requirements
- **Database-Driven**: All permissions resolved in real-time from `agent_base_permissions` and `task_tool_assignments` tables
- **Time-Limited**: Task-specific tool assignments can have expiration times
- **Usage Tracking**: Every tool operation logged for optimization analysis

### MCP Integration
Tools are implemented as **Model Context Protocol (MCP) servers** with standardized interfaces:
- Each tool category runs as a separate MCP server process
- Permission checking happens at the MCP server level before execution
- All tool calls automatically logged with timing, parameters, and outcomes
- Servers can be dynamically started/stopped without system restart

## Core System Tools

### Entity Manager
**Tool Name**: `entity_manager`  
**Availability**: All agents (base tool)  
**Purpose**: Core CRUD operations for all entity types

#### Available Operations:
```
# Agent Management
- get_agent(agent_id) → agent configuration
- update_agent(agent_id, updates) → success boolean  
- create_agent(config) → new agent_id
- list_agents(filters) → agent list

# Task Management  
- get_task(task_id) → task details with current status
- update_task(task_id, updates) → success boolean
- create_task(instruction, **params) → new task_id
- get_task_dependencies(task_id) → dependency list

# Process Management
- get_process(process_id) → process template
- list_processes(category) → available processes

# Document Management
- get_document(doc_id) → document content and metadata
- create_document(name, content, metadata) → doc_id
- update_document(doc_id, updates) → success boolean
- search_documents(query, filters) → matching documents

# Tool Management
- get_tool(tool_id) → tool definition and capabilities
- list_tools(category) → available tools

# Event Management  
- get_events(filters) → system events for analysis
- log_event(type, entity_id, data) → event_id
```

#### Usage Notes:
- **Required Parameters**: All operations require `agent_type` and `task_id` for permission checking
- **Permission Levels**: Operations respect entity-level permissions (read/write per entity type)
- **Error Handling**: Permission errors clearly distinguish between "not found" and "access denied"
- **Performance**: Entity operations automatically logged with execution time

#### Example Usage:
```python
# Get current task details
task = await call_tool("entity_manager", "get_task", {
    "task_id": current_task_id,
    "agent_type": "planning_agent", 
    "task_id": current_task_id
})

# Create new document
doc_id = await call_tool("entity_manager", "create_document", {
    "name": "analysis_results",
    "content": "# Analysis Results\n...",
    "metadata": {"category": "analysis", "task_id": current_task_id},
    "agent_type": "investigator_agent",
    "task_id": current_task_id
})
```

### Message User  
**Tool Name**: `message_user`  
**Availability**: All agents (base tool)  
**Purpose**: Send messages and updates to system users

#### Available Operations:
```
- send_message(message, type="info") → success boolean
- send_structured_message(title, content, sections) → success boolean
```

#### Message Types:
- `info` - General information
- `success` - Successful completion notifications  
- `warning` - Important notices requiring attention
- `error` - Error conditions needing user intervention
- `progress` - Progress updates for long-running tasks

#### Usage Notes:
- **No Permission Restrictions**: All agents can send user messages
- **Automatic Context**: Messages automatically tagged with source agent and task
- **Rate Limiting**: Excessive messaging may trigger optimization review
- **Structured Format**: Use structured messages for complex information

#### Example Usage:
```python
# Send simple progress update
await call_tool("message_user", "send_message", {
    "message": "Analysis phase completed successfully. Found 3 optimization opportunities.",
    "message_type": "info"
})

# Send structured results
await call_tool("message_user", "send_structured_message", {
    "title": "Task Completion Report",
    "content": "Task completed with high quality rating.",
    "sections": [
        {"title": "Results", "content": "Generated 5 recommendations"},
        {"title": "Next Steps", "content": "Ready for implementation review"}
    ]
})
```

## File System Tools

### File System Listing
**Tool Name**: `file_system_listing`  
**Availability**: Context Addition, Tool Addition, Documentation Agent (base); others via assignment  
**Purpose**: Read and browse file system within allowed directories

#### Available Operations:
```
- list_files(directory_path) → file list
- read_file(file_path) → file content string
- file_exists(file_path) → boolean
```

#### Security Restrictions:
- **Sandboxed Access**: Only allowed paths defined in system configuration
- **No Write Operations**: Read-only access for safety
- **Path Validation**: All paths validated against allowed directories before access
- **Automatic Logging**: File access logged for audit and optimization

#### Typical Allowed Paths:
- `/project/docs` - Project documentation
- `/project/src` - Source code (read-only)
- `/project/config` - Configuration files
- `/project/output` - Generated outputs

### File Edit
**Tool Name**: `file_edit`  
**Availability**: Assigned by Tool Addition Agent when justified  
**Purpose**: Create, modify, and write files within sandbox

#### Available Operations:
```
- write_file(file_path, content) → success boolean
- create_file(file_path, content) → success boolean  
- append_to_file(file_path, content) → success boolean
```

#### Security Features:
- **Higher Permission Level**: Requires explicit assignment by Tool Addition Agent
- **Sandboxed Writes**: Can only write within allowed directories
- **Backup Creation**: System may create backups before modifications
- **Change Logging**: All file modifications logged with content hashes

#### Request Pattern:
```python
# Request file editing capability
await call_tool("need_more_tools", {
    "tool_request": "file editing capabilities", 
    "justification": "Need to create configuration files for the new component"
})
```

## Database Analysis Tools

### SQL Lite
**Tool Name**: `sql_lite`  
**Availability**: Review Agent, Investigator Agent, Optimizer Agent (base); others via assignment  
**Purpose**: Execute predefined database queries for system analysis

#### Available Query Types:
```
- get_recent_events(since_timestamp, limit) → recent system events
- get_agent_performance(agent_id, since_timestamp) → performance metrics  
- get_entity_relationships(entity_type, entity_id) → relationship graph
- get_task_dependencies(task_id) → task dependency tree
- get_optimization_opportunities(min_usage, max_success_rate) → improvement candidates
```

#### Security Model:
- **Predefined Queries Only**: No arbitrary SQL execution
- **Parameter Binding**: All parameters safely bound to prevent injection
- **Query-Specific Permissions**: Tool assignments can limit specific queries
- **Result Limiting**: Automatic limits prevent excessive data retrieval

#### Permission Scoping:
When assigned by Tool Addition Agent, can include query restrictions:
```python
# Example: Limited database access
"tool_permissions": {
    "sql_lite": {
        "allowed_queries": ["get_recent_events", "get_agent_performance"]
    }
}
```

#### Usage Examples:
```python
# Analyze recent system performance
events = await call_tool("sql_lite", "execute_query", {
    "query_name": "get_recent_events",
    "parameters": [time.time() - 86400, 50],  # Last 24 hours, 50 events
    "agent_type": "investigator_agent",
    "task_id": current_task_id
})

# Get performance data for optimization
performance = await call_tool("sql_lite", "execute_query", {
    "query_name": "get_agent_performance", 
    "parameters": ["planning_agent", time.time() - 604800],  # Last week
    "agent_type": "optimizer_agent",
    "task_id": current_task_id
})
```

## System Operation Tools

### Terminal
**Tool Name**: `terminal`  
**Availability**: Recovery Agent (base); others via assignment for specific operations  
**Purpose**: Execute whitelisted system commands for diagnosis and operations

#### Allowed Commands:
```
Git Operations:
- git status, git log, git diff, git show, git branch

File Operations:  
- ls (all variations), pwd, cat, grep, find

System Information:
- which, echo, python --version, python -c "simple expressions"
```

#### Security Features:
- **Command Whitelist**: Only predefined commands executable
- **Argument Filtering**: Command arguments validated against allowed patterns
- **Timeout Protection**: 30-second timeout prevents hanging processes
- **Working Directory Control**: Can be restricted to specific directories
- **Output Capture**: All stdout/stderr captured and returned safely

#### Usage Notes:
- **High Security Tool**: Requires strong justification for assignment
- **Audit Trail**: All command executions logged with full command line
- **Error Handling**: Command failures returned as structured data, not exceptions

#### Example Usage:
```python
# Check git repository status
result = await call_tool("terminal", "execute_command", {
    "command": "git status --porcelain",
    "working_directory": "/project",
    "agent_type": "investigator_agent", 
    "task_id": current_task_id
})

if result["returncode"] == 0:
    git_status = result["stdout"]
else:
    error_info = result["stderr"]
```

### GitHub
**Tool Name**: `github`  
**Availability**: Tool Addition Agent (base); others via assignment  
**Purpose**: Git repository operations and version control

#### Available Operations:
```
- git_status() → repository status
- git_log(limit, since) → commit history
- git_diff(file_path) → file changes
- git_commit(message, files) → create commit
- git_push(branch) → push changes
- git_branch(action, branch_name) → branch operations
```

#### Security Considerations:
- **Repository Scoped**: Operations limited to project repository
- **Commit Verification**: Commits require explicit message and file specification
- **Push Restrictions**: May require additional authorization for production branches
- **Change Tracking**: All git operations logged for project audit trail

## Tool Request System

### Requesting Additional Tools

When your current tools are insufficient for the task, use the `need_more_tools` function:

```python
await call_tool("need_more_tools", {
    "tool_request": "specific capability needed",
    "justification": "detailed reason why this tool is necessary for task success"
})
```

#### Request Process:
1. **Validation**: Request Validation Agent evaluates necessity and security
2. **Assignment**: Tool Addition Agent determines appropriate tools
3. **Implementation**: Database updated with new permissions
4. **Notification**: System message confirms tool availability

#### Good Request Examples:
```python
# Database analysis need
await call_tool("need_more_tools", {
    "tool_request": "database analysis capabilities",
    "justification": "Need to analyze recent system events to identify performance bottlenecks for optimization recommendations"
})

# File editing need  
await call_tool("need_more_tools", {
    "tool_request": "file modification capabilities",
    "justification": "Need to create and update configuration files as part of system setup process"
})

# System diagnosis need
await call_tool("need_more_tools", {
    "tool_request": "system diagnostic tools", 
    "justification": "Need to examine system processes and logs to diagnose reported performance issues"
})
```

#### Request Guidelines:
- **Be Specific**: Clearly describe the capability needed
- **Justify Necessity**: Explain why current tools are insufficient
- **Task Relevant**: Connect tool need to specific task requirements
- **Security Aware**: Understand that higher-privilege tools require stronger justification

### Tool Assignment Patterns

The Tool Addition Agent uses these patterns to assign tools:

#### Analysis Tasks → Database Tools
```
Keywords: "analyze", "performance", "events", "history", "patterns"
Assigns: sql_lite with query restrictions
Duration: 24 hours typically
```

#### File Operations → File System Tools
```
Keywords: "file", "document", "code", "configuration"  
Assigns: file_system_listing (read) or file_edit (write)
Duration: 8-12 hours typically
```

#### System Issues → Diagnostic Tools
```
Keywords: "system", "process", "debug", "diagnose", "performance"
Assigns: terminal with command restrictions
Duration: 6 hours typically
```

#### Code Changes → Version Control
```
Keywords: "git", "commit", "repository", "branch", "code changes"
Assigns: github with repository scope
Duration: 48 hours typically
```

## Usage Best Practices

### Permission Efficiency
- **Use Base Tools First**: Exhaust capabilities of assigned tools before requesting more
- **Specific Requests**: Request specific capabilities rather than broad tool categories
- **Temporary Assignment**: Understand that additional tools may have time limits

### Security Awareness
- **Least Privilege**: Only request minimum necessary permissions
- **Audit Trail**: Remember all tool usage is logged and analyzed
- **Safe Operations**: Prefer read operations over write operations when possible

### Performance Optimization
- **Batch Operations**: Group related tool calls to minimize overhead
- **Cache Results**: Store results in variables rather than repeated tool calls
- **Error Handling**: Check tool call results and handle errors gracefully

### Integration Patterns
- **Entity Updates**: Use entity_manager for all system state changes
- **User Communication**: Use message_user for progress updates and results
- **Documentation**: Create documents for reusable knowledge and results

## Tool Development and Extension

### Adding New Tools
The system supports adding new tools through:

1. **MCP Server Implementation**: New capabilities implemented as MCP servers
2. **Database Registration**: Tools registered in `available_tools` table
3. **Permission Integration**: Permission checking integrated into tool operations
4. **Usage Tracking**: Automatic logging for optimization analysis

### Tool Optimization
The system continuously optimizes tools through:

- **Usage Pattern Analysis**: Identifying which tools are most effective
- **Performance Monitoring**: Tracking tool execution times and success rates  
- **Permission Refinement**: Adjusting permission models based on actual usage
- **Capability Gaps**: Detecting unmet needs for new tool development

This tool ecosystem is designed to grow and adapt based on actual usage patterns while maintaining security and auditability throughout the system's evolution.