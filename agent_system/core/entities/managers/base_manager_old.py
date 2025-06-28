"""Base manager abstract class for entity-specific operations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import json
import aiosqlite

from agent_system.core.entities.base import Entity, EntityState
from agent_system.core.events.event_types import EntityType, EventType
from agent_system.core.events.event_manager import EventManager


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
        
        # Cache for frequently accessed entities
        self.cache: Dict[int, Entity] = {}
        self.cache_size = 50  # Smaller cache per manager
    
    def _get_cache_key(self, entity_id: int) -> int:
        """Generate cache key for an entity."""
        return entity_id
    
    async def create(self, name: str, **kwargs) -> Entity:
        """Create a new entity of this manager's type."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Insert into entities table
                cursor = await db.execute("""
                    INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
                    VALUES (?, (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = ?), ?, ?, ?, ?, ?, ?)
                """, (
                    self.entity_type.value,
                    self.entity_type.value,
                    name,
                    kwargs.get('version', '1.0.0'),
                    kwargs.get('state', EntityState.ACTIVE.value),
                    json.dumps(kwargs.get('metadata', {})),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                entity_id = cursor.lastrowid
                
                # Insert into type-specific table
                await self._create_type_specific_record(db, entity_id, name, **kwargs)
                
                await db.commit()
                
                # Create entity instance
                entity = self.entity_class(
                    entity_id=entity_id,
                    name=name,
                    entity_type=self.entity_type,
                    **kwargs
                )
                
                # Set event manager
                entity.event_manager = self.event_manager
                
                # Log creation event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.ENTITY_CREATED,
                        self.entity_type,
                        entity_id,
                        name=name
                    )
                
                # Cache the entity
                self.cache[entity_id] = entity
                
                return entity
                
            except Exception as e:
                await db.rollback()
                raise e
    
    async def get(self, entity_id: int) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        # Check cache first
        if entity_id in self.cache:
            return self.cache[entity_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get from entities table
            cursor = await db.execute("""
                SELECT * FROM entities 
                WHERE entity_type = ? AND entity_id = ?
            """, (self.entity_type.value, entity_id))
            
            entity_row = await cursor.fetchone()
            if not entity_row:
                return None
            
            # Get type-specific data
            type_data = await self._get_type_specific_data(db, entity_id)
            if not type_data:
                return None
            
            # Merge data
            entity_data = dict(entity_row)
            entity_data.update(type_data)
            entity_data['metadata'] = json.loads(entity_data.get('metadata', '{}'))
            
            # Get relationships
            relationships = await self._get_entity_relationships(db, entity_id)
            entity_data['relationships'] = relationships
            
            # Create entity instance
            entity = await self.entity_class.from_dict(entity_data)
            entity.event_manager = self.event_manager
            
            # Cache it
            self.cache[entity_id] = entity
            
            return entity
    
    async def update(self, entity: Entity, **updates) -> bool:
        """Update an entity with new values."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Update entities table
                await db.execute("""
                    UPDATE entities 
                    SET name = ?, version = ?, state = ?, metadata = ?, updated_at = ?
                    WHERE entity_type = ? AND entity_id = ?
                """, (
                    updates.get('name', entity.name),
                    updates.get('version', entity.version),
                    updates.get('state', entity.state.value),
                    json.dumps(updates.get('metadata', entity.metadata)),
                    datetime.now().isoformat(),
                    self.entity_type.value,
                    entity.entity_id
                ))
                
                # Update type-specific table
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
                        EventType.ENTITY_UPDATED,
                        self.entity_type,
                        entity.entity_id,
                        updates=updates
                    )
                
                # Update cache
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
            # Hard delete from database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("BEGIN")
                
                try:
                    # Delete from type-specific table
                    await self._delete_type_specific_record(db, entity_id)
                    
                    # Delete from entities table
                    await db.execute("""
                        DELETE FROM entities 
                        WHERE entity_type = ? AND entity_id = ?
                    """, (self.entity_type.value, entity_id))
                    
                    # Delete relationships
                    await db.execute("""
                        DELETE FROM entity_relationships 
                        WHERE (source_type = ? AND source_id = ?) 
                           OR (target_type = ? AND target_id = ?)
                    """, (self.entity_type.value, entity_id, self.entity_type.value, entity_id))
                    
                    await db.commit()
                    
                except Exception as e:
                    await db.rollback()
                    raise e
        else:
            # Soft delete - update state
            await entity.update_state(EntityState.ARCHIVED)
            await self.update(entity, state=EntityState.ARCHIVED)
        
        # Log deletion event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_ARCHIVED if not hard_delete else EventType.ENTITY_UPDATED,
                self.entity_type,
                entity_id,
                hard_delete=hard_delete
            )
        
        # Remove from cache
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
            
            query = """
                SELECT entity_id FROM entities 
                WHERE entity_type = ?
            """
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
            fields = ['name']  # Base default, subclasses can override
        
        entities = await self.list(limit=1000)  # Get more for filtering
        
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
    
    async def _get_entity_relationships(
        self,
        db,
        entity_id: int
    ) -> Dict[str, List[int]]:
        """Get all relationships for an entity."""
        cursor = await db.execute("""
            SELECT relationship_type, target_id
            FROM entity_relationships
            WHERE source_type = ? AND source_id = ?
        """, (self.entity_type.value, entity_id))
        
        rows = await cursor.fetchall()
        relationships = {}
        
        for row in rows:
            rel_type = row['relationship_type']
            if rel_type not in relationships:
                relationships[rel_type] = []
            relationships[rel_type].append(row['target_id'])
        
        return relationships
    
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