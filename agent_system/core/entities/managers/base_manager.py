"""Compact base manager abstract class for entity-specific operations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import aiosqlite

from agent_system.core.entities.base import Entity, EntityState
from agent_system.core.events.event_types import EntityType, EventType
from agent_system.core.events.event_manager import EventManager
from .db_operations import DatabaseOperations


class BaseManager(ABC):
    """Abstract base class for entity-specific managers."""
    
    def __init__(
        self, 
        db_path: str, 
        entity_type: EntityType,
        entity_class: Type[Entity],
        event_manager: Optional[EventManager] = None
    ):
        self.db_path = db_path
        self.entity_type = entity_type
        self.entity_class = entity_class
        self.event_manager = event_manager
        self.cache: Dict[int, Entity] = {}
        self.cache_size = 50
    
    async def create(self, name: str, **kwargs) -> Entity:
        """Create a new entity of this manager's type."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Insert base entity record
                entity_id = await DatabaseOperations.insert_entity_record(
                    db, self.entity_type, name, **kwargs
                )
                
                # Insert type-specific record
                await self._create_type_specific_record(db, entity_id, name, **kwargs)
                await db.commit()
                
                # Create entity instance
                entity = self.entity_class(
                    entity_id=entity_id,
                    name=name,
                    entity_type=self.entity_type,
                    **kwargs
                )
                entity.event_manager = self.event_manager
                
                # Log creation event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.ENTITY_CREATED, self.entity_type, entity_id, name=name
                    )
                
                self.cache[entity_id] = entity
                return entity
                
            except Exception as e:
                await db.rollback()
                raise e
    
    async def get(self, entity_id: int) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        if entity_id in self.cache:
            return self.cache[entity_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get base entity data
            entity_data = await DatabaseOperations.get_entity_record(
                db, self.entity_type, entity_id
            )
            if not entity_data:
                return None
            
            # Get type-specific data
            type_data = await self._get_type_specific_data(db, entity_id)
            if not type_data:
                return None
            
            # Merge data
            entity_data.update(type_data)
            entity_data['relationships'] = await DatabaseOperations.get_entity_relationships(
                db, self.entity_type, entity_id
            )
            
            # Create entity instance
            entity = await self.entity_class.from_dict(entity_data)
            entity.event_manager = self.event_manager
            
            self.cache[entity_id] = entity
            return entity
    
    async def update(self, entity: Entity, **updates) -> bool:
        """Update an entity with new values."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Update base entity record
                base_updates = {
                    'name': updates.get('name', entity.name),
                    'version': updates.get('version', entity.version),
                    'state': updates.get('state', entity.state.value),
                    'metadata': updates.get('metadata', entity.metadata)
                }
                
                await DatabaseOperations.update_entity_record(
                    db, self.entity_type, entity.entity_id, **base_updates
                )
                
                # Update type-specific record
                await self._update_type_specific_record(db, entity, **updates)
                await db.commit()
                
                # Update entity object
                for key, value in updates.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                entity.updated_at = datetime.now()
                
                # Log update event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.ENTITY_UPDATED, self.entity_type, 
                        entity.entity_id, updates=updates
                    )
                
                self.cache[entity.entity_id] = entity
                return True
                
            except Exception as e:
                await db.rollback()
                raise e
    
    async def delete(self, entity_id: int, hard_delete: bool = False) -> bool:
        """Delete an entity (soft delete by default)."""
        entity = await self.get(entity_id)
        if not entity:
            return False
        
        if hard_delete:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("BEGIN")
                
                try:
                    await self._delete_type_specific_record(db, entity_id)
                    await DatabaseOperations.delete_entity_record(db, self.entity_type, entity_id)
                    await DatabaseOperations.delete_entity_relationships(db, self.entity_type, entity_id)
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    raise e
        else:
            await entity.update_state(EntityState.ARCHIVED)
            await self.update(entity, state=EntityState.ARCHIVED)
        
        # Log deletion event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_ARCHIVED if not hard_delete else EventType.ENTITY_UPDATED,
                self.entity_type, entity_id, hard_delete=hard_delete
            )
        
        if entity_id in self.cache:
            del self.cache[entity_id]
        
        return True
    
    async def list(
        self,
        state: Optional[EntityState] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Entity]:
        """List entities of this manager's type."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT entity_id FROM entities WHERE entity_type = ?"
            params = [self.entity_type.value]
            
            if state:
                query += " AND state = ?"
                params.append(state.value)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            entities = []
            for row in rows:
                entity = await self.get(row['entity_id'])
                if entity:
                    entities.append(entity)
            
            return entities
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search entities by text in specified fields."""
        if not fields:
            fields = ['name']
        
        entities = await self.list(limit=1000)
        results = []
        search_lower = search_term.lower()
        
        for entity in entities:
            for field in fields:
                if hasattr(entity, field):
                    value = getattr(entity, field)
                    if value and isinstance(value, str) and search_lower in value.lower():
                        results.append(entity)
                        break
        
        return results[:limit]
    
    @abstractmethod
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
        """Create type-specific database record."""
        pass
    
    @abstractmethod
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get type-specific data for an entity."""
        pass
    
    @abstractmethod
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update type-specific database record."""
        pass
    
    @abstractmethod
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete type-specific database record."""
        pass