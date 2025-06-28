"""Process entity implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from ..entities.base import Entity, EntityState
from ..events.event_types import EntityType


class ProcessType(str, Enum):
    """Process types."""
    DEFAULT = "default"          # Neutral task process
    TOOL_TRIGGERED = "tool_triggered"  # Triggered by tool calls
    EVENT_TRIGGERED = "event_triggered"  # Triggered by events
    SYSTEM = "system"           # System maintenance processes
    RECOVERY = "recovery"       # Error recovery processes


class ProcessEntity(Entity):
    """Entity representation of a process."""
    
    def __init__(
        self,
        entity_id: int,
        name: str,
        description: str,
        process_type: ProcessType,
        implementation_path: str,
        parameters_schema: Optional[Dict[str, Any]] = None,
        triggers: Optional[List[str]] = None,
        required_tools: Optional[List[str]] = None,
        required_context: Optional[List[str]] = None,
        can_rollback: bool = False,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            entity_type=EntityType.PROCESS,
            version=version,
            state=state,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.description = description
        self.process_type = process_type
        self.implementation_path = implementation_path
        self.parameters_schema = parameters_schema or {}
        self.triggers = triggers or []
        self.required_tools = required_tools or []
        self.required_context = required_context or []
        self.can_rollback = can_rollback
        
        # Process-specific tracking
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.average_execution_time = 0.0
        self.rollback_count = 0
    
    async def validate(self) -> bool:
        """Validate process configuration."""
        # Basic validation
        if not self.name or not self.description or not self.implementation_path:
            return False
        
        # Validate process type
        if not isinstance(self.process_type, ProcessType):
            return False
        
        # Validate implementation path format
        if not self.implementation_path.endswith('.py'):
            return False
        
        # Validate triggers for tool-triggered processes
        if self.process_type == ProcessType.TOOL_TRIGGERED and not self.triggers:
            return False
        
        return True
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert process entity to dictionary."""
        base_dict = await super().to_dict()
        base_dict.update({
            "description": self.description,
            "process_type": self.process_type.value,
            "implementation_path": self.implementation_path,
            "parameters_schema": self.parameters_schema,
            "triggers": self.triggers,
            "required_tools": self.required_tools,
            "required_context": self.required_context,
            "can_rollback": self.can_rollback,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_execution_time": self.average_execution_time,
            "rollback_count": self.rollback_count
        })
        return base_dict
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ProcessEntity':
        """Create process entity from dictionary."""
        entity = cls(
            entity_id=data["entity_id"],
            name=data["name"],
            description=data["description"],
            process_type=ProcessType(data["process_type"]),
            implementation_path=data["implementation_path"],
            parameters_schema=data.get("parameters_schema", {}),
            triggers=data.get("triggers", []),
            required_tools=data.get("required_tools", []),
            required_context=data.get("required_context", []),
            can_rollback=data.get("can_rollback", False),
            version=data.get("version", "1.0.0"),
            state=EntityState(data.get("state", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Restore relationships and tracking
        entity.relationships = data.get("relationships", {})
        entity.execution_count = data.get("execution_count", 0)
        entity.success_count = data.get("success_count", 0)
        entity.failure_count = data.get("failure_count", 0)
        entity.average_execution_time = data.get("average_execution_time", 0.0)
        entity.rollback_count = data.get("rollback_count", 0)
        
        return entity
    
    async def record_execution(
        self,
        success: bool,
        execution_time: float,
        error: Optional[str] = None,
        rolled_back: bool = False
    ) -> bool:
        """Record a process execution for statistics."""
        self.execution_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        if rolled_back:
            self.rollback_count += 1
        
        # Update average execution time
        total_time = self.average_execution_time * (self.execution_count - 1)
        self.average_execution_time = (total_time + execution_time) / self.execution_count
        
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.PROCESS_EXECUTED,
                EntityType.PROCESS,
                self.entity_id,
                success=success,
                execution_time=execution_time,
                error=error,
                rolled_back=rolled_back
            )
        
        return True
    
    async def add_trigger(self, trigger: str) -> bool:
        """Add a trigger to this process."""
        if trigger not in self.triggers:
            self.triggers.append(trigger)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.PROCESS,
                    self.entity_id,
                    update_type="trigger_added",
                    trigger=trigger
                )
            
            return True
        return False
    
    async def remove_trigger(self, trigger: str) -> bool:
        """Remove a trigger from this process."""
        if trigger in self.triggers:
            self.triggers.remove(trigger)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.PROCESS,
                    self.entity_id,
                    update_type="trigger_removed",
                    trigger=trigger
                )
            
            return True
        return False
    
    async def update_implementation(self, new_path: str) -> bool:
        """Update the process implementation path."""
        old_path = self.implementation_path
        self.implementation_path = new_path
        self.updated_at = datetime.now()
        
        # Increment version for implementation changes
        version_parts = self.version.split('.')
        version_parts[1] = str(int(version_parts[1]) + 1)  # Minor version bump
        self.version = '.'.join(version_parts)
        
        if self.event_manager:
            await self.event_manager.log_event(
                EntityType.ENTITY_UPDATED,
                EntityType.PROCESS,
                self.entity_id,
                update_type="implementation_updated",
                old_path=old_path,
                new_path=new_path,
                version=self.version
            )
        
        return True
    
    def get_success_rate(self) -> float:
        """Calculate the process's success rate."""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    def get_rollback_rate(self) -> float:
        """Calculate the process's rollback rate."""
        if self.execution_count == 0:
            return 0.0
        return self.rollback_count / self.execution_count
    
    def is_triggered_by(self, trigger: str) -> bool:
        """Check if this process is triggered by a specific trigger."""
        return trigger in self.triggers