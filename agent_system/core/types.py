"""
Common type definitions for the agent system.

This module provides TypedDict classes and type aliases to improve type safety
and code clarity throughout the system.
"""

from typing import TypedDict, Optional, List, Dict, Any, Union, Literal
from datetime import datetime

# Task-related types
class TaskMetadata(TypedDict, total=False):
    """Metadata associated with a task."""
    assigned_agent: str
    additional_context: List[str]
    additional_tools: List[str]
    agent_type: str
    execution_time_ms: int
    parent_task_id: Optional[int]
    tree_id: str
    priority: str

class TaskResult(TypedDict):
    """Result of a task execution."""
    success: bool
    result: Any
    error_message: Optional[str]
    metadata: Dict[str, Any]

# Agent-related types
class AgentPermissions(TypedDict, total=False):
    """Permissions for an agent."""
    web_search: bool
    file_system: bool
    shell_access: bool
    git_operations: bool
    database_write: bool
    spawn_agents: bool

class ModelConfig(TypedDict):
    """AI model configuration."""
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    api_key: Optional[str]

# Event-related types
class EventData(TypedDict, total=False):
    """Data associated with system events."""
    task_instruction: str
    agent_name: str
    error: str
    execution_time_ms: float
    outcome: str
    task_id: int
    agent_id: int
    tool_name: str

# Tool-related types
class ToolResult(TypedDict):
    """Result from tool execution."""
    tool: str
    success: bool
    result: Any
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    metadata: Dict[str, Any]

class ToolConfig(TypedDict):
    """Configuration for MCP tools."""
    name: str
    description: str
    category: str
    permissions: List[str]
    parameters: Dict[str, Any]

# Health check types
class HealthData(TypedDict, total=False):
    """Health check data structure."""
    active_agents: int
    database: str
    task_manager: Dict[str, int]
    running_agents: int
    queued_tasks: int
    system_status: str

# Knowledge system types
class KnowledgeGap(TypedDict):
    """Represents a gap in knowledge."""
    gap_type: str
    description: str
    priority: str
    suggested_resolution: str

class ContextPackage(TypedDict):
    """Assembled context for a task."""
    completeness_score: float
    knowledge_sources: List[str]
    domain: str
    missing_requirements: List[str]
    context_data: Dict[str, Any]

# Database query types
class QueryFilter(TypedDict, total=False):
    """Generic query filter for database operations."""
    status: str
    category: str
    name: str
    limit: int
    offset: int

# API response types
class APIResponse(TypedDict):
    """Standard API response format."""
    success: bool
    data: Any
    error: Optional[str]
    timestamp: str

class ErrorResponse(TypedDict):
    """Error response format."""
    error: str
    type: str
    code: str
    timestamp: str
    request_id: Optional[str]

# Entity status literals
TaskStatus = Literal["pending", "in_progress", "completed", "failed", "cancelled"]
AgentStatus = Literal["active", "deprecated", "testing", "disabled"]
EntityType = Literal["agent", "task", "tool", "context_document", "process", "event"]

# Common type aliases
EntityID = int
TaskTreeID = str
AgentName = str
ToolName = str
DocumentName = str
ProcessName = str