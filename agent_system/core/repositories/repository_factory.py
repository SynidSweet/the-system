"""Factory for creating repository instances."""

from typing import Dict, Type, TypeVar, Optional
from enum import Enum

from ..events.event_types import EntityType
from ..events.event_manager import EventManager
from .repository_interface import Repository
from .agent_repository import AgentRepository
from .task_repository import TaskRepository
from .memory_repository import InMemoryAgentRepository, InMemoryTaskRepository

T = TypeVar('T', bound=Repository)


class RepositoryFactory:
    """Factory for creating and managing repository instances."""
    
    _repositories: Dict[EntityType, Type[Repository]] = {
        EntityType.AGENT: AgentRepository,
        EntityType.TASK: TaskRepository,
        # Add other repositories here as they're implemented
    }
    
    _instances: Dict[str, Repository] = {}
    
    @classmethod
    def create_repository(
        cls,
        entity_type: EntityType,
        db_path: str,
        event_manager: Optional[EventManager] = None,
        use_singleton: bool = True,
        use_memory: bool = False
    ) -> Repository:
        """Create a repository instance for the specified entity type."""
        
        # Create cache key for singleton pattern
        cache_key = f"{entity_type.value}_{db_path}"
        
        # Return existing instance if using singleton pattern
        if use_singleton and cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Choose repository implementation
        if use_memory:
            # Use in-memory repository for testing
            if entity_type == EntityType.AGENT:
                from .agent_repository import AgentRepository
                from .agent import AgentEntity
                repository = InMemoryAgentRepository(entity_type, AgentEntity, event_manager)
            elif entity_type == EntityType.TASK:
                from .task_repository import TaskRepository
                from .task import TaskEntity
                repository = InMemoryTaskRepository(entity_type, TaskEntity, event_manager)
            else:
                raise ValueError(f"No in-memory repository implementation for entity type: {entity_type}")
        else:
            # Use database repository
            repo_class = cls._repositories.get(entity_type)
            if not repo_class:
                raise ValueError(f"No repository implementation found for entity type: {entity_type}")
            
            # Create new instance
            repository = repo_class(db_path=db_path, event_manager=event_manager)
        
        # Cache if using singleton pattern
        if use_singleton:
            cls._instances[cache_key] = repository
        
        return repository
    
    @classmethod
    def register_repository(cls, entity_type: EntityType, repository_class: Type[Repository]):
        """Register a new repository class for an entity type."""
        cls._repositories[entity_type] = repository_class
    
    @classmethod
    def get_available_types(cls) -> list[EntityType]:
        """Get list of entity types with available repositories."""
        return list(cls._repositories.keys())
    
    @classmethod
    def clear_cache(cls):
        """Clear the repository instance cache."""
        cls._instances.clear()


class RepositoryManager:
    """Manages multiple repositories with shared configuration."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        self.db_path = db_path
        self.event_manager = event_manager
        self._repositories: Dict[EntityType, Repository] = {}
    
    def get_repository(self, entity_type: EntityType) -> Repository:
        """Get or create a repository for the specified entity type."""
        if entity_type not in self._repositories:
            self._repositories[entity_type] = RepositoryFactory.create_repository(
                entity_type=entity_type,
                db_path=self.db_path,
                event_manager=self.event_manager,
                use_singleton=False
            )
        
        return self._repositories[entity_type]
    
    @property
    def agents(self) -> AgentRepository:
        """Get the agent repository."""
        return self.get_repository(EntityType.AGENT)
    
    @property
    def tasks(self) -> TaskRepository:
        """Get the task repository."""
        return self.get_repository(EntityType.TASK)
    
    # Add properties for other repositories as they're implemented
    
    def close_all(self):
        """Close all repository connections if needed."""
        # For now, repositories don't maintain persistent connections
        # But this provides a hook for future implementations
        pass