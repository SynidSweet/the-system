"""Entity Manager for CRUD operations on all entity types."""

import asyncio
from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime
import json
import aiosqlite

from .base import Entity, EntityState
from .agent_entity import AgentEntity
from .task_entity import TaskEntity, TaskState
from .tool_entity import ToolEntity, ToolCategory
from .context_entity import ContextEntity, ContextCategory, ContextFormat
from .process_entity import ProcessEntity, ProcessType
from .event_entity import EventEntity
from ..events.event_types import EntityType, EventType
from ..events.event_manager import EventManager


class EntityManager:
    """Manages CRUD operations for all entity types."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        self.db_path = db_path
        self.event_manager = event_manager
        
        # Entity type mapping
        self.entity_classes: Dict[EntityType, Type[Entity]] = {
            EntityType.AGENT: AgentEntity,
            EntityType.TASK: TaskEntity,
            EntityType.TOOL: ToolEntity,
            EntityType.DOCUMENT: ContextEntity,
            EntityType.PROCESS: ProcessEntity,
            EntityType.EVENT: EventEntity
        }
        
        # Cache for frequently accessed entities
        self.cache: Dict[str, Entity] = {}
        self.cache_size = 100
    
    def _get_cache_key(self, entity_type: EntityType, entity_id: int) -> str:
        """Generate cache key for an entity."""
        return f"{entity_type.value}:{entity_id}"
    
    async def create_entity(
        self,
        entity_type: EntityType,
        name: str,
        **kwargs
    ) -> Entity:
        """Create a new entity of the specified type."""
        async with aiosqlite.connect(self.db_path) as db:
            # Begin transaction
            await db.execute("BEGIN")
            
            try:
                # Insert into entities table
                cursor = await db.execute("""
                    INSERT INTO entities (entity_type, entity_id, name, version, status, metadata, created_at, updated_at)
                    VALUES (?, (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = ?), ?, ?, ?, ?, ?, ?)
                """, (
                    entity_type.value,
                    entity_type.value,
                    name,
                    kwargs.get('version', '1.0.0'),
                    kwargs.get('state', EntityState.ACTIVE.value),
                    json.dumps(kwargs.get('metadata', {})),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                entity_id = cursor.lastrowid
                
                # Insert into type-specific table
                if entity_type == EntityType.AGENT:
                    await self._create_agent_record(db, entity_id, name, **kwargs)
                elif entity_type == EntityType.TASK:
                    await self._create_task_record(db, entity_id, name, **kwargs)
                elif entity_type == EntityType.TOOL:
                    await self._create_tool_record(db, entity_id, name, **kwargs)
                elif entity_type == EntityType.DOCUMENT:
                    await self._create_context_record(db, entity_id, name, **kwargs)
                elif entity_type == EntityType.PROCESS:
                    await self._create_process_record(db, entity_id, name, **kwargs)
                elif entity_type == EntityType.EVENT:
                    await self._create_event_record(db, entity_id, **kwargs)
                
                await db.commit()
                
                # Create entity instance
                entity_class = self.entity_classes[entity_type]
                entity = entity_class(
                    entity_id=entity_id,
                    name=name,
                    **kwargs
                )
                
                # Set event manager
                entity.event_manager = self.event_manager
                
                # Log creation event
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.ENTITY_CREATED,
                        entity_type,
                        entity_id,
                        event_data={"name": name}
                    )
                
                # Cache the entity
                cache_key = self._get_cache_key(entity_type, entity_id)
                self.cache[cache_key] = entity
                
                return entity
                
            except Exception as e:
                await db.rollback()
                raise e
    
    async def get_entity(
        self,
        entity_type: EntityType,
        entity_id: int
    ) -> Optional[Entity]:
        """Retrieve an entity by type and ID."""
        # Check cache first
        cache_key = self._get_cache_key(entity_type, entity_id)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get from entities table
            cursor = await db.execute("""
                SELECT * FROM entities 
                WHERE entity_type = ? AND entity_id = ?
            """, (entity_type.value, entity_id))
            
            entity_row = await cursor.fetchone()
            if not entity_row:
                return None
            
            # Get type-specific data
            type_data = await self._get_type_specific_data(db, entity_type, entity_id)
            if not type_data:
                return None
            
            # Merge data
            entity_data = dict(entity_row)
            entity_data.update(type_data)
            entity_data['metadata'] = json.loads(entity_data.get('metadata', '{}'))
            
            # Get relationships
            relationships = await self._get_entity_relationships(db, entity_type, entity_id)
            entity_data['relationships'] = relationships
            
            # Create entity instance
            entity_class = self.entity_classes[entity_type]
            entity = await entity_class.from_dict(entity_data)
            entity.event_manager = self.event_manager
            
            # Cache it
            self.cache[cache_key] = entity
            
            return entity
    
    async def update_entity(
        self,
        entity: Entity,
        **updates
    ) -> bool:
        """Update an entity with new values."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            
            try:
                # Update entities table
                await db.execute("""
                    UPDATE entities 
                    SET name = ?, version = ?, status = ?, metadata = ?, updated_at = ?
                    WHERE entity_type = ? AND entity_id = ?
                """, (
                    updates.get('name', entity.name),
                    updates.get('version', entity.version),
                    updates.get('state', entity.state.value),
                    json.dumps(updates.get('metadata', entity.metadata)),
                    datetime.now().isoformat(),
                    entity.entity_type.value,
                    entity.entity_id
                ))
                
                # Update type-specific table
                if entity.entity_type == EntityType.AGENT:
                    await self._update_agent_record(db, entity, **updates)
                elif entity.entity_type == EntityType.TASK:
                    await self._update_task_record(db, entity, **updates)
                elif entity.entity_type == EntityType.TOOL:
                    await self._update_tool_record(db, entity, **updates)
                elif entity.entity_type == EntityType.DOCUMENT:
                    await self._update_context_record(db, entity, **updates)
                elif entity.entity_type == EntityType.PROCESS:
                    await self._update_process_record(db, entity, **updates)
                
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
                        entity.entity_type,
                        entity.entity_id,
                        event_data={"updates": updates}
                    )
                
                # Update cache
                cache_key = self._get_cache_key(entity.entity_type, entity.entity_id)
                self.cache[cache_key] = entity
                
                return True
                
            except Exception as e:
                await db.rollback()
                raise e
    
    async def delete_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        hard_delete: bool = False
    ) -> bool:
        """Delete an entity (soft delete by default)."""
        entity = await self.get_entity(entity_type, entity_id)
        if not entity:
            return False
        
        if hard_delete:
            # Hard delete from database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("BEGIN")
                
                try:
                    # Delete from type-specific table
                    if entity_type == EntityType.AGENT:
                        await db.execute("DELETE FROM agents WHERE id = ?", (entity_id,))
                    elif entity_type == EntityType.TASK:
                        await db.execute("DELETE FROM tasks WHERE id = ?", (entity_id,))
                    elif entity_type == EntityType.TOOL:
                        await db.execute("DELETE FROM tools WHERE id = ?", (entity_id,))
                    elif entity_type == EntityType.DOCUMENT:
                        await db.execute("DELETE FROM context_documents WHERE id = ?", (entity_id,))
                    elif entity_type == EntityType.PROCESS:
                        await db.execute("DELETE FROM processes WHERE id = ?", (entity_id,))
                    
                    # Delete from entities table
                    await db.execute("""
                        DELETE FROM entities 
                        WHERE entity_type = ? AND entity_id = ?
                    """, (entity_type.value, entity_id))
                    
                    # Delete relationships
                    await db.execute("""
                        DELETE FROM entity_relationships 
                        WHERE (source_type = ? AND source_id = ?) 
                           OR (target_type = ? AND target_id = ?)
                    """, (entity_type.value, entity_id, entity_type.value, entity_id))
                    
                    await db.commit()
                    
                except Exception as e:
                    await db.rollback()
                    raise e
        else:
            # Soft delete - update state
            await entity.update_state(EntityState.ARCHIVED)
            await self.update_entity(entity, state=EntityState.ARCHIVED)
        
        # Log deletion event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_ARCHIVED if not hard_delete else EventType.ENTITY_UPDATED,
                entity_type,
                entity_id,
                hard_delete=hard_delete
            )
        
        # Remove from cache
        cache_key = self._get_cache_key(entity_type, entity_id)
        if cache_key in self.cache:
            del self.cache[cache_key]
        
        return True
    
    async def list_entities(
        self,
        entity_type: EntityType,
        state: Optional[EntityState] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Entity]:
        """List entities of a specific type."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT entity_id FROM entities 
                WHERE entity_type = ?
            """
            params = [entity_type.value]
            
            if state:
                query += " AND state = ?"
                params.append(state.value)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            entities = []
            for row in rows:
                entity = await self.get_entity(entity_type, row['entity_id'])
                if entity:
                    entities.append(entity)
            
            return entities
    
    async def search_entities(
        self,
        entity_type: EntityType,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search entities by text in specified fields."""
        if not fields:
            fields = ['name', 'instruction', 'description', 'title', 'content']
        
        entities = await self.list_entities(entity_type, limit=1000)  # Get more for filtering
        
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
    
    # Relationship management methods
    async def create_relationship(
        self,
        source_entity: Entity,
        target_entity: Entity,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a relationship between two entities."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO entity_relationships 
                (source_type, source_id, target_type, target_id, relationship_type, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                source_entity.entity_type.value,
                source_entity.entity_id,
                target_entity.entity_type.value,
                target_entity.entity_id,
                relationship_type,
                json.dumps(metadata or {}),
                datetime.now().isoformat()
            ))
            await db.commit()
        
        # Update entity objects
        await source_entity.add_relationship(
            relationship_type,
            target_entity.entity_id,
            metadata
        )
        
        return True
    
    async def get_related_entities(
        self,
        entity: Entity,
        relationship_type: Optional[str] = None,
        target_type: Optional[EntityType] = None
    ) -> List[Entity]:
        """Get entities related to the given entity."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT target_type, target_id, relationship_type
                FROM entity_relationships
                WHERE source_type = ? AND source_id = ?
            """
            params = [entity.entity_type.value, entity.entity_id]
            
            if relationship_type:
                query += " AND relationship_type = ?"
                params.append(relationship_type)
            
            if target_type:
                query += " AND target_type = ?"
                params.append(target_type.value)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            related_entities = []
            for row in rows:
                target_entity_type = EntityType(row['target_type'])
                target_entity = await self.get_entity(
                    target_entity_type,
                    row['target_id']
                )
                if target_entity:
                    related_entities.append(target_entity)
            
            return related_entities
    
    # Helper methods for type-specific operations
    async def _create_agent_record(self, db, entity_id: int, name: str, **kwargs):
        """Create agent-specific record."""
        await db.execute("""
            INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            name,
            kwargs['instruction'],
            json.dumps(kwargs.get('context_documents', [])),
            json.dumps(kwargs.get('available_tools', [])),
            json.dumps(kwargs.get('permissions', [])),
            json.dumps(kwargs.get('constraints', []))
        ))
    
    async def _create_task_record(self, db, entity_id: int, name: str, **kwargs):
        """Create task-specific record."""
        await db.execute("""
            INSERT INTO tasks (id, parent_task_id, tree_id, agent_id, instruction, status, result, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            kwargs.get('parent_task_id'),
            kwargs.get('tree_id', entity_id),
            None,  # Agent ID will be set later
            kwargs['instruction'],
            kwargs.get('task_state', TaskState.CREATED.value),
            json.dumps(kwargs.get('result', {})),
            json.dumps(kwargs.get('metadata', {}))
        ))
    
    async def _create_tool_record(self, db, entity_id: int, name: str, **kwargs):
        """Create tool-specific record."""
        await db.execute("""
            INSERT INTO tools (id, name, description, category, implementation, parameters, permissions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            name,
            kwargs['description'],
            kwargs.get('category', ToolCategory.SYSTEM.value),
            kwargs['implementation'],
            json.dumps(kwargs.get('parameters', {})),
            json.dumps(kwargs.get('permissions', []))
        ))
    
    async def _create_context_record(self, db, entity_id: int, name: str, **kwargs):
        """Create context document record."""
        await db.execute("""
            INSERT INTO context_documents (id, name, title, category, content, format, version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            name,
            kwargs['title'],
            kwargs.get('category', ContextCategory.SYSTEM.value),
            kwargs['content'],
            kwargs.get('format', ContextFormat.MARKDOWN.value),
            kwargs.get('version', '1.0.0')
        ))
    
    async def _create_process_record(self, db, entity_id: int, name: str, **kwargs):
        """Create process-specific record."""
        await db.execute("""
            INSERT INTO processes (id, name, description, parameters, steps, rollback_steps, permissions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            name,
            kwargs['description'],
            json.dumps(kwargs.get('parameters_schema', {})),
            json.dumps([]),  # Steps will be populated from implementation
            json.dumps([]),  # Rollback steps will be populated from implementation
            json.dumps(kwargs.get('permissions', []))
        ))
    
    async def _create_event_record(self, db, entity_id: int, **kwargs):
        """Create event-specific record (events table already exists)."""
        # Events are already created through the event system
        pass
    
    async def _get_type_specific_data(
        self,
        db,
        entity_type: EntityType,
        entity_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get type-specific data for an entity."""
        if entity_type == EntityType.AGENT:
            cursor = await db.execute(
                "SELECT * FROM agents WHERE id = ?",
                (entity_id,)
            )
        elif entity_type == EntityType.TASK:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (entity_id,)
            )
        elif entity_type == EntityType.TOOL:
            cursor = await db.execute(
                "SELECT * FROM tools WHERE id = ?",
                (entity_id,)
            )
        elif entity_type == EntityType.DOCUMENT:
            cursor = await db.execute(
                "SELECT * FROM context_documents WHERE id = ?",
                (entity_id,)
            )
        elif entity_type == EntityType.PROCESS:
            cursor = await db.execute(
                "SELECT * FROM processes WHERE id = ?",
                (entity_id,)
            )
        elif entity_type == EntityType.EVENT:
            cursor = await db.execute(
                "SELECT * FROM events WHERE id = ?",
                (entity_id,)
            )
        else:
            return None
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON fields
            for field in ['context_documents', 'available_tools', 'permissions', 
                         'constraints', 'parameters', 'steps', 'rollback_steps',
                         'result', 'metadata', 'data']:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except:
                        pass
            return data
        return None
    
    async def _get_entity_relationships(
        self,
        db,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, List[int]]:
        """Get all relationships for an entity."""
        cursor = await db.execute("""
            SELECT relationship_type, target_id
            FROM entity_relationships
            WHERE source_type = ? AND source_id = ?
        """, (entity_type.value, entity_id))
        
        rows = await cursor.fetchall()
        relationships = {}
        
        for row in rows:
            rel_type = row['relationship_type']
            if rel_type not in relationships:
                relationships[rel_type] = []
            relationships[rel_type].append(row['target_id'])
        
        return relationships
    
    async def _update_agent_record(self, db, entity: AgentEntity, **updates):
        """Update agent-specific fields."""
        if any(field in updates for field in ['instruction', 'context_documents', 
                                              'available_tools', 'permissions', 'constraints']):
            await db.execute("""
                UPDATE agents SET
                    instruction = ?,
                    context_documents = ?,
                    available_tools = ?,
                    permissions = ?,
                    constraints = ?
                WHERE id = ?
            """, (
                updates.get('instruction', entity.instruction),
                json.dumps(updates.get('context_documents', entity.context_documents)),
                json.dumps(updates.get('available_tools', entity.available_tools)),
                json.dumps(updates.get('permissions', entity.permissions)),
                json.dumps(updates.get('constraints', entity.constraints)),
                entity.entity_id
            ))
    
    async def _update_task_record(self, db, entity: TaskEntity, **updates):
        """Update task-specific fields."""
        if any(field in updates for field in ['task_state', 'result', 'assigned_agent']):
            await db.execute("""
                UPDATE tasks SET
                    status = ?,
                    result = ?,
                    metadata = ?
                WHERE id = ?
            """, (
                updates.get('task_state', entity.task_state.value),
                json.dumps(updates.get('result', entity.result or {})),
                json.dumps(entity.metadata),
                entity.entity_id
            ))
    
    async def _update_tool_record(self, db, entity: ToolEntity, **updates):
        """Update tool-specific fields."""
        if any(field in updates for field in ['description', 'implementation', 'parameters']):
            await db.execute("""
                UPDATE tools SET
                    description = ?,
                    implementation = ?,
                    parameters = ?
                WHERE id = ?
            """, (
                updates.get('description', entity.description),
                updates.get('implementation', entity.implementation),
                json.dumps(updates.get('parameters', entity.parameters)),
                entity.entity_id
            ))
    
    async def _update_context_record(self, db, entity: ContextEntity, **updates):
        """Update context document fields."""
        if any(field in updates for field in ['title', 'content', 'category']):
            await db.execute("""
                UPDATE context_documents SET
                    title = ?,
                    content = ?,
                    category = ?
                WHERE id = ?
            """, (
                updates.get('title', entity.title),
                updates.get('content', entity.content),
                updates.get('category', entity.category.value),
                entity.entity_id
            ))
    
    async def _update_process_record(self, db, entity: ProcessEntity, **updates):
        """Update process-specific fields."""
        if any(field in updates for field in ['description', 'implementation_path']):
            await db.execute("""
                UPDATE processes SET
                    description = ?,
                    parameters = ?
                WHERE id = ?
            """, (
                updates.get('description', entity.description),
                json.dumps(updates.get('parameters_schema', entity.parameters_schema)),
                entity.entity_id
            ))