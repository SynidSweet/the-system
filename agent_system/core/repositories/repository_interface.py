"""Repository interface definition using Protocol for type safety."""

from typing import Protocol, TypeVar, Generic, Optional, List, Dict, Any
from abc import abstractmethod

T = TypeVar('T')


class Repository(Protocol[T]):
    """Repository interface for data access operations."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        ...
    
    @abstractmethod
    async def get(self, entity_id: int) -> Optional[T]:
        """Retrieve an entity by ID."""
        ...
    
    @abstractmethod
    async def update(self, entity_id: int, updates: Dict[str, Any]) -> Optional[T]:
        """Update an entity with new values."""
        ...
    
    @abstractmethod
    async def delete(self, entity_id: int, hard_delete: bool = False) -> bool:
        """Delete an entity (soft delete by default)."""
        ...
    
    @abstractmethod
    async def list(
        self, 
        state: Optional[str] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[T]:
        """List entities with optional filtering."""
        ...
    
    @abstractmethod
    async def search(
        self, 
        search_term: str, 
        fields: List[str] = None, 
        limit: int = 50
    ) -> List[T]:
        """Search entities by text in specified fields."""
        ...
    
    @abstractmethod
    async def count(self, state: Optional[str] = None) -> int:
        """Count entities with optional state filter."""
        ...


class DatabaseConnection(Protocol):
    """Database connection interface for dependency injection."""
    
    @abstractmethod
    async def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a query with parameters."""
        ...
    
    @abstractmethod
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one result from a query."""
        ...
    
    @abstractmethod
    async def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all results from a query."""
        ...
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        ...
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...