"""
Tool-specific models for MCP tool system.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class MCPToolCall(BaseModel):
    """Represents a call to an MCP tool"""
    tool_name: str
    arguments: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class MCPToolResult(BaseModel):
    """Represents the result of an MCP tool call"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class ToolImplementation(BaseModel):
    """Represents a tool implementation"""
    name: str
    description: str
    parameters: Dict[str, Any]
    implementation_type: str = "mcp"  # mcp, internal, external
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)