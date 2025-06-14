"""Tool initialization and registration"""

from tools.base_tool import tool_registry
from tools.core_mcp.core_tools import (
    BreakDownTaskTool,
    StartSubtaskTool, 
    RequestContextTool,
    RequestToolsTool,
    EndTaskTool,
    FlagForReviewTool,
    ThinkOutLoudTool
)
from tools.system_tools.internal_tools import (
    ListAgentsTool,
    ListDocumentsTool,
    ListOptionalToolsTool,
    QueryDatabaseTool
)
from tools.system_tools.user_communication import SendMessageToUserTool


def initialize_tools():
    """Initialize and register all core and system tools"""
    
    # Register core MCP tools
    tool_registry.register_tool(BreakDownTaskTool(), "core")
    tool_registry.register_tool(StartSubtaskTool(), "core")
    tool_registry.register_tool(RequestContextTool(), "core")
    tool_registry.register_tool(RequestToolsTool(), "core")
    tool_registry.register_tool(EndTaskTool(), "core")
    tool_registry.register_tool(FlagForReviewTool(), "core")
    tool_registry.register_tool(ThinkOutLoudTool(), "core")
    
    # Register internal system tools
    tool_registry.register_tool(ListAgentsTool(), "system")
    tool_registry.register_tool(ListDocumentsTool(), "system")
    tool_registry.register_tool(ListOptionalToolsTool(), "system")
    tool_registry.register_tool(QueryDatabaseTool(), "system")
    
    # Register user communication tool
    tool_registry.register_tool(SendMessageToUserTool(), "system")
    
    print(f" Registered {len(tool_registry._tools)} tools")
    return tool_registry