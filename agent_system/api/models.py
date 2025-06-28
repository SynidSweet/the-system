"""
API models for request/response handling.

These models serve as the interface between the HTTP API and the internal entity system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Status of a task in the system"""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_SUBTASKS = "waiting_for_subtasks"
    BLOCKED = "blocked"


class TaskSubmission(BaseModel):
    """Model for submitting a new task"""
    instruction: str = Field(..., description="The task instruction to execute")
    agent_type: Optional[str] = Field(None, description="Specific agent type to use")
    priority: Optional[int] = Field(1, ge=1, le=10, description="Task priority (1-10)")
    max_execution_time: Optional[int] = Field(None, description="Maximum execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """Response model for task submission"""
    task_id: str = Field(..., description="Unique task identifier")
    tree_id: str = Field(..., description="Task tree identifier")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="Task creation timestamp")
    instruction: str = Field(..., description="The task instruction")
    agent_type: Optional[str] = Field(None, description="Assigned agent type")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task metadata")


class TaskUpdate(BaseModel):
    """Model for task updates via WebSocket"""
    task_id: str
    tree_id: str
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SystemHealth(BaseModel):
    """System health check response"""
    status: str = Field(..., description="System status")
    version: str = Field(..., description="System version")
    services: Dict[str, bool] = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")


class AgentInfo(BaseModel):
    """Information about an agent"""
    id: str
    name: str
    type: str
    status: str
    capabilities: List[str]
    metadata: Optional[Dict[str, Any]] = None


class TaskTreeResponse(BaseModel):
    """Response model for task tree visualization"""
    tree_id: str
    root_task_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    tree_data: Dict[str, Any]  # Hierarchical tree structure