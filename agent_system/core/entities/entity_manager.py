"""EntityManager facade that delegates to type-specific managers."""

from typing import Dict, List, Optional, Any, Type, Union

from .base import Entity, EntityState
from .agent import AgentEntity
from .task import TaskEntity
from .tool import ToolEntity
from .context import ContextEntity
from .process import ProcessEntity
from .event import EventEntity
from ..events.event_types import EntityType
from ..events.event_manager import EventManager

from .managers.agent_manager import AgentManager
from .managers.task_manager import TaskManager
from .managers.tool_manager import ToolManager
from .managers.context_manager import ContextManager
from .managers.process_manager import ProcessManager
from .managers.event_manager import EventEntityManager


class EntityManager:
    """Facade that delegates to type-specific entity managers."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        self.db_path = db_path
        self.event_manager = event_manager
        
        # Initialize type-specific managers
        self.managers: Dict[EntityType, Any] = {
            EntityType.AGENT: AgentManager(db_path, event_manager),
            EntityType.TASK: TaskManager(db_path, event_manager),
            EntityType.TOOL: ToolManager(db_path, event_manager),
            EntityType.DOCUMENT: ContextManager(db_path, event_manager),
            EntityType.PROCESS: ProcessManager(db_path, event_manager),
            EntityType.EVENT: EventEntityManager(db_path, event_manager)
        }
        
        # Entity type mapping for backward compatibility
        self.entity_classes: Dict[EntityType, Type[Entity]] = {
            EntityType.AGENT: AgentEntity,
            EntityType.TASK: TaskEntity,
            EntityType.TOOL: ToolEntity,
            EntityType.DOCUMENT: ContextEntity,
            EntityType.PROCESS: ProcessEntity,
            EntityType.EVENT: EventEntity
        }
    
    # Backward compatibility methods - delegate to specific managers
    
    async def create_entity(
        self,
        entity_type: EntityType,
        name: str,
        **kwargs
    ) -> Entity:
        """Create a new entity of the specified type."""
        manager = self.managers[entity_type]
        return await manager.create(name, **kwargs)
    
    async def get_entity(
        self,
        entity_type: EntityType,
        entity_id: int
    ) -> Optional[Entity]:
        """Retrieve an entity by type and ID."""
        manager = self.managers[entity_type]
        return await manager.get(entity_id)
    
    async def update_entity(
        self,
        entity: Entity,
        **updates
    ) -> bool:
        """Update an entity with new values."""
        manager = self.managers[entity.entity_type]
        return await manager.update(entity, **updates)
    
    async def delete_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        hard_delete: bool = False
    ) -> bool:
        """Delete an entity (soft delete by default)."""
        manager = self.managers[entity_type]
        return await manager.delete(entity_id, hard_delete)
    
    async def list_entities(
        self,
        entity_type: EntityType,
        state: Optional[EntityState] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Entity]:
        """List entities of a specific type."""
        manager = self.managers[entity_type]
        return await manager.list(state, limit, offset)
    
    async def search_entities(
        self,
        entity_type: EntityType,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search entities by text in specified fields."""
        manager = self.managers[entity_type]
        return await manager.search(search_term, fields, limit)
    
    # Relationship management methods
    async def create_relationship(
        self,
        source_entity: Entity,
        target_entity: Entity,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a relationship between two entities."""
        import aiosqlite
        import json
        from datetime import datetime
        
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
        import aiosqlite
        
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
    
    # Convenience methods for accessing specific managers
    
    @property
    def agents(self) -> AgentManager:
        """Get the agent manager."""
        return self.managers[EntityType.AGENT]
    
    @property
    def tasks(self) -> TaskManager:
        """Get the task manager."""
        return self.managers[EntityType.TASK]
    
    @property
    def tools(self) -> ToolManager:
        """Get the tool manager."""
        return self.managers[EntityType.TOOL]
    
    @property
    def documents(self) -> ContextManager:
        """Get the context document manager."""
        return self.managers[EntityType.DOCUMENT]
    
    @property
    def processes(self) -> ProcessManager:
        """Get the process manager."""
        return self.managers[EntityType.PROCESS]
    
    @property
    def events(self) -> EventEntityManager:
        """Get the event entity manager."""
        return self.managers[EntityType.EVENT]