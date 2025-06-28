"""
Terminal MCP Server - Provides controlled command execution with whitelisting.

This server implements secure terminal access with:
- Command whitelisting and validation
- Working directory restrictions
- Output limiting and timeout controls
- Environment variable filtering
"""

import asyncio
import os
import shlex
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from .base import MCPServer
from core.permissions.manager import DatabasePermissionManager


class TerminalMCPServer(MCPServer):
    """
    MCP server for terminal command execution with security controls.
    
    Operations:
    - execute_command: Run a whitelisted command
    - list_files: List files in working directory
    - change_directory: Change working directory (restricted)
    - get_environment: Get filtered environment variables
    - check_command: Validate if a command is allowed
    """
    
    # Default whitelisted commands and patterns
    DEFAULT_WHITELIST = {
        # File operations
        "ls", "dir", "pwd", "find", "tree",
        
        # Text processing
        "cat", "head", "tail", "grep", "sed", "awk", "wc",
        "sort", "uniq", "cut", "tr",
        
        # Archive operations
        "tar", "zip", "unzip", "gzip", "gunzip",
        
        # Development tools
        "git", "npm", "yarn", "pip", "python", "node",
        "make", "cmake", "gcc", "g++",
        
        # System info
        "date", "whoami", "hostname", "uname", "which",
        "df", "du", "free",
        
        # Network tools (read-only)
        "ping", "curl", "wget", "host", "dig", "nslookup"
    }
    
    # Dangerous commands that are always blocked
    BLACKLIST = {
        "rm", "rmdir", "del", "format", "fdisk",
        "sudo", "su", "chmod", "chown", "kill", "pkill",
        "reboot", "shutdown", "halt", "poweroff",
        "systemctl", "service", "docker", "kubectl",
        "nc", "netcat", "telnet", "ssh", "scp"
    }
    
    def __init__(
        self,
        permission_manager: DatabasePermissionManager,
        allowed_directories: List[str],
        command_whitelist: Optional[Set[str]] = None,
        max_output_size: int = 1024 * 1024,  # 1MB
        default_timeout: int = 30  # seconds
    ):
        super().__init__("terminal", permission_manager)
        
        # Set allowed directories
        self.allowed_directories = []
        for path in allowed_directories:
            abs_path = Path(path).resolve()
            if abs_path.exists():
                self.allowed_directories.append(abs_path)
        
        if not self.allowed_directories:
            raise ValueError("No valid allowed directories configured")
        
        # Set command whitelist
        self.command_whitelist = command_whitelist or self.DEFAULT_WHITELIST.copy()
        
        # Ensure blacklisted commands are not in whitelist
        self.command_whitelist = self.command_whitelist - self.BLACKLIST
        
        # Configuration
        self.max_output_size = max_output_size
        self.default_timeout = default_timeout
        
        # Current working directory (starts at first allowed directory)
        self.current_directory = self.allowed_directories[0]
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories."""
        try:
            abs_path = path.resolve()
            for allowed_path in self.allowed_directories:
                try:
                    abs_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    def _validate_command(self, command: str) -> tuple[str, List[str]]:
        """Validate and parse a command."""
        # Parse command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")
        
        if not parts:
            raise ValueError("Empty command")
        
        cmd_name = parts[0]
        cmd_args = parts[1:]
        
        # Check if command is in whitelist
        base_cmd = os.path.basename(cmd_name)
        if base_cmd not in self.command_whitelist:
            raise PermissionError(
                f"Command '{base_cmd}' is not allowed. "
                f"Use 'check_command' to see allowed commands."
            )
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "&&", "||", ";", "|", ">", "<", ">>", "<<",
            "`", "$(", "${", "eval", "exec"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command:
                raise PermissionError(
                    f"Command contains forbidden pattern: {pattern}"
                )
        
        # Additional validation for specific commands
        if base_cmd == "find":
            # Restrict find to prevent -exec
            if "-exec" in cmd_args or "-execdir" in cmd_args:
                raise PermissionError("find with -exec is not allowed")
        
        if base_cmd in ["python", "node", "ruby", "perl"]:
            # Restrict scripting languages to file execution only
            if not cmd_args or not Path(cmd_args[0]).exists():
                raise PermissionError(
                    f"{base_cmd} must be used with an existing script file"
                )
        
        return cmd_name, cmd_args
    
    def _filter_environment(self) -> Dict[str, str]:
        """Get filtered environment variables."""
        # Only include safe environment variables
        safe_vars = {
            "PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL",
            "TERM", "COLUMNS", "LINES", "PWD", "OLDPWD"
        }
        
        filtered_env = {}
        for var in safe_vars:
            if var in os.environ:
                filtered_env[var] = os.environ[var]
        
        # Override PWD to current directory
        filtered_env["PWD"] = str(self.current_directory)
        
        return filtered_env
    
    async def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_directory: Optional[str] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Execute a whitelisted command."""
        try:
            # Validate command
            cmd_name, cmd_args = self._validate_command(command)
            
            # Determine working directory
            if working_directory:
                work_dir = Path(working_directory).resolve()
                if not self._is_path_allowed(work_dir):
                    raise PermissionError(
                        f"Working directory outside allowed paths: {working_directory}"
                    )
            else:
                work_dir = self.current_directory
            
            # Set timeout
            timeout = timeout or self.default_timeout
            
            # Prepare environment
            env = self._filter_environment()
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                cmd_name,
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
                env=env
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command,
                    "timeout": True
                }
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Limit output size
            if len(stdout_text) > self.max_output_size:
                stdout_text = stdout_text[:self.max_output_size] + "\n... (output truncated)"
            
            if len(stderr_text) > self.max_output_size:
                stderr_text = stderr_text[:self.max_output_size] + "\n... (output truncated)"
            
            return {
                "success": process.returncode == 0,
                "command": command,
                "working_directory": str(work_dir),
                "exit_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def list_files(
        self,
        path: Optional[str] = None,
        show_hidden: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """List files in a directory."""
        try:
            # Determine target path
            if path:
                target_path = Path(path).resolve()
                if not self._is_path_allowed(target_path):
                    raise PermissionError(f"Path outside allowed directories: {path}")
            else:
                target_path = self.current_directory
            
            if not target_path.is_dir():
                raise ValueError(f"Not a directory: {target_path}")
            
            # List files
            files = []
            for item in sorted(target_path.iterdir()):
                # Skip hidden files unless requested
                if item.name.startswith('.') and not show_hidden:
                    continue
                
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })
            
            return {
                "success": True,
                "path": str(target_path),
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def change_directory(
        self,
        path: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Change the current working directory."""
        try:
            # Resolve target path
            if path.startswith('/'):
                target_path = Path(path).resolve()
            else:
                target_path = (self.current_directory / path).resolve()
            
            # Check if allowed
            if not self._is_path_allowed(target_path):
                raise PermissionError(f"Path outside allowed directories: {path}")
            
            if not target_path.is_dir():
                raise ValueError(f"Not a directory: {target_path}")
            
            # Change directory
            old_dir = self.current_directory
            self.current_directory = target_path
            
            return {
                "success": True,
                "old_directory": str(old_dir),
                "new_directory": str(self.current_directory)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_environment(
        self,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get filtered environment variables."""
        try:
            env = self._filter_environment()
            
            return {
                "success": True,
                "environment": env,
                "current_directory": str(self.current_directory),
                "allowed_directories": [str(d) for d in self.allowed_directories]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_command(
        self,
        command: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Check if a command is allowed without executing it."""
        try:
            # Try to validate the command
            cmd_name, cmd_args = self._validate_command(command)
            
            return {
                "success": True,
                "allowed": True,
                "command": cmd_name,
                "arguments": cmd_args,
                "message": "Command is allowed"
            }
            
        except PermissionError as e:
            return {
                "success": True,
                "allowed": False,
                "error": str(e),
                "whitelisted_commands": sorted(list(self.command_whitelist))
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def register_tools(self):
        """Register terminal tools."""
        self.register_tool("execute_command", self.execute_command)
        self.register_tool("list_allowed_commands", self.list_allowed_commands)
        self.register_tool("get_working_directory", self.get_working_directory)
        self.register_tool("change_directory", self.change_directory)
    
    async def list_allowed_commands(self, agent_type: str = None, task_id: int = None) -> List[str]:
        """List all allowed commands."""
        return sorted(list(self.command_whitelist))
    
    async def get_working_directory(self, agent_type: str = None, task_id: int = None) -> str:
        """Get current working directory."""
        return str(self.current_directory)
    
    @property
    def name(self) -> str:
        """Return the server name."""
        return "terminal"
    
    @property
    def supported_operations(self) -> List[str]:
        """Return list of supported operations."""
        return [
            "execute_command",
            "list_files",
            "change_directory",
            "get_environment",
            "check_command"
        ]