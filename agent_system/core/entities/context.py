"""Context document entity implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from agent_system.core.entities.base import Entity, EntityState
from agent_system.core.events.event_types import EntityType


class ContextCategory(str, Enum):
    """Context document categories."""
    SYSTEM = "system"
    GUIDE = "guide"
    REFERENCE = "reference"
    EXAMPLE = "example"
    PATTERN = "pattern"
    SPECIFICATION = "specification"
    KNOWLEDGE = "knowledge"
    USER = "user"


class ContextFormat(str, Enum):
    """Context document formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"
    YAML = "yaml"
    CODE = "code"


class ContextEntity(Entity):
    """Entity representation of a context document."""
    
    def __init__(
        self,
        entity_id: int,
        name: str,
        title: str,
        content: str,
        category: ContextCategory,
        format: ContextFormat = ContextFormat.MARKDOWN,
        tags: Optional[List[str]] = None,
        parent_document_id: Optional[int] = None,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            entity_type=EntityType.DOCUMENT,
            version=version,
            state=state,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.title = title
        self.content = content
        self.category = category
        self.format = format
        self.tags = tags or []
        self.parent_document_id = parent_document_id
        
        # Context-specific tracking
        self.access_count = 0
        self.last_accessed = None
        self.referenced_by: List[int] = []  # Entities that reference this doc
    
    async def validate(self) -> bool:
        """Validate context document configuration."""
        # Basic validation
        if not self.name or not self.title or not self.content:
            return False
        
        # Validate category and format
        if not isinstance(self.category, ContextCategory):
            return False
        
        if not isinstance(self.format, ContextFormat):
            return False
        
        # Ensure content is not empty
        if len(self.content.strip()) < 10:
            return False
        
        return True
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert context entity to dictionary."""
        base_dict = await super().to_dict()
        base_dict.update({
            "title": self.title,
            "content": self.content,
            "category": self.category.value,
            "format": self.format.value,
            "tags": self.tags,
            "parent_document_id": self.parent_document_id,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "referenced_by": self.referenced_by
        })
        return base_dict
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'ContextEntity':
        """Create context entity from dictionary."""
        entity = cls(
            entity_id=data["entity_id"],
            name=data["name"],
            title=data["title"],
            content=data["content"],
            category=ContextCategory(data["category"]),
            format=ContextFormat(data.get("format", "markdown")),
            tags=data.get("tags", []),
            parent_document_id=data.get("parent_document_id"),
            version=data.get("version", "1.0.0"),
            state=EntityState(data.get("state", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Restore relationships and tracking
        entity.relationships = data.get("relationships", {})
        entity.access_count = data.get("access_count", 0)
        entity.last_accessed = (
            datetime.fromisoformat(data["last_accessed"]) 
            if data.get("last_accessed") else None
        )
        entity.referenced_by = data.get("referenced_by", [])
        
        return entity
    
    async def record_access(self, accessing_entity_id: int) -> bool:
        """Record an access to this context document."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        
        if accessing_entity_id not in self.referenced_by:
            self.referenced_by.append(accessing_entity_id)
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.CONTEXT_ACCESSED,
                EntityType.DOCUMENT,
                self.entity_id,
                accessing_entity_id=accessing_entity_id
            )
        
        return True
    
    async def update_content(self, new_content: str) -> bool:
        """Update the document content with versioning."""
        old_content = self.content
        self.content = new_content
        self.updated_at = datetime.now()
        
        # Increment version
        version_parts = self.version.split('.')
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        self.version = '.'.join(version_parts)
        
        if self.event_manager:
            await self.event_manager.log_event(
                EventType.ENTITY_UPDATED,
                EntityType.DOCUMENT,
                self.entity_id,
                update_type="content_updated",
                version=self.version,
                content_length_old=len(old_content),
                content_length_new=len(new_content)
            )
        
        return True
    
    async def add_tag(self, tag: str) -> bool:
        """Add a tag to the document."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.DOCUMENT,
                    self.entity_id,
                    update_type="tag_added",
                    tag=tag
                )
            
            return True
        return False
    
    async def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the document."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.DOCUMENT,
                    self.entity_id,
                    update_type="tag_removed",
                    tag=tag
                )
            
            return True
        return False
    
    def get_word_count(self) -> int:
        """Get the word count of the document content."""
        return len(self.content.split())
    
    def search_content(self, search_term: str) -> bool:
        """Check if a search term exists in the document."""
        return search_term.lower() in self.content.lower()