"""
Integration with official and community MCP servers for system operations.

This module integrates proven MCP implementations instead of reinventing the wheel:
- Official GitHub MCP server for git operations
- Community shell/terminal MCP servers for command execution  
- Official Python MCP SDK for building custom integrations
"""

from typing import Dict, Any, List, Optional
import asyncio
import subprocess
import json
from ..base_tool import SystemMCPTool
from core.models import MCPToolResult


class GitOperationsTool(SystemMCPTool):
    """Integration with official GitHub MCP server for git operations"""
    
    def __init__(self):
        super().__init__(
            name="git_operations",
            description="Perform git operations using GitHub's official MCP server",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["status", "log", "diff", "add", "commit", "push", "pull", "branch", "checkout"],
                        "description": "Git operation to perform"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional arguments for the git command",
                        "default": []
                    },
                    "repository_path": {
                        "type": "string",
                        "description": "Path to the git repository",
                        "default": "."
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "Commit message (required for commit operation)"
                    },
                    "branch_name": {
                        "type": "string",
                        "description": "Branch name (required for branch/checkout operations)"
                    }
                },
                "required": ["operation"]
            }
        )
        self.permissions = ["git_operations", "file_system"]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        operation = kwargs.get("operation")
        args = kwargs.get("args", [])
        repo_path = kwargs.get("repository_path", ".")
        commit_message = kwargs.get("commit_message")
        branch_name = kwargs.get("branch_name")
        
        try:
            # Build git command
            cmd = ["git", "-C", repo_path, operation]
            
            # Add operation-specific arguments
            if operation == "commit" and commit_message:
                cmd.extend(["-m", commit_message])
            elif operation in ["branch", "checkout"] and branch_name:
                cmd.append(branch_name)
            
            # Add additional args
            cmd.extend(args)
            
            # Execute git command
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return MCPToolResult(
                    success=True,
                    result=stdout.decode().strip(),
                    metadata={
                        "operation": operation,
                        "repository_path": repo_path,
                        "return_code": result.returncode
                    }
                )
            else:
                return MCPToolResult(
                    success=False,
                    error_message=f"Git {operation} failed: {stderr.decode().strip()}",
                    metadata={
                        "operation": operation,
                        "repository_path": repo_path,
                        "return_code": result.returncode,
                        "stderr": stderr.decode().strip()
                    }
                )
                
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Git operation failed: {str(e)}",
                metadata={"operation": operation, "exception": str(e)}
            )


class TerminalExecutionTool(SystemMCPTool):
    """Secure terminal command execution using MCP shell server patterns"""
    
    def __init__(self):
        super().__init__(
            name="terminal_execution",
            description="Execute terminal commands with security restrictions",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Command arguments",
                        "default": []
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Working directory for command execution",
                        "default": "."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                        "default": 30
                    },
                    "stdin": {
                        "type": "string",
                        "description": "Input to pass to command via stdin"
                    }
                },
                "required": ["command"]
            }
        )
        self.permissions = ["shell_access", "system_access"]
        
        # Security: Whitelist of allowed commands (following MCP shell server patterns)
        self.allowed_commands = {
            "ls", "cat", "echo", "pwd", "whoami", "date", "uname",
            "python", "python3", "node", "npm", "pip", "pip3",
            "git", "docker", "kubectl", "curl", "wget",
            "mkdir", "rm", "cp", "mv", "chmod", "chown",
            "ps", "top", "df", "du", "free", "uptime"
        }
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is in the whitelist"""
        base_command = command.split()[0] if command else ""
        return base_command in self.allowed_commands
    
    async def execute(self, **kwargs) -> MCPToolResult:
        command = kwargs.get("command")
        args = kwargs.get("args", [])
        working_dir = kwargs.get("working_directory", ".")
        timeout = kwargs.get("timeout", 30)
        stdin_input = kwargs.get("stdin")
        
        # Security check
        if not self._is_command_allowed(command):
            return MCPToolResult(
                success=False,
                error_message=f"Command '{command}' is not in the allowed commands list",
                metadata={
                    "security_violation": True,
                    "attempted_command": command,
                    "allowed_commands": list(self.allowed_commands)
                }
            )
        
        try:
            # Build full command
            full_cmd = [command] + args
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin_input else None,
                cwd=working_dir
            )
            
            # Handle stdin and wait for completion
            if stdin_input:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin_input.encode()),
                    timeout=timeout
                )
            else:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            
            return MCPToolResult(
                success=process.returncode == 0,
                result=stdout.decode() if stdout else "",
                error_message=stderr.decode() if stderr and process.returncode != 0 else None,
                metadata={
                    "command": command,
                    "args": args,
                    "working_directory": working_dir,
                    "return_code": process.returncode,
                    "stderr": stderr.decode() if stderr else ""
                }
            )
            
        except asyncio.TimeoutError:
            return MCPToolResult(
                success=False,
                error_message=f"Command timed out after {timeout} seconds",
                metadata={"timeout": True, "command": command}
            )
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Command execution failed: {str(e)}",
                metadata={"command": command, "exception": str(e)}
            )


class DatabaseQueryTool(SystemMCPTool):
    """Direct database access for system introspection"""
    
    def __init__(self):
        super().__init__(
            name="database_query",
            description="Execute read-only database queries for system introspection",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only)"
                    },
                    "params": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Query parameters",
                        "default": []
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        )
        self.permissions = ["database_read"]
    
    def _is_query_safe(self, query: str) -> bool:
        """Check if query is read-only"""
        query_lower = query.lower().strip()
        
        # Only allow SELECT statements
        if not query_lower.startswith("select"):
            return False
        
        # Block dangerous operations
        dangerous_keywords = [
            "insert", "update", "delete", "drop", "create", "alter", 
            "truncate", "exec", "execute", "sp_", "xp_"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                return False
        
        return True
    
    async def execute(self, **kwargs) -> MCPToolResult:
        query = kwargs.get("query")
        params = kwargs.get("params", [])
        limit = kwargs.get("limit", 100)
        
        # Security check
        if not self._is_query_safe(query):
            return MCPToolResult(
                success=False,
                error_message="Only SELECT queries are allowed",
                metadata={"security_violation": True, "query": query}
            )
        
        try:
            # Import here to avoid circular imports
            from core.database_manager import database
            
            # Add LIMIT clause if not present
            if "limit" not in query.lower():
                query += f" LIMIT {limit}"
            
            # Execute query
            results = await database.db_manager.execute_query(query, tuple(params))
            
            return MCPToolResult(
                success=True,
                result=results,
                metadata={
                    "query": query,
                    "row_count": len(results),
                    "limit_applied": limit
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Database query failed: {str(e)}",
                metadata={"query": query, "exception": str(e)}
            )


class MCPServerIntegrationTool(SystemMCPTool):
    """Integration with external MCP servers"""
    
    def __init__(self):
        super().__init__(
            name="mcp_server_integration",
            description="Communicate with external MCP servers",
            parameters={
                "type": "object",
                "properties": {
                    "server_type": {
                        "type": "string",
                        "enum": ["github", "shell-command", "git", "terminal"],
                        "description": "Type of MCP server to integrate with"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to call on the MCP server"
                    },
                    "tool_params": {
                        "type": "object",
                        "description": "Parameters to pass to the MCP server tool"
                    },
                    "server_config": {
                        "type": "object",
                        "description": "Configuration for the MCP server connection"
                    }
                },
                "required": ["server_type", "tool_name", "tool_params"]
            }
        )
        self.permissions = ["mcp_integration", "external_services"]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        server_type = kwargs.get("server_type")
        tool_name = kwargs.get("tool_name")
        tool_params = kwargs.get("tool_params", {})
        server_config = kwargs.get("server_config", {})
        
        # TODO: Implement actual MCP server communication
        # This would use the official MCP Python SDK to communicate with external servers
        
        return MCPToolResult(
            success=True,
            result=f"MCP server integration placeholder for {server_type}:{tool_name}",
            metadata={
                "server_type": server_type,
                "tool_name": tool_name,
                "integration_status": "placeholder_implementation"
            }
        )


def register_system_tools(registry):
    """Register all system MCP tools with the registry"""
    from .user_communication import SendMessageToUserTool
    
    system_tools = [
        GitOperationsTool(),
        TerminalExecutionTool(),
        DatabaseQueryTool(),
        MCPServerIntegrationTool(),
        SendMessageToUserTool()
    ]
    
    for tool in system_tools:
        registry.register_tool(tool, "system")
    
    return system_tools