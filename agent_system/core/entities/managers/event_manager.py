"""Event entity-specific manager (not to be confused with core event manager)."""

from typing import Dict, List, Optional, Any
import json
import aiosqlite

from ..base import Entity
from ..event import EventEntity
from ...events.event_types import EntityType
from ...events.event_manager import EventManager
from .base_manager import BaseManager


class EventEntityManager(BaseManager):
    """Manager for event entities (different from core EventManager)."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.EVENT,
            entity_class=EventEntity,
            event_manager=event_manager
        )
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search event entities by type or data content."""
        if not fields:
            fields = ['name']  # Events don't have much searchable text
        
        return await super().search(search_term, fields, limit)
    
    async def find_by_event_type(self, event_type: str) -> List[EventEntity]:
        """Find events by their type."""
        events = await self.list(limit=1000)
        
        results = []
        for event in events:
            if isinstance(event, EventEntity):
                # Event type might be stored in metadata
                if event.metadata.get('event_type') == event_type:
                    results.append(event)
        
        return results
    
    async def find_by_entity_reference(self, entity_type: str, entity_id: int) -> List[EventEntity]:
        """Find events related to a specific entity."""
        events = await self.list(limit=1000)
        
        results = []
        for event in events:
            if isinstance(event, EventEntity):
                # Check if event references the entity
                metadata = event.metadata
                if (metadata.get('entity_type') == entity_type and 
                    metadata.get('entity_id') == entity_id):
                    results.append(event)
        
        return results
    
    async def find_by_date_range(self, start_date: str, end_date: str) -> List[EventEntity]:
        """Find events within a date range."""
        # This would be more efficiently done at the database level
        # For now, we'll filter in memory
        events = await self.list(limit=10000)
        
        results = []
        for event in events:
            if isinstance(event, EventEntity):
                if (event.created_at and 
                    start_date <= event.created_at.isoformat() <= end_date):
                    results.append(event)
        
        return results
    
    async def get_recent_events(self, limit: int = 100) -> List[EventEntity]:
        """Get the most recent events."""
        return await self.list(limit=limit)
    
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
        """Create event-specific record (events table already managed by core event system)."""
        # Events are typically created through the event system
        # This manager is more for querying existing events
        pass
    
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get event-specific data."""
        cursor = await db.execute(
            "SELECT * FROM events WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON fields
            if 'data' in data and data['data']:
                try:
                    data['data'] = json.loads(data['data'])
                except:
                    data['data'] = {}
            
            if 'resource_usage' in data and data['resource_usage']:
                try:
                    data['resource_usage'] = json.loads(data['resource_usage'])
                except:
                    data['resource_usage'] = {}
            
            return data
        return None
    
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update event-specific fields."""
        # Events are typically immutable once created
        # Only metadata updates might be allowed
        pass
    
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete event-specific record."""
        await db.execute("DELETE FROM events WHERE id = ?", (entity_id,))