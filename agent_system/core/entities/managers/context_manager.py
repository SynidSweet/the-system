"""Context document-specific entity manager."""

from typing import Dict, List, Optional, Any
import json
import aiosqlite

from ..base import Entity
from ..context import ContextEntity, ContextCategory, ContextFormat
from ...events.event_types import EntityType
from ...events.event_manager import EventManager
from .base_manager import BaseManager


class ContextManager(BaseManager):
    """Manager for context document entities with specialized document operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.DOCUMENT,
            entity_class=ContextEntity,
            event_manager=event_manager
        )
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search context documents by title, content, or tags."""
        if not fields:
            fields = ['name', 'title', 'content']
        
        return await super().search(search_term, fields, limit)
    
    async def find_by_category(self, category: ContextCategory) -> List[ContextEntity]:
        """Find documents by their category."""
        documents = await self.list(limit=1000)
        
        results = []
        for doc in documents:
            if isinstance(doc, ContextEntity) and doc.category == category:
                results.append(doc)
        
        return results
    
    async def find_by_format(self, format_type: ContextFormat) -> List[ContextEntity]:
        """Find documents by their format."""
        documents = await self.list(limit=1000)
        
        results = []
        for doc in documents:
            if isinstance(doc, ContextEntity) and doc.format == format_type:
                results.append(doc)
        
        return results
    
    async def find_by_tag(self, tag: str) -> List[ContextEntity]:
        """Find documents that have a specific tag."""
        documents = await self.list(limit=1000)
        
        results = []
        for doc in documents:
            if isinstance(doc, ContextEntity) and tag in (doc.tags or []):
                results.append(doc)
        
        return results
    
    async def find_children(self, parent_document_id: int) -> List[ContextEntity]:
        """Find all child documents of a parent document."""
        documents = await self.list(limit=1000)
        
        results = []
        for doc in documents:
            if isinstance(doc, ContextEntity) and doc.parent_document_id == parent_document_id:
                results.append(doc)
        
        return results
    
    async def get_system_documents(self) -> List[ContextEntity]:
        """Get all system-category documents."""
        return await self.find_by_category(ContextCategory.SYSTEM)
    
    async def get_knowledge_documents(self) -> List[ContextEntity]:
        """Get all knowledge-category documents."""
        return await self.find_by_category(ContextCategory.KNOWLEDGE)
    
    async def update_content(self, doc_id: int, content: str) -> bool:
        """Update a document's content."""
        doc = await self.get(doc_id)
        if not doc or not isinstance(doc, ContextEntity):
            return False
        
        return await self.update(doc, content=content)
    
    async def add_tag(self, doc_id: int, tag: str) -> bool:
        """Add a tag to a document."""
        doc = await self.get(doc_id)
        if not doc or not isinstance(doc, ContextEntity):
            return False
        
        current_tags = doc.tags or []
        if tag not in current_tags:
            updated_tags = current_tags + [tag]
            return await self.update(doc, tags=updated_tags)
        
        return True
    
    async def remove_tag(self, doc_id: int, tag: str) -> bool:
        """Remove a tag from a document."""
        doc = await self.get(doc_id)
        if not doc or not isinstance(doc, ContextEntity):
            return False
        
        current_tags = doc.tags or []
        if tag in current_tags:
            updated_tags = [t for t in current_tags if t != tag]
            return await self.update(doc, tags=updated_tags)
        
        return True
    
    async def clone_document(self, doc_id: int, new_name: str, modifications: Optional[Dict[str, Any]] = None) -> Optional[ContextEntity]:
        """Clone a document with optional modifications."""
        original = await self.get(doc_id)
        if not original or not isinstance(original, ContextEntity):
            return None
        
        # Prepare new document data
        clone_data = {
            'title': original.title,
            'content': original.content,
            'category': original.category,
            'format': original.format,
            'tags': (original.tags or []).copy(),
            'metadata': original.metadata.copy()
        }
        
        # Apply modifications
        if modifications:
            clone_data.update(modifications)
        
        return await self.create(new_name, **clone_data)
    
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
        """Create context document-specific record."""
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
    
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get context document-specific data."""
        cursor = await db.execute(
            "SELECT * FROM context_documents WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            
            # Convert category and format strings to enums
            if 'category' in data:
                try:
                    data['category'] = ContextCategory(data['category'])
                except ValueError:
                    data['category'] = ContextCategory.SYSTEM
            
            if 'format' in data:
                try:
                    data['format'] = ContextFormat(data['format'])
                except ValueError:
                    data['format'] = ContextFormat.MARKDOWN
            
            return data
        return None
    
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update context document-specific fields."""
        if not isinstance(entity, ContextEntity):
            return
        
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
    
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete context document-specific record."""
        await db.execute("DELETE FROM context_documents WHERE id = ?", (entity_id,))