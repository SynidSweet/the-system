from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time
from core.models import MCPToolCall, MCPToolResult, ToolImplementation


class BaseMCPTool(ABC):
    """Base class for all MCP tools in the agent system"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.permissions: List[str] = []
        self.timeout_seconds: int = 300
        self.retry_count: int = 0
    
    @abstractmethod
    async def execute(self, **kwargs) -> MCPToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters against schema"""
        # Basic validation - can be overridden for specific tools
        required_params = self.parameters.get('required', [])
        for param in required_params:
            if param not in kwargs:
                return False
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this tool"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    async def execute_with_timeout(self, **kwargs) -> MCPToolResult:
        """Execute tool with timeout and error handling"""
        start_time = time.time()
        
        try:
            # Validate parameters
            if not self.validate_parameters(**kwargs):
                return MCPToolResult(
                    success=False,
                    error_message=f"Invalid parameters for tool {self.name}",
                    metadata={"validation_failed": True}
                )
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.execute(**kwargs),
                timeout=self.timeout_seconds
            )
            
            # Add execution time to metadata
            execution_time = int((time.time() - start_time) * 1000)
            if result.metadata is None:
                result.metadata = {}
            result.metadata['execution_time_ms'] = execution_time
            
            return result
            
        except asyncio.TimeoutError:
            return MCPToolResult(
                success=False,
                error_message=f"Tool {self.name} timed out after {self.timeout_seconds} seconds",
                metadata={"timeout": True, "execution_time_ms": int((time.time() - start_time) * 1000)}
            )
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Tool {self.name} failed: {str(e)}",
                metadata={"exception": str(e), "execution_time_ms": int((time.time() - start_time) * 1000)}
            )


class CoreMCPTool(BaseMCPTool):
    """Base class for core MCP tools that all agents have access to"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        super().__init__(name, description, parameters)
        self.permissions = ["core_toolkit"]  # All agents have access to core tools


class SystemMCPTool(BaseMCPTool):
    """Base class for system tools that require special permissions"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        super().__init__(name, description, parameters)
        self.permissions = ["system_access"]  # Requires system permissions


class MCPToolRegistry:
    """Registry for managing all MCP tools in the system"""
    
    def __init__(self):
        self._tools: Dict[str, BaseMCPTool] = {}
        self._tool_categories: Dict[str, List[str]] = {
            "core": [],
            "system": [],
            "custom": []
        }
    
    def register_tool(self, tool: BaseMCPTool, category: str = "custom"):
        """Register a tool in the registry"""
        self._tools[tool.name] = tool
        
        if category not in self._tool_categories:
            self._tool_categories[category] = []
        self._tool_categories[category].append(tool.name)
    
    def get_tool(self, name: str) -> Optional[BaseMCPTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[BaseMCPTool]:
        """Get all tools in a category"""
        tool_names = self._tool_categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_available_tools(self, agent_permissions: List[str]) -> List[BaseMCPTool]:
        """Get tools available to an agent based on permissions"""
        available_tools = []
        
        for tool in self._tools.values():
            # Check if agent has required permissions for this tool
            has_permission = any(
                perm in agent_permissions 
                for perm in tool.permissions
            ) or not tool.permissions  # Tools with no permissions are available to all
            
            if has_permission:
                available_tools.append(tool)
        
        return available_tools
    
    def get_tool_schemas(self, agent_permissions: List[str] = None) -> List[Dict[str, Any]]:
        """Get schemas for all available tools"""
        if agent_permissions is None:
            tools = list(self._tools.values())
        else:
            tools = self.get_available_tools(agent_permissions)
        
        return [tool.get_schema() for tool in tools]
    
    async def execute_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Execute a tool call"""
        tool = self.get_tool(tool_call.tool_name)
        
        if not tool:
            return MCPToolResult(
                success=False,
                error_message=f"Tool '{tool_call.tool_name}' not found in registry"
            )
        
        return await tool.execute_with_timeout(**tool_call.parameters)
    
    def list_tools(self) -> Dict[str, List[str]]:
        """List all registered tools by category"""
        return dict(self._tool_categories)


# Global tool registry instance
tool_registry = MCPToolRegistry()