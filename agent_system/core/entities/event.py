"""Event entity implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime

from agent_system.core.entities.base import Entity, EntityState
from agent_system.core.events.event_types import EntityType, EventType, EventOutcome


class EventEntity(Entity):
    """Entity representation of an event."""
    
    def __init__(
        self,
        entity_id: int,
        event_type: EventType,
        primary_entity_type: EntityType,
        primary_entity_id: int,
        secondary_entity_type: Optional[EntityType] = None,
        secondary_entity_id: Optional[int] = None,
        outcome: EventOutcome = EventOutcome.SUCCESS,
        data: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Events use their event_type as name
        super().__init__(
            entity_id=entity_id,
            name=f"{event_type.value}_{entity_id}",
            entity_type=EntityType.EVENT,
            version=version,
            state=state,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.event_type = event_type
        self.primary_entity_type = primary_entity_type
        self.primary_entity_id = primary_entity_id
        self.secondary_entity_type = secondary_entity_type
        self.secondary_entity_id = secondary_entity_id
        self.outcome = outcome
        self.data = data or {}
        
        # Event-specific tracking
        self.analyzed = False
        self.patterns_detected: List[str] = []
        self.triggered_actions: List[str] = []
    
    async def validate(self) -> bool:
        """Validate event configuration."""
        # Basic validation
        if not isinstance(self.event_type, EventType):
            return False
        
        if not isinstance(self.primary_entity_type, EntityType):
            return False
        
        if not isinstance(self.outcome, EventOutcome):
            return False
        
        # Ensure primary entity ID is valid
        if self.primary_entity_id <= 0:
            return False
        
        return True
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert event entity to dictionary."""
        base_dict = await super().to_dict()
        base_dict.update({
            "event_type": self.event_type.value,
            "primary_entity_type": self.primary_entity_type.value,
            "primary_entity_id": self.primary_entity_id,
            "secondary_entity_type": self.secondary_entity_type.value if self.secondary_entity_type else None,
            "secondary_entity_id": self.secondary_entity_id,
            "outcome": self.outcome.value,
            "data": self.data,
            "analyzed": self.analyzed,
            "patterns_detected": self.patterns_detected,
            "triggered_actions": self.triggered_actions
        })
        return base_dict
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'EventEntity':
        """Create event entity from dictionary."""
        entity = cls(
            entity_id=data["entity_id"],
            event_type=EventType(data["event_type"]),
            primary_entity_type=EntityType(data["primary_entity_type"]),
            primary_entity_id=data["primary_entity_id"],
            secondary_entity_type=EntityType(data["secondary_entity_type"]) if data.get("secondary_entity_type") else None,
            secondary_entity_id=data.get("secondary_entity_id"),
            outcome=EventOutcome(data.get("outcome", "success")),
            data=data.get("data", {}),
            version=data.get("version", "1.0.0"),
            state=EntityState(data.get("state", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Restore relationships and tracking
        entity.relationships = data.get("relationships", {})
        entity.analyzed = data.get("analyzed", False)
        entity.patterns_detected = data.get("patterns_detected", [])
        entity.triggered_actions = data.get("triggered_actions", [])
        
        return entity
    
    async def mark_analyzed(self, patterns: List[str] = None) -> bool:
        """Mark the event as analyzed."""
        self.analyzed = True
        if patterns:
            self.patterns_detected.extend(patterns)
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_UPDATED,
                EntityType.EVENT,
                self.entity_id,
                update_type="marked_analyzed",
                patterns=patterns
            )
        
        return True
    
    async def add_triggered_action(self, action: str) -> bool:
        """Record an action triggered by this event."""
        if action not in self.triggered_actions:
            self.triggered_actions.append(action)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EventType.ENTITY_UPDATED,
                    EntityType.EVENT,
                    self.entity_id,
                    update_type="action_triggered",
                    action=action
                )
            
            return True
        return False
    
    def is_error_event(self) -> bool:
        """Check if this is an error event."""
        return self.outcome in [EventOutcome.FAILURE, EventOutcome.ERROR]
    
    def involves_entity(self, entity_type: EntityType, entity_id: int) -> bool:
        """Check if event involves a specific entity."""
        primary_match = (
            self.primary_entity_type == entity_type and 
            self.primary_entity_id == entity_id
        )
        secondary_match = (
            self.secondary_entity_type == entity_type and
            self.secondary_entity_id == entity_id
        )
        return primary_match or secondary_match
    
    def get_duration(self) -> Optional[float]:
        """Get event duration if available in data."""
        return self.data.get("duration") or self.data.get("execution_time")