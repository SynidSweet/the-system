"""Tool System Manager - Manages MCP servers and tool permissions."""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from agent_system.core.database_manager import DatabaseManager
from agent_system.core.entities.entity_manager import EntityManager
from agent_system.core.permissions.manager import DatabasePermissionManager, get_permission_manager
from agent_system.tools.mcp_servers.base import get_mcp_registry, MCPServerRegistry
from agent_system.tools.mcp_servers.entity_manager import EntityManagerMCP
from agent_system.tools.mcp_servers.message_user import MessageUserMCP, UserInterface
from agent_system.tools.mcp_servers.file_system import FileSystemMCPServer
from agent_system.tools.mcp_servers.sql_lite import SQLiteMCPServer
from agent_system.tools.mcp_servers.terminal import TerminalMCPServer
from agent_system.tools.mcp_servers.github import GitHubMCPServer

logger = logging.getLogger(__name__)


class ToolSystemManager:
    """Manages the tool system including MCP servers and permissions."""
    
    def __init__(self, db_manager: DatabaseManager, entity_manager: EntityManager, config: Dict[str, Any]):
        self.db_manager = db_manager
        self.entity_manager = entity_manager
        self.config = config
        self.permission_manager = get_permission_manager(db_manager)
        self.mcp_registry = get_mcp_registry()
        self.user_interface = UserInterface()
        self._cleanup_task = None
        
    async def start_mcp_servers(self):
        """Start all MCP servers with permission integration."""
        logger.info("Starting MCP servers...")
        
        # Entity Manager (core system)
        entity_server = EntityManagerMCP(self.entity_manager, self.permission_manager)
        await self.mcp_registry.register_server(entity_server)
        
        # Message User
        message_server = MessageUserMCP(self.permission_manager, self.user_interface)
        await self.mcp_registry.register_server(message_server)
        
        # File System
        allowed_paths = self.config.get("allowed_file_paths", ["/code/personal/the-system"])
        if allowed_paths:
            file_server = FileSystemMCPServer(
                permission_manager=self.permission_manager,
                allowed_paths=allowed_paths
            )
            await self.mcp_registry.register_server(file_server)
        
        # SQL Lite
        sql_server = SQLiteMCPServer(
            permission_manager=self.permission_manager,
            db_path="/code/personal/the-system/data/agent_system.db",
            read_only=True,
            max_results=1000
        )
        await self.mcp_registry.register_server(sql_server)
        
        # Terminal
        terminal_server = TerminalMCPServer(
            permission_manager=self.permission_manager,
            allowed_directories=self.config.get("allowed_file_paths", ["/code/personal/the-system"]),
            command_whitelist=None,  # Use default whitelist
            max_output_size=1024 * 1024,  # 1MB
            default_timeout=30
        )
        await self.mcp_registry.register_server(terminal_server)
        
        # GitHub
        repo_path = self.config.get("github", {}).get("repo_path", "/code/personal/the-system")
        if repo_path:
            try:
                github_server = GitHubMCPServer(
                    permission_manager=self.permission_manager,
                    repo_path=repo_path,
                    allow_push=self.config.get("github", {}).get("allow_push", False),
                    protected_branches=self.config.get("github", {}).get("protected_branches", ["main", "master"])
                )
                await self.mcp_registry.register_server(github_server)
            except ValueError as e:
                logger.warning(f"Could not initialize GitHub MCP server: {e}")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info(f"Started {len(self.mcp_registry.servers)} MCP servers")
        
    async def stop_mcp_servers(self):
        """Stop all MCP servers."""
        logger.info("Stopping MCP servers...")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Stop all servers
        await self.mcp_registry.stop_all()
        
        logger.info("All MCP servers stopped")
    
    async def get_agent_tools(self, agent_type: str, task_id: int = None) -> List[str]:
        """Get list of available tools for an agent."""
        permissions = await self.permission_manager.get_agent_permissions(agent_type, task_id)
        
        # Filter to only include registered MCP servers
        available_tools = []
        for tool_name in permissions.tools:
            if self.mcp_registry.get_server(tool_name):
                available_tools.append(tool_name)
        
        return available_tools
    
    async def call_tool(self, tool_name: str, operation: str, parameters: Dict[str, Any],
                       agent_type: str, task_id: int) -> Dict[str, Any]:
        """Call a tool operation through the appropriate MCP server."""
        # Check if tool is available
        available_tools = await self.get_agent_tools(agent_type, task_id)
        if tool_name not in available_tools:
            raise PermissionError(f"Tool '{tool_name}' not available for agent type '{agent_type}'")
        
        # Call through MCP registry
        return await self.mcp_registry.call_tool(
            server_name=tool_name,
            tool_name=operation,
            parameters=parameters,
            agent_type=agent_type,
            task_id=task_id
        )
    
    async def _periodic_cleanup(self):
        """Background task to clean up expired permissions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.permission_manager.cleanup_expired_assignments()
                logger.info("Cleaned up expired tool permissions")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error cleaning up permissions: {e}")
                await asyncio.sleep(60)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get tool system status."""
        return {
            "mcp_servers": {
                server_name: server.get_server_info()
                for server_name, server in self.mcp_registry.servers.items()
            },
            "total_servers": len(self.mcp_registry.servers),
            "all_tools": self.mcp_registry.get_all_tools()
        }


# Global tool system manager
_tool_system_manager: Optional[ToolSystemManager] = None


async def initialize_tool_system(db_manager: DatabaseManager, entity_manager: EntityManager, 
                               config: Dict[str, Any]) -> ToolSystemManager:
    """Initialize the global tool system."""
    global _tool_system_manager
    
    if _tool_system_manager is None:
        _tool_system_manager = ToolSystemManager(db_manager, entity_manager, config)
        await _tool_system_manager.start_mcp_servers()
    
    return _tool_system_manager


def get_tool_system_manager() -> Optional[ToolSystemManager]:
    """Get the current tool system manager."""
    return _tool_system_manager


async def shutdown_tool_system():
    """Shutdown the tool system."""
    global _tool_system_manager
    
    if _tool_system_manager:
        await _tool_system_manager.stop_mcp_servers()
        _tool_system_manager = None