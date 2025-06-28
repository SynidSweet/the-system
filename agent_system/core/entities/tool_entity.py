"""Tool entity implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json

from .base import Entity, EntityState
from ..events.event_types import EntityType


class ToolCategory(str, Enum):
    """Tool categories."""
    CORE = "core"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    DEVELOPMENT = "development"
    RESEARCH = "research"
    SYSTEM = "system"
    EXTERNAL = "external"


class ToolEntity(Entity):
    """Entity representation of a tool."""
    
    def __init__(
        self,
        entity_id: int,
        name: str,
        description: str,
        category: ToolCategory,
        implementation: str,
        parameters: Optional[Dict[str, Any]] = None,
        permissions: Optional[List[str]] = None,
        requires_validation: bool = False,
        triggers_process: Optional[str] = None,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            entity_type=EntityType.TOOL,
            version=version,
            state=state,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.description = description
        self.category = category
        self.implementation = implementation
        self.parameters = parameters or {}
        self.permissions = permissions or []
        self.requires_validation = requires_validation
        self.triggers_process = triggers_process
        
        # Tool-specific tracking
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.average_execution_time = 0.0
    
    async def validate(self) -> bool:
        """Validate tool configuration."""
        # Basic validation
        if not self.name or not self.description or not self.implementation:
            return False
        
        # Validate category
        if not isinstance(self.category, ToolCategory):
            return False
        
        # Validate parameters schema if provided
        if self.parameters:
            required_keys = ["type", "properties"]
            if not all(key in self.parameters for key in required_keys):
                return False
        
        # Validate implementation format
        if self.implementation not in ["mcp", "internal", "process", "external"]:
            return False
        
        return True
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert tool entity to dictionary."""
        base_dict = await super().to_dict()
        base_dict.update({
            "description": self.description,
            "category": self.category.value,
            "implementation": self.implementation,
            "parameters": self.parameters,
            "permissions": self.permissions,
            "requires_validation": self.requires_validation,
            "triggers_process": self.triggers_process,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_execution_time": self.average_execution_time
        })
        return base_dict
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ToolEntity':
        """Create tool entity from dictionary."""
        entity = cls(
            entity_id=data["entity_id"],
            name=data["name"],
            description=data["description"],
            category=ToolCategory(data["category"]),
            implementation=data["implementation"],
            parameters=data.get("parameters", {}),
            permissions=data.get("permissions", []),
            requires_validation=data.get("requires_validation", False),
            triggers_process=data.get("triggers_process"),
            version=data.get("version", "1.0.0"),
            state=EntityState(data.get("state", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Restore relationships and stats
        entity.relationships = data.get("relationships", {})
        entity.execution_count = data.get("execution_count", 0)
        entity.success_count = data.get("success_count", 0)
        entity.failure_count = data.get("failure_count", 0)
        entity.average_execution_time = data.get("average_execution_time", 0.0)
        
        return entity
    
    async def record_execution(
        self,
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ) -> bool:
        """Record a tool execution for statistics."""
        self.execution_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update average execution time
        total_time = self.average_execution_time * (self.execution_count - 1)
        self.average_execution_time = (total_time + execution_time) / self.execution_count
        
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.TOOL_COMPLETED if success else EventType.TOOL_FAILED,
                EntityType.TOOL,
                self.entity_id,
                event_data={
                    "success": success,
                    "execution_time": execution_time,
                    "error": error
                }
            )
        
        return True
    
    async def update_implementation(self, new_implementation: str) -> bool:
        """Update the tool's implementation type."""
        old_implementation = self.implementation
        self.implementation = new_implementation
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EntityType.ENTITY_UPDATED,
                EntityType.TOOL,
                self.entity_id,
                update_type="implementation_changed",
                old_implementation=old_implementation,
                new_implementation=new_implementation
            )
        
        return True
    
    async def set_process_trigger(self, process_name: str) -> bool:
        """Set the process that this tool triggers."""
        self.triggers_process = process_name
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EntityType.ENTITY_UPDATED,
                EntityType.TOOL,
                self.entity_id,
                update_type="process_trigger_set",
                process_name=process_name
            )
        
        return True
    
    def get_success_rate(self) -> float:
        """Calculate the tool's success rate."""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    def get_failure_rate(self) -> float:
        """Calculate the tool's failure rate."""
        if self.execution_count == 0:
            return 0.0
        return self.failure_count / self.execution_count


# Fix missing import
from enum import Enum