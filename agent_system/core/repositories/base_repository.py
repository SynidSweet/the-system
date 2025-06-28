"""Base repository implementation with common CRUD operations."""

from typing import Dict, List, Optional, Any, Type, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime
import json
import aiosqlite

from ..entities.base import Entity, EntityState
from ..events.event_types import EntityType, EventType
from ..events.event_manager import EventManager
from .repository_interface import Repository

T = TypeVar('T', bound=Entity)


class BaseRepository(Repository[T], ABC):
    """Base repository implementation with common operations."""
    
    def __init__(
        self,
        db_path: str,
        entity_type: EntityType,
        entity_class: Type[T],
        event_manager: Optional[EventManager] = None
    ):
        self.db_path = db_path
        self.entity_type = entity_type
        self.entity_class = entity_class
        self.event_manager = event_manager
        self.cache: Dict[int, T] = {}
        self.cache_size = 50
    
    async def create(self, entity_data: Dict[str, Any]) -> T:
        """Create a new entity."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Insert base entity record
                entity_id = await self._insert_base_entity(db, entity_data)
                
                # Insert type-specific record
                await self._insert_type_specific(db, entity_id, entity_data)
                await db.commit()
                
                # Create entity instance
                entity = await self._create_entity_instance(entity_id, entity_data)
                
                # Log creation event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.ENTITY_CREATED, 
                        self.entity_type, 
                        entity_id,
                        name=entity_data.get('name', 'unnamed')
                    )
                
                self.cache[entity_id] = entity
                return entity
                
            except Exception as e:
                await db.rollback()
                raise e
    
    async def get(self, entity_id: int) -> Optional[T]:
        """Retrieve an entity by ID."""
        if entity_id in self.cache:
            return self.cache[entity_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get base entity data
            base_data = await self._get_base_entity(db, entity_id)
            if not base_data:
                return None
            
            # Get type-specific data
            type_data = await self._get_type_specific(db, entity_id)
            if not type_data:
                return None
            
            # Merge data and create entity
            entity_data = {**base_data, **type_data}
            entity = await self._create_entity_instance(entity_id, entity_data)
            
            self.cache[entity_id] = entity
            return entity
    
    async def update(self, entity_id: int, updates: Dict[str, Any]) -> Optional[T]:
        """Update an entity with new values."""
        entity = await self.get(entity_id)
        if not entity:
            return None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Update base entity
                await self._update_base_entity(db, entity_id, updates)
                
                # Update type-specific data
                await self._update_type_specific(db, entity_id, updates)
                await db.commit()
                
                # Update entity object
                for key, value in updates.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                entity.updated_at = datetime.now()
                
                # Log update event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.ENTITY_UPDATED,
                        self.entity_type,
                        entity_id,
                        updates=updates
                    )
                
                self.cache[entity_id] = entity
                return entity
                
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
                    await self._delete_type_specific(db, entity_id)
                    await self._delete_base_entity(db, entity_id)
                    await self._delete_relationships(db, entity_id)
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    raise e
        else:
            await self.update(entity_id, {'state': EntityState.ARCHIVED.value})
        
        # Log deletion event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_ARCHIVED if not hard_delete else EventType.ENTITY_UPDATED,
                self.entity_type,
                entity_id,
                hard_delete=hard_delete
            )
        
        if entity_id in self.cache:
            del self.cache[entity_id]
        
        return True
    
    async def list(
        self,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """List entities with optional filtering."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT entity_id FROM entities WHERE entity_type = ?"
            params = [self.entity_type.value]
            
            if state:
                query += " AND state = ?"
                params.append(state)
            
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
    ) -> List[T]:
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
    
    async def count(self, state: Optional[str] = None) -> int:
        """Count entities with optional state filter."""
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT COUNT(*) as count FROM entities WHERE entity_type = ?"
            params = [self.entity_type.value]
            
            if state:
                query += " AND state = ?"
                params.append(state)
            
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return row['count'] if row else 0
    
    # Private helper methods
    async def _insert_base_entity(self, db, entity_data: Dict[str, Any]) -> int:
        """Insert base entity record and return entity_id."""
        cursor = await db.execute("""
            INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
            VALUES (?, (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = ?), ?, ?, ?, ?, ?, ?)
        """, (
            self.entity_type.value,
            self.entity_type.value,
            entity_data.get('name', 'unnamed'),
            entity_data.get('version', '1.0.0'),
            entity_data.get('state', 'active'),
            json.dumps(entity_data.get('metadata', {})),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        return cursor.lastrowid
    
    async def _get_base_entity(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get base entity record."""
        cursor = await db.execute("""
            SELECT * FROM entities 
            WHERE entity_type = ? AND entity_id = ?
        """, (self.entity_type.value, entity_id))
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            data['metadata'] = json.loads(data.get('metadata', '{}'))
            return data
        return None
    
    async def _update_base_entity(self, db, entity_id: int, updates: Dict[str, Any]):
        """Update base entity record."""
        await db.execute("""
            UPDATE entities 
            SET name = ?, version = ?, state = ?, metadata = ?, updated_at = ?
            WHERE entity_type = ? AND entity_id = ?
        """, (
            updates.get('name'),
            updates.get('version'),
            updates.get('state'),
            json.dumps(updates.get('metadata', {})),
            datetime.now().isoformat(),
            self.entity_type.value,
            entity_id
        ))
    
    async def _delete_base_entity(self, db, entity_id: int):
        """Delete base entity record."""
        await db.execute("""
            DELETE FROM entities 
            WHERE entity_type = ? AND entity_id = ?
        """, (self.entity_type.value, entity_id))
    
    async def _delete_relationships(self, db, entity_id: int):
        """Delete all relationships for an entity."""
        await db.execute("""
            DELETE FROM entity_relationships 
            WHERE (source_type = ? AND source_id = ?) 
               OR (target_type = ? AND target_id = ?)
        """, (self.entity_type.value, entity_id, self.entity_type.value, entity_id))
    
    async def _create_entity_instance(self, entity_id: int, entity_data: Dict[str, Any]) -> T:
        """Create entity instance from data."""
        entity_data['entity_id'] = entity_id
        entity_data['entity_type'] = self.entity_type
        
        entity = await self.entity_class.from_dict(entity_data)
        entity.event_manager = self.event_manager
        return entity
    
    # Abstract methods for type-specific operations
    @abstractmethod
    async def _insert_type_specific(self, db, entity_id: int, entity_data: Dict[str, Any]):
        """Insert type-specific record."""
        pass
    
    @abstractmethod
    async def _get_type_specific(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get type-specific data."""
        pass
    
    @abstractmethod
    async def _update_type_specific(self, db, entity_id: int, updates: Dict[str, Any]):
        """Update type-specific record."""
        pass
    
    @abstractmethod
    async def _delete_type_specific(self, db, entity_id: int):
        """Delete type-specific record."""
        pass