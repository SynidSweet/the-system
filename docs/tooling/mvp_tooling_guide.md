# MVP Optional Tooling Implementation Guide

## Architecture Overview

The MVP tooling system implements a **database-driven permission model** with **additive tool assignment**:

- **Base Tools**: Minimal tools assigned to each agent type by default
- **Dynamic Assignment**: Tool Addition Agent assigns additional tools to specific tasks
- **Database Permissions**: All permissions stored and resolved from database
- **MCP Integration**: Tools implemented as MCP servers with permission checking
- **Usage Tracking**: Complete audit trail for optimization and security

## Database Schema

### Permission Management Tables

```sql
-- Base permissions for each agent type
CREATE TABLE agent_base_permissions (
    agent_type TEXT PRIMARY KEY,
    entity_permissions JSON,     -- {"agent": ["read"], "task": ["read", "write"]}
    base_tools JSON,            -- ["entity_manager", "message_user"]
    max_concurrent_tools INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic tool assignments to specific tasks
CREATE TABLE task_tool_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    tool_permissions JSON,       -- Tool-specific permissions
    assigned_by_agent_id INTEGER, -- Which agent assigned this tool
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,        -- Optional expiration
    assignment_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (assigned_by_agent_id) REFERENCES tasks(id)
);

-- Tool usage tracking for optimization
CREATE TABLE tool_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    agent_type TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    operation TEXT,              -- Specific tool operation used
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    execution_time_ms INTEGER,
    parameters_hash TEXT,        -- Hash of parameters for pattern analysis
    result_summary TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Tool definitions and capabilities
CREATE TABLE available_tools (
    tool_name TEXT PRIMARY KEY,
    tool_type TEXT NOT NULL,     -- "mcp_server", "internal", "external"
    description TEXT,
    mcp_server_url TEXT,         -- For MCP tools
    available_operations JSON,   -- List of operations this tool supports
    security_level TEXT DEFAULT 'standard', -- "minimal", "standard", "elevated"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Initial Data Population

```sql
-- Base agent permissions
INSERT INTO agent_base_permissions (agent_type, entity_permissions, base_tools) VALUES
('agent_selector', '{"agent": ["read"], "task": ["read", "write"]}', '["entity_manager"]'),
('planning_agent', '{"task": ["read", "write"], "process": ["read"]}', '["entity_manager"]'),
('context_addition', '{"document": ["read", "write"], "task": ["read"]}', '["entity_manager", "file_system_listing"]'),
('tool_addition', '{"tool": ["read", "write"], "task": ["read", "write"]}', '["entity_manager", "file_system_listing"]'),
('task_evaluator', '{"task": ["read"], "event": ["read"]}', '["entity_manager"]'),
('summary_agent', '{"task": ["read"], "event": ["read"]}', '["entity_manager"]'),
('documentation_agent', '{"document": ["read", "write"], "task": ["read"]}', '["entity_manager", "file_system_listing"]'),
('review_agent', '{"all": ["read"], "agent": ["write"], "process": ["write"]}', '["entity_manager", "sql_lite", "file_system_listing"]'),
('feedback_agent', '{"task": ["read"], "event": ["read"]}', '["entity_manager"]'),
('request_validation', '{"task": ["read"], "tool": ["read"]}', '["entity_manager"]'),
('investigator_agent', '{"all": ["read"]}', '["entity_manager", "sql_lite"]'),
('optimizer_agent', '{"all": ["read", "write"]}', '["entity_manager", "sql_lite"]'),
('recovery_agent', '{"all": ["read", "write"]}', '["entity_manager", "sql_lite", "terminal"]');

-- Available tools registry
INSERT INTO available_tools (tool_name, tool_type, description, available_operations, security_level) VALUES
('entity_manager', 'mcp_server', 'Core entity CRUD operations', '["read", "write", "create", "delete"]', 'minimal'),
('message_user', 'mcp_server', 'Send messages to user', '["send_message"]', 'minimal'),
('file_system_listing', 'mcp_server', 'List and read files', '["list_files", "read_file"]', 'standard'),
('file_edit', 'mcp_server', 'Edit and write files', '["write_file", "edit_file", "create_file"]', 'elevated'),
('sql_lite', 'mcp_server', 'Database queries', '["execute_query"]', 'standard'),
('terminal', 'mcp_server', 'System commands', '["execute_command"]', 'elevated'),
('github', 'mcp_server', 'Git operations', '["git_status", "git_commit", "git_push"]', 'elevated');
```

## Permission Management System

### Core Permission Manager

```python
# core/permissions/manager.py
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class AgentPermissions:
    entity_access: Dict[str, List[str]]
    tools: List[str]
    tool_permissions: Dict[str, Dict[str, any]]

@dataclass
class ToolAssignment:
    tool_name: str
    assignment_reason: str
    duration_hours: Optional[int] = None
    specific_permissions: Optional[Dict[str, any]] = None

class DatabasePermissionManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_agent_permissions(self, agent_type: str, task_id: int = None) -> AgentPermissions:
        """Get complete permissions for agent including task-specific tools"""
        # Get base permissions
        base_query = """
            SELECT entity_permissions, base_tools 
            FROM agent_base_permissions 
            WHERE agent_type = ?
        """
        base_result = await self.db.execute(base_query, [agent_type]).fetchone()
        
        if not base_result:
            raise ValueError(f"No base permissions found for agent type: {agent_type}")
        
        entity_permissions = json.loads(base_result['entity_permissions'])
        base_tools = json.loads(base_result['base_tools'])
        
        # Get task-specific tool assignments
        task_tools = []
        tool_permissions = {}
        
        if task_id:
            task_query = """
                SELECT tool_name, tool_permissions 
                FROM task_tool_assignments 
                WHERE task_id = ? 
                AND is_active = TRUE 
                AND (expires_at IS NULL OR expires_at > ?)
            """
            task_results = await self.db.execute(task_query, [task_id, time.time()]).fetchall()
            
            for row in task_results:
                task_tools.append(row['tool_name'])
                if row['tool_permissions']:
                    tool_permissions[row['tool_name']] = json.loads(row['tool_permissions'])
        
        return AgentPermissions(
            entity_access=entity_permissions,
            tools=base_tools + task_tools,
            tool_permissions=tool_permissions
        )
    
    async def assign_tool_to_task(self, task_id: int, tool_assignment: ToolAssignment, 
                                 assigned_by: int) -> bool:
        """Assign tool to specific task"""
        expires_at = None
        if tool_assignment.duration_hours:
            expires_at = time.time() + (tool_assignment.duration_hours * 3600)
        
        tool_permissions_json = None
        if tool_assignment.specific_permissions:
            tool_permissions_json = json.dumps(tool_assignment.specific_permissions)
        
        query = """
            INSERT INTO task_tool_assignments 
            (task_id, tool_name, tool_permissions, assigned_by_agent_id, expires_at, assignment_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        await self.db.execute(query, [
            task_id, 
            tool_assignment.tool_name,
            tool_permissions_json,
            assigned_by,
            expires_at,
            tool_assignment.assignment_reason
        ])
        
        # Log tool assignment event
        await self.log_tool_assignment(task_id, tool_assignment, assigned_by)
        return True
    
    async def check_permission(self, agent_type: str, task_id: int, 
                              operation: str, entity_type: str) -> bool:
        """Check if agent has permission for specific operation"""
        permissions = await self.get_agent_permissions(agent_type, task_id)
        
        # Check entity permissions
        if entity_type in permissions.entity_access:
            return operation in permissions.entity_access[entity_type]
        
        # Check for wildcard permissions
        if "all" in permissions.entity_access:
            return operation in permissions.entity_access["all"]
        
        return False
    
    async def log_tool_usage(self, task_id: int, agent_type: str, tool_name: str, 
                           operation: str, success: bool, execution_time_ms: int,
                           parameters_hash: str = None, result_summary: str = None):
        """Log tool usage for optimization analysis"""
        query = """
            INSERT INTO tool_usage_events 
            (task_id, agent_type, tool_name, operation, success, execution_time_ms, parameters_hash, result_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.db.execute(query, [
            task_id, agent_type, tool_name, operation, 
            success, execution_time_ms, parameters_hash, result_summary
        ])
    
    async def cleanup_expired_assignments(self):
        """Remove expired tool assignments"""
        query = """
            UPDATE task_tool_assignments 
            SET is_active = FALSE 
            WHERE expires_at IS NOT NULL AND expires_at <= ?
        """
        await self.db.execute(query, [time.time()])
```

## MCP Server Implementations

### 1. Entity Manager MCP Server

```python
# tools/mcp_servers/entity_manager.py
from mcp import Server
from typing import Dict, List, Any
import json

class EntityManagerMCP:
    def __init__(self, db_connection, permission_manager):
        self.db = db_connection
        self.permissions = permission_manager
        self.server = Server("entity-manager")
        self.register_tools()
    
    def register_tools(self):
        # Agent Management Tools
        self.server.register_tool("get_agent", self.get_agent)
        self.server.register_tool("update_agent", self.update_agent)
        self.server.register_tool("create_agent", self.create_agent)
        self.server.register_tool("list_agents", self.list_agents)
        
        # Task Management Tools
        self.server.register_tool("get_task", self.get_task)
        self.server.register_tool("update_task", self.update_task)
        self.server.register_tool("create_task", self.create_task)
        self.server.register_tool("get_task_dependencies", self.get_task_dependencies)
        
        # Process Management Tools
        self.server.register_tool("get_process", self.get_process)
        self.server.register_tool("list_processes", self.list_processes)
        
        # Document Management Tools
        self.server.register_tool("get_document", self.get_document)
        self.server.register_tool("create_document", self.create_document)
        self.server.register_tool("update_document", self.update_document)
        self.server.register_tool("search_documents", self.search_documents)
        
        # Tool Management Tools
        self.server.register_tool("get_tool", self.get_tool)
        self.server.register_tool("list_tools", self.list_tools)
        
        # Event Management Tools
        self.server.register_tool("get_events", self.get_events)
        self.server.register_tool("log_event", self.log_event)
    
    async def get_agent(self, agent_id: int, agent_type: str, task_id: int) -> Dict[str, Any]:
        """Get agent by ID"""
        if not await self.permissions.check_permission(agent_type, task_id, "read", "agent"):
            raise PermissionError("Insufficient permissions to read agent")
        
        start_time = time.time()
        success = False
        
        try:
            query = "SELECT * FROM agents WHERE id = ?"
            result = await self.db.execute(query, [agent_id]).fetchone()
            success = True
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "entity_manager", "get_agent",
                success, int((time.time() - start_time) * 1000)
            )
            
            return dict(result) if result else None
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "entity_manager", "get_agent",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
    
    async def update_agent(self, agent_id: int, updates: Dict[str, Any], 
                          agent_type: str, task_id: int) -> bool:
        """Update agent configuration"""
        if not await self.permissions.check_permission(agent_type, task_id, "write", "agent"):
            raise PermissionError("Insufficient permissions to update agent")
        
        # Build update query dynamically
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key in ["instruction", "specialization", "context_documents", "available_tools"]:
                set_clauses.append(f"{key} = ?")
                params.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        params.append(time.time())
        params.append(agent_id)
        
        query = f"UPDATE agents SET {', '.join(set_clauses)} WHERE id = ?"
        
        await self.db.execute(query, params)
        
        # Log the update event
        await self.permissions.log_tool_usage(
            task_id, agent_type, "entity_manager", "update_agent", True, 0,
            result_summary=f"Updated agent {agent_id}"
        )
        
        return True
    
    # Similar implementations for other entity operations...
```

### 2. File System MCP Server

```python
# tools/mcp_servers/file_system.py
import os
import hashlib
from pathlib import Path

class FileSystemMCP:
    def __init__(self, allowed_paths: List[str], permission_manager):
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self.permissions = permission_manager
        self.server = Server("file-system")
        self.register_tools()
    
    def register_tools(self):
        self.server.register_tool("list_files", self.list_files)
        self.server.register_tool("read_file", self.read_file)
        self.server.register_tool("write_file", self.write_file)
        self.server.register_tool("create_file", self.create_file)
        self.server.register_tool("file_exists", self.file_exists)
    
    def is_path_allowed(self, file_path: str) -> bool:
        """Check if file path is within allowed directories"""
        try:
            target_path = Path(file_path).resolve()
            return any(
                target_path.is_relative_to(allowed_path) 
                for allowed_path in self.allowed_paths
            )
        except (ValueError, OSError):
            return False
    
    async def list_files(self, directory_path: str, agent_type: str, task_id: int) -> List[str]:
        """List files in directory"""
        if not self.is_path_allowed(directory_path):
            raise PermissionError(f"Access to {directory_path} not allowed")
        
        start_time = time.time()
        
        try:
            directory = Path(directory_path)
            if not directory.exists() or not directory.is_dir():
                raise FileNotFoundError(f"Directory {directory_path} not found")
            
            files = [
                str(item.relative_to(directory)) 
                for item in directory.iterdir()
                if self.is_path_allowed(str(item))
            ]
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "file_system", "list_files",
                True, int((time.time() - start_time) * 1000),
                result_summary=f"Listed {len(files)} files"
            )
            
            return files
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "file_system", "list_files",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
    
    async def read_file(self, file_path: str, agent_type: str, task_id: int) -> str:
        """Read file contents"""
        if not self.is_path_allowed(file_path):
            raise PermissionError(f"Access to {file_path} not allowed")
        
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "file_system", "read_file",
                True, int((time.time() - start_time) * 1000),
                parameters_hash=hashlib.md5(file_path.encode()).hexdigest(),
                result_summary=f"Read {len(content)} characters"
            )
            
            return content
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "file_system", "read_file",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
    
    async def write_file(self, file_path: str, content: str, 
                        agent_type: str, task_id: int) -> bool:
        """Write content to file"""
        # Check if agent has write permission for this tool
        permissions = await self.permissions.get_agent_permissions(agent_type, task_id)
        if "file_edit" not in permissions.tools:
            raise PermissionError("Agent does not have file editing permissions")
        
        if not self.is_path_allowed(file_path):
            raise PermissionError(f"Access to {file_path} not allowed")
        
        start_time = time.time()
        
        try:
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "file_system", "write_file",
                True, int((time.time() - start_time) * 1000),
                result_summary=f"Wrote {len(content)} characters"
            )
            
            return True
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "file_system", "write_file",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
```

### 3. SQL Lite MCP Server

```python
# tools/mcp_servers/sql_lite.py

class SQLiteMCP:
    def __init__(self, db_connection, permission_manager):
        self.db = db_connection
        self.permissions = permission_manager
        self.server = Server("sql-lite")
        
        # Predefined safe queries
        self.allowed_queries = {
            "get_recent_events": """
                SELECT event_type, primary_entity_type, primary_entity_id, 
                       timestamp, outcome 
                FROM events 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """,
            "get_agent_performance": """
                SELECT agent_id, COUNT(*) as task_count, 
                       AVG(CASE WHEN outcome = 'success' THEN 1.0 ELSE 0.0 END) as success_rate,
                       AVG(duration_seconds) as avg_duration
                FROM task_completions 
                WHERE agent_id = ? AND timestamp > ?
                GROUP BY agent_id
            """,
            "get_entity_relationships": """
                SELECT source_type, source_id, target_type, target_id, 
                       relationship_type, strength
                FROM entity_relationships 
                WHERE source_type = ? AND source_id = ?
            """,
            "get_task_dependencies": """
                SELECT t.id, t.instruction, t.status, t.assigned_agent
                FROM tasks t
                JOIN task_dependencies td ON t.id = td.dependency_task_id
                WHERE td.task_id = ?
            """,
            "get_optimization_opportunities": """
                SELECT entity_type, entity_id, 
                       COUNT(*) as usage_count,
                       AVG(success_rate) as avg_success_rate
                FROM entity_usage_stats 
                WHERE usage_count > ?
                GROUP BY entity_type, entity_id
                HAVING avg_success_rate < ?
            """
        }
        
        self.register_tools()
    
    def register_tools(self):
        self.server.register_tool("execute_query", self.execute_query)
        self.server.register_tool("list_available_queries", self.list_available_queries)
    
    async def execute_query(self, query_name: str, parameters: List[Any],
                           agent_type: str, task_id: int) -> List[Dict[str, Any]]:
        """Execute predefined query with parameters"""
        # Check if query is allowed
        if query_name not in self.allowed_queries:
            raise ValueError(f"Query '{query_name}' not in allowed queries")
        
        # Check agent permissions for this tool
        permissions = await self.permissions.get_agent_permissions(agent_type, task_id)
        if "sql_lite" not in permissions.tools:
            raise PermissionError("Agent does not have SQL query permissions")
        
        # Check for query-specific permissions
        tool_perms = permissions.tool_permissions.get("sql_lite", {})
        allowed_queries = tool_perms.get("allowed_queries", list(self.allowed_queries.keys()))
        
        if query_name not in allowed_queries:
            raise PermissionError(f"Agent not authorized for query '{query_name}'")
        
        start_time = time.time()
        
        try:
            query = self.allowed_queries[query_name]
            results = await self.db.execute(query, parameters).fetchall()
            
            # Convert to list of dicts
            result_dicts = [dict(row) for row in results]
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "sql_lite", f"query_{query_name}",
                True, int((time.time() - start_time) * 1000),
                parameters_hash=hashlib.md5(str(parameters).encode()).hexdigest(),
                result_summary=f"Returned {len(result_dicts)} rows"
            )
            
            return result_dicts
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "sql_lite", f"query_{query_name}",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
    
    async def list_available_queries(self, agent_type: str, task_id: int) -> List[str]:
        """List queries available to this agent"""
        permissions = await self.permissions.get_agent_permissions(agent_type, task_id)
        tool_perms = permissions.tool_permissions.get("sql_lite", {})
        
        return tool_perms.get("allowed_queries", list(self.allowed_queries.keys()))
```

### 4. Terminal MCP Server

```python
# tools/mcp_servers/terminal.py
import subprocess
import shlex
from typing import List, Dict

class TerminalMCP:
    def __init__(self, permission_manager):
        self.permissions = permission_manager
        self.server = Server("terminal")
        
        # Whitelisted commands
        self.allowed_commands = {
            "git": ["status", "log", "diff", "show", "branch"],
            "ls": ["*"],  # All ls variations allowed
            "pwd": ["*"],
            "cat": ["*"],  # But still subject to file system restrictions
            "grep": ["*"],
            "find": ["*"],
            "echo": ["*"],
            "which": ["*"],
            "python": ["--version", "-c"],  # Limited python execution
        }
        
        self.register_tools()
    
    def register_tools(self):
        self.server.register_tool("execute_command", self.execute_command)
        self.server.register_tool("list_allowed_commands", self.list_allowed_commands)
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if command is in whitelist"""
        parts = shlex.split(command)
        if not parts:
            return False
        
        base_cmd = parts[0]
        
        if base_cmd not in self.allowed_commands:
            return False
        
        allowed_args = self.allowed_commands[base_cmd]
        if "*" in allowed_args:
            return True
        
        # Check if any arguments match allowed patterns
        cmd_args = parts[1:] if len(parts) > 1 else []
        return any(arg in allowed_args for arg in cmd_args)
    
    async def execute_command(self, command: str, working_directory: str = None,
                             agent_type: str = None, task_id: int = None) -> Dict[str, Any]:
        """Execute whitelisted command"""
        # Check permissions
        permissions = await self.permissions.get_agent_permissions(agent_type, task_id)
        if "terminal" not in permissions.tools:
            raise PermissionError("Agent does not have terminal access")
        
        # Check command whitelist
        if not self.is_command_allowed(command):
            raise PermissionError(f"Command '{command}' not allowed")
        
        start_time = time.time()
        
        try:
            # Execute with timeout and restrictions
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=working_directory
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "terminal", "execute_command",
                result.returncode == 0, execution_time,
                parameters_hash=hashlib.md5(command.encode()).hexdigest(),
                result_summary=f"Exit code: {result.returncode}"
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command,
                "execution_time_ms": execution_time
            }
            
        except subprocess.TimeoutExpired:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "terminal", "execute_command",
                False, 30000, result_summary="Command timeout"
            )
            raise RuntimeError(f"Command '{command}' timed out after 30 seconds")
        
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "terminal", "execute_command",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
```

### 5. Message User MCP Server

```python
# tools/mcp_servers/message_user.py

class MessageUserMCP:
    def __init__(self, permission_manager, user_interface):
        self.permissions = permission_manager
        self.user_interface = user_interface
        self.server = Server("message-user")
        self.register_tools()
    
    def register_tools(self):
        self.server.register_tool("send_message", self.send_message)
        self.server.register_tool("send_structured_message", self.send_structured_message)
    
    async def send_message(self, message: str, message_type: str = "info",
                          agent_type: str = None, task_id: int = None) -> bool:
        """Send simple message to user"""
        # Message user is a minimal permission tool - all agents can use it
        
        start_time = time.time()
        
        try:
            success = await self.user_interface.send_message(
                content=message,
                message_type=message_type,
                source_agent=agent_type,
                source_task=task_id
            )
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "message_user", "send_message",
                success, int((time.time() - start_time) * 1000),
                result_summary=f"Sent {len(message)} character message"
            )
            
            return success
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "message_user", "send_message",
                False, int((time.time() - start_time) * 1000),
                result_summary=str(e)
            )
            raise
    
    async def send_structured_message(self, title: str, content: str, 
                                    sections: List[Dict[str, str]] = None,
                                    agent_type: str = None, task_id: int = None) -> bool:
        """Send structured message with sections"""
        
        structured_content = {
            "title": title,
            "content": content,
            "sections": sections or [],
            "timestamp": time.time(),
            "source": {
                "agent_type": agent_type,
                "task_id": task_id
            }
        }
        
        try:
            success = await self.user_interface.send_structured_message(structured_content)
            
            await self.permissions.log_tool_usage(
                task_id, agent_type, "message_user", "send_structured_message",
                success, 0, result_summary="Sent structured message"
            )
            
            return success
            
        except Exception as e:
            await self.permissions.log_tool_usage(
                task_id, agent_type, "message_user", "send_structured_message",
                False, 0, result_summary=str(e)
            )
            raise
```

## Tool Assignment System

### Tool Addition Agent Integration

```python
# agents/tool_addition.py

class ToolAdditionAgent:
    def __init__(self, permission_manager):
        self.permissions = permission_manager
    
    async def analyze_tool_needs(self, task_instruction: str, current_tools: List[str],
                                task_context: Dict[str, Any]) -> List[ToolAssignment]:
        """Analyze task and determine what additional tools are needed"""
        
        assignments = []
        
        # Database analysis needs
        if any(keyword in task_instruction.lower() 
               for keyword in ["analyze", "performance", "events", "history"]):
            if "sql_lite" not in current_tools:
                assignments.append(ToolAssignment(
                    tool_name="sql_lite",
                    assignment_reason="Task requires database analysis",
                    duration_hours=24,
                    specific_permissions={
                        "allowed_queries": ["get_recent_events", "get_agent_performance"]
                    }
                ))
        
        # File system needs
        if any(keyword in task_instruction.lower() 
               for keyword in ["file", "document", "code", "edit"]):
            if "file_system_listing" not in current_tools:
                assignments.append(ToolAssignment(
                    tool_name="file_system_listing",
                    assignment_reason="Task requires file system access",
                    duration_hours=12
                ))
            
            # Check if editing is needed
            if any(keyword in task_instruction.lower() 
                   for keyword in ["edit", "modify", "create", "write"]):
                if "file_edit" not in current_tools:
                    assignments.append(ToolAssignment(
                        tool_name="file_edit",
                        assignment_reason="Task requires file modification",
                        duration_hours=8
                    ))
        
        # Git operations
        if any(keyword in task_instruction.lower() 
               for keyword in ["git", "commit", "repository", "branch"]):
            if "github" not in current_tools:
                assignments.append(ToolAssignment(
                    tool_name="github",
                    assignment_reason="Task requires git operations",
                    duration_hours=48
                ))
        
        # System operations
        if any(keyword in task_instruction.lower() 
               for keyword in ["system", "process", "debug", "diagnose"]):
            if "terminal" not in current_tools:
                assignments.append(ToolAssignment(
                    tool_name="terminal",
                    assignment_reason="Task requires system diagnosis",
                    duration_hours=6
                ))
        
        return assignments
    
    async def implement_tool_assignments(self, task_id: int, assignments: List[ToolAssignment],
                                       assigning_task_id: int) -> Dict[str, Any]:
        """Implement the tool assignments in database"""
        
        implemented = []
        failed = []
        
        for assignment in assignments:
            try:
                success = await self.permissions.assign_tool_to_task(
                    task_id=task_id,
                    tool_assignment=assignment,
                    assigned_by=assigning_task_id
                )
                
                if success:
                    implemented.append(assignment.tool_name)
                else:
                    failed.append(assignment.tool_name)
                    
            except Exception as e:
                failed.append(f"{assignment.tool_name}: {str(e)}")
        
        return {
            "implemented_tools": implemented,
            "failed_tools": failed,
            "total_assigned": len(implemented)
        }
```

## System Integration

### MCP Server Startup

```python
# tools/startup.py

class ToolSystemManager:
    def __init__(self, db_connection, config):
        self.db = db_connection
        self.config = config
        self.permission_manager = DatabasePermissionManager(db_connection)
        self.mcp_servers = {}
    
    async def start_mcp_servers(self):
        """Start all MCP servers with permission integration"""
        
        # Entity Manager (core system)
        entity_server = EntityManagerMCP(self.db, self.permission_manager)
        self.mcp_servers["entity_manager"] = entity_server
        
        # File System
        file_server = FileSystemMCP(
            allowed_paths=self.config.get("allowed_file_paths", ["/project"]),
            permission_manager=self.permission_manager
        )
        self.mcp_servers["file_system"] = file_server
        
        # SQL Lite
        sql_server = SQLiteMCP(self.db, self.permission_manager)
        self.mcp_servers["sql_lite"] = sql_server
        
        # Terminal
        terminal_server = TerminalMCP(self.permission_manager)
        self.mcp_servers["terminal"] = terminal_server
        
        # Message User
        message_server = MessageUserMCP(
            self.permission_manager, 
            self.config.get("user_interface")
        )
        self.mcp_servers["message_user"] = message_server
        
        # Start all servers
        for name, server in self.mcp_servers.items():
            await server.start()
            print(f"Started MCP server: {name}")
    
    async def get_agent_tools(self, agent_type: str, task_id: int = None) -> List[str]:
        """Get list of MCP server URLs for agent"""
        permissions = await self.permission_manager.get_agent_permissions(agent_type, task_id)
        
        server_urls = []
        for tool_name in permissions.tools:
            if tool_name in self.mcp_servers:
                server_urls.append(self.mcp_servers[tool_name].get_url())
        
        return server_urls
    
    async def cleanup_expired_permissions(self):
        """Background task to clean up expired permissions"""
        while True:
            try:
                await self.permission_manager.cleanup_expired_assignments()
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                print(f"Error cleaning up permissions: {e}")
                await asyncio.sleep(60)
```

## Usage Examples

### Tool Assignment Flow

```python
# Example: Agent requests additional tools during task execution

# 1. Agent calls need_more_tools() in their task
agent_response = {
    "tool_calls": [{
        "name": "need_more_tools",
        "arguments": {
            "tool_request": "database analysis capabilities",
            "justification": "Need to analyze recent system events to understand performance patterns"
        }
    }]
}

# 2. Runtime triggers need_more_tools_process
process_result = await process_engine.execute_process(
    "need_more_tools_process",
    requesting_task_id=current_task_id,
    tool_request="database analysis capabilities",
    justification="Need to analyze recent system events"
)

# 3. Tool Addition Agent analyzes and assigns tools
tool_assignments = await tool_addition_agent.analyze_tool_needs(
    task_instruction=current_task.instruction,
    current_tools=current_task.available_tools
)

# 4. Database updated with new permissions
for assignment in tool_assignments:
    await permission_manager.assign_tool_to_task(
        task_id=current_task_id,
        tool_assignment=assignment,
        assigned_by=tool_addition_task_id
    )

# 5. Agent can now use additional tools
new_permissions = await permission_manager.get_agent_permissions(
    agent_type="investigator_agent",
    task_id=current_task_id
)
# new_permissions.tools now includes "sql_lite"
```

### Tool Usage with Permission Checking

```python
# Example: Agent uses SQL tool with permission verification

# Agent makes tool call
tool_response = await mcp_client.call_tool("sql_lite", "execute_query", {
    "query_name": "get_recent_events",
    "parameters": [time.time() - 86400, 50],  # Last 24 hours, limit 50
    "agent_type": "investigator_agent",
    "task_id": current_task_id
})

# MCP server checks permissions before execution
# 1. Verify agent has sql_lite tool assigned
# 2. Check query-specific permissions
# 3. Execute query and log usage
# 4. Return results

# Usage automatically logged for optimization
tool_usage_logged = {
    "task_id": current_task_id,
    "agent_type": "investigator_agent", 
    "tool_name": "sql_lite",
    "operation": "query_get_recent_events",
    "success": True,
    "execution_time_ms": 45
}
```

This implementation provides a secure, auditable, and optimizable tool system that grows with your MVP while maintaining clear permission boundaries and comprehensive usage tracking.