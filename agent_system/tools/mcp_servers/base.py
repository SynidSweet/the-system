"""Base MCP Server implementation for tool servers."""

import asyncio
import json
import logging
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod
import time

from ...core.permissions.manager import DatabasePermissionManager

logger = logging.getLogger(__name__)


class MCPToolError(Exception):
    """Base exception for MCP tool errors."""
    pass


class PermissionError(MCPToolError):
    """Raised when permission check fails."""
    pass


class MCPServer(ABC):
    """Base class for MCP server implementations."""
    
    def __init__(self, server_name: str, permission_manager: DatabasePermissionManager):
        self.server_name = server_name
        self.permission_manager = permission_manager
        self.tools: Dict[str, Callable] = {}
        self.is_running = False
        
    @abstractmethod
    def register_tools(self):
        """Register all tools provided by this server."""
        pass
    
    def register_tool(self, tool_name: str, handler: Callable):
        """Register a tool handler."""
        self.tools[tool_name] = handler
        logger.info(f"Registered tool '{tool_name}' on server '{self.server_name}'")
    
    async def start(self):
        """Start the MCP server."""
        self.register_tools()
        self.is_running = True
        logger.info(f"MCP server '{self.server_name}' started with {len(self.tools)} tools")
    
    async def stop(self):
        """Stop the MCP server."""
        self.is_running = False
        logger.info(f"MCP server '{self.server_name}' stopped")
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], 
                       agent_type: str, task_id: int) -> Dict[str, Any]:
        """Call a tool with permission checking and usage tracking."""
        if not self.is_running:
            raise MCPToolError(f"Server '{self.server_name}' is not running")
        
        if tool_name not in self.tools:
            raise MCPToolError(f"Tool '{tool_name}' not found on server '{self.server_name}'")
        
        # Check permissions
        has_permission = await self.permission_manager.check_tool_access(
            agent_type, task_id, self.server_name
        )
        
        if not has_permission:
            raise PermissionError(
                f"Agent type '{agent_type}' does not have access to '{self.server_name}'"
            )
        
        # Track execution
        start_time = time.time()
        success = False
        error_message = None
        result = None
        
        try:
            # Add agent context to parameters
            parameters['agent_type'] = agent_type
            parameters['task_id'] = task_id
            
            # Execute tool
            handler = self.tools[tool_name]
            result = await handler(**parameters)
            success = True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Tool execution failed: {tool_name} - {error_message}")
            raise
        
        finally:
            # Log usage
            execution_time = int((time.time() - start_time) * 1000)
            await self.permission_manager.log_tool_usage(
                task_id=task_id,
                agent_type=agent_type,
                tool_name=self.server_name,
                operation=tool_name,
                success=success,
                execution_time_ms=execution_time,
                parameters_hash=self.permission_manager.hash_parameters(parameters),
                result_summary=str(result)[:200] if result else None,
                error_message=error_message
            )
        
        return result
    
    def list_tools(self) -> List[str]:
        """List available tools on this server."""
        return list(self.tools.keys())
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": self.server_name,
            "status": "running" if self.is_running else "stopped",
            "tools": self.list_tools(),
            "tool_count": len(self.tools)
        }


class MCPServerRegistry:
    """Registry for managing multiple MCP servers."""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        
    async def register_server(self, server: MCPServer):
        """Register an MCP server."""
        if server.server_name in self.servers:
            raise ValueError(f"Server '{server.server_name}' already registered")
        
        self.servers[server.server_name] = server
        await server.start()
        
    async def unregister_server(self, server_name: str):
        """Unregister an MCP server."""
        if server_name in self.servers:
            await self.servers[server_name].stop()
            del self.servers[server_name]
    
    async def call_tool(self, server_name: str, tool_name: str, 
                       parameters: Dict[str, Any], agent_type: str, task_id: int) -> Dict[str, Any]:
        """Call a tool on a specific server."""
        if server_name not in self.servers:
            raise MCPToolError(f"Server '{server_name}' not found")
        
        return await self.servers[server_name].call_tool(
            tool_name, parameters, agent_type, task_id
        )
    
    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """Get a specific server."""
        return self.servers.get(server_name)
    
    def list_servers(self) -> List[str]:
        """List registered server names."""
        return list(self.servers.keys())
    
    def get_all_tools(self) -> Dict[str, List[str]]:
        """Get all tools organized by server."""
        return {
            server_name: server.list_tools()
            for server_name, server in self.servers.items()
        }
    
    async def start_all(self):
        """Start all registered servers."""
        for server in self.servers.values():
            if not server.is_running:
                await server.start()
    
    async def stop_all(self):
        """Stop all registered servers."""
        for server in self.servers.values():
            if server.is_running:
                await server.stop()


# Global registry instance
_mcp_registry: Optional[MCPServerRegistry] = None


def get_mcp_registry() -> MCPServerRegistry:
    """Get or create the global MCP server registry."""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPServerRegistry()
    return _mcp_registry