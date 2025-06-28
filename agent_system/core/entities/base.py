"""Base Entity classes for the entity-based architecture."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json

from ..events.event_types import EntityType, EventType
from ..events.event_manager import EventManager


class EntityState(str, Enum):
    """Common entity states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    FAILED = "failed"


class Entity(ABC):
    """Abstract base class for all entities in the system."""
    
    def __init__(
        self,
        entity_id: int,
        name: str,
        entity_type: EntityType,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.entity_id = entity_id
        self.name = name
        self.entity_type = entity_type
        self.version = version
        self.state = state
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # Relationships
        self.relationships: Dict[str, List[int]] = {}
        
        # Event manager for tracking
        self.event_manager: Optional[EventManager] = None
    
    @abstractmethod
    async def validate(self) -> bool:
        """Validate entity configuration and state."""
        pass
    
    @abstractmethod
    async def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        base_dict = {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "version": self.version,
            "state": self.state.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "relationships": self.relationships
        }
        return base_dict
    
    @classmethod
    @abstractmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create entity from dictionary representation."""
        pass
    
    async def add_relationship(
        self,
        relationship_type: str,
        target_entity_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a relationship to another entity."""
        if relationship_type not in self.relationships:
            self.relationships[relationship_type] = []
        
        if target_entity_id not in self.relationships[relationship_type]:
            self.relationships[relationship_type].append(target_entity_id)
            
            # Log relationship creation event
            if self.event_manager:
                await self.event_manager.log_event(
                    EventType.RELATIONSHIP_CREATED,
                    self.entity_type,
                    self.entity_id,
                    target_entity_type=EntityType.UNKNOWN,
                    target_entity_id=target_entity_id,
                    relationship_type=relationship_type,
                    metadata=metadata
                )
            
            return True
        return False
    
    async def remove_relationship(
        self,
        relationship_type: str,
        target_entity_id: int
    ) -> bool:
        """Remove a relationship to another entity."""
        if relationship_type in self.relationships:
            if target_entity_id in self.relationships[relationship_type]:
                self.relationships[relationship_type].remove(target_entity_id)
                
                # Log relationship removal event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.RELATIONSHIP_REMOVED,
                        self.entity_type,
                        self.entity_id,
                        target_entity_id=target_entity_id,
                        relationship_type=relationship_type
                    )
                
                return True
        return False
    
    async def update_state(self, new_state: EntityState) -> bool:
        """Update entity state with event logging."""
        old_state = self.state
        self.state = new_state
        self.updated_at = datetime.now()
        
        # Log state change event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_UPDATED,
                self.entity_type,
                self.entity_id,
                old_state=old_state.value,
                new_state=new_state.value
            )
        
        return True
    
    async def update_metadata(self, key: str, value: Any) -> bool:
        """Update entity metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.now()
        
        # Log metadata update
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_UPDATED,
                self.entity_type,
                self.entity_id,
                metadata_key=key,
                metadata_value=value
            )
        
        return True
    
    def get_relationships(self, relationship_type: Optional[str] = None) -> Dict[str, List[int]]:
        """Get relationships, optionally filtered by type."""
        if relationship_type:
            return {relationship_type: self.relationships.get(relationship_type, [])}
        return self.relationships
    
    def has_relationship(self, relationship_type: str, target_entity_id: int) -> bool:
        """Check if entity has a specific relationship."""
        return (
            relationship_type in self.relationships and
            target_entity_id in self.relationships[relationship_type]
        )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.entity_id}, name='{self.name}', state={self.state.value})>"