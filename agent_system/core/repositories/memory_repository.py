"""In-memory repository implementations for testing."""

from typing import Dict, List, Optional, Any, TypeVar
from datetime import datetime
import copy

from ..entities.base import Entity, EntityState
from ..events.event_types import EntityType, EventType
from ..events.event_manager import EventManager
from .repository_interface import Repository

T = TypeVar('T', bound=Entity)


class InMemoryRepository(Repository[T]):
    """In-memory repository implementation for testing."""
    
    def __init__(
        self,
        entity_type: EntityType,
        entity_class: type,
        event_manager: Optional[EventManager] = None
    ):
        self.entity_type = entity_type
        self.entity_class = entity_class
        self.event_manager = event_manager
        self._storage: Dict[int, T] = {}
        self._next_id = 1
    
    async def create(self, entity_data: Dict[str, Any]) -> T:
        """Create a new entity."""
        entity_id = self._next_id
        self._next_id += 1
        
        # Create entity with ID
        entity_data = copy.deepcopy(entity_data)
        entity_data['entity_id'] = entity_id
        entity_data['entity_type'] = self.entity_type
        entity_data['created_at'] = datetime.now()
        entity_data['updated_at'] = datetime.now()
        
        # Set defaults
        if 'state' not in entity_data:
            entity_data['state'] = EntityState.ACTIVE
        if 'version' not in entity_data:
            entity_data['version'] = '1.0.0'
        if 'metadata' not in entity_data:
            entity_data['metadata'] = {}
        
        # Create entity instance
        entity = await self.entity_class.from_dict(entity_data)
        entity.event_manager = self.event_manager
        
        # Store entity
        self._storage[entity_id] = entity
        
        # Log creation event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_CREATED,
                self.entity_type,
                entity_id,
                name=entity_data.get('name', 'unnamed')
            )
        
        return entity
    
    async def get(self, entity_id: int) -> Optional[T]:
        """Retrieve an entity by ID."""
        return self._storage.get(entity_id)
    
    async def update(self, entity_id: int, updates: Dict[str, Any]) -> Optional[T]:
        """Update an entity with new values."""
        entity = self._storage.get(entity_id)
        if not entity:
            return None
        
        # Update entity attributes
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
        
        return entity
    
    async def delete(self, entity_id: int, hard_delete: bool = False) -> bool:
        """Delete an entity (soft delete by default)."""
        entity = self._storage.get(entity_id)
        if not entity:
            return False
        
        if hard_delete:
            del self._storage[entity_id]
        else:
            entity.state = EntityState.ARCHIVED
            entity.updated_at = datetime.now()
        
        # Log deletion event
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_ARCHIVED if not hard_delete else EventType.ENTITY_UPDATED,
                self.entity_type,
                entity_id,
                hard_delete=hard_delete
            )
        
        return True
    
    async def list(
        self,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """List entities with optional filtering."""
        entities = list(self._storage.values())
        
        # Filter by state if specified
        if state:
            state_enum = EntityState(state) if isinstance(state, str) else state
            entities = [e for e in entities if e.state == state_enum]
        
        # Sort by creation time (newest first)
        entities.sort(key=lambda e: e.created_at, reverse=True)
        
        # Apply pagination
        start = offset
        end = offset + limit
        return entities[start:end]
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[T]:
        """Search entities by text in specified fields."""
        if not fields:
            fields = ['name']
        
        entities = list(self._storage.values())
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
        if not state:
            return len(self._storage)
        
        state_enum = EntityState(state) if isinstance(state, str) else state
        return sum(1 for entity in self._storage.values() if entity.state == state_enum)
    
    def clear(self):
        """Clear all entities (for testing)."""
        self._storage.clear()
        self._next_id = 1


class InMemoryAgentRepository(InMemoryRepository):
    """In-memory agent repository with agent-specific methods."""
    
    async def find_by_capability(self, tool_name: str) -> List[T]:
        """Find agents that have access to a specific tool."""
        agents = list(self._storage.values())
        results = []
        
        for agent in agents:
            if hasattr(agent, 'available_tools') and tool_name in agent.available_tools:
                results.append(agent)
        
        return results
    
    async def find_by_context_document(self, document_name: str) -> List[T]:
        """Find agents that use a specific context document."""
        agents = list(self._storage.values())
        results = []
        
        for agent in agents:
            if hasattr(agent, 'context_documents') and document_name in agent.context_documents:
                results.append(agent)
        
        return results


class InMemoryTaskRepository(InMemoryRepository):
    """In-memory task repository with task-specific methods."""
    
    async def find_by_status(self, status: str) -> List[T]:
        """Find tasks by their current status."""
        tasks = list(self._storage.values())
        results = []
        
        for task in tasks:
            if hasattr(task, 'metadata') and task.metadata.get('status') == status:
                results.append(task)
        
        return results
    
    async def find_by_agent(self, agent_id: int) -> List[T]:
        """Find tasks assigned to a specific agent."""
        tasks = list(self._storage.values())
        results = []
        
        for task in tasks:
            if hasattr(task, 'metadata') and task.metadata.get('agent_id') == agent_id:
                results.append(task)
        
        return results