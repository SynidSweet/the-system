"""Tool-specific entity manager."""

from typing import Dict, List, Optional, Any
import json
import aiosqlite

from ..base import Entity
from ..tool import ToolEntity, ToolCategory
from ...events.event_types import EntityType
from ...events.event_manager import EventManager
from .base_manager import BaseManager


class ToolManager(BaseManager):
    """Manager for tool entities with specialized tool operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.TOOL,
            entity_class=ToolEntity,
            event_manager=event_manager
        )
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search tools by name, description, or category."""
        if not fields:
            fields = ['name', 'description']
        
        return await super().search(search_term, fields, limit)
    
    async def find_by_category(self, category: ToolCategory) -> List[ToolEntity]:
        """Find tools by their category."""
        tools = await self.list(limit=1000)
        
        results = []
        for tool in tools:
            if isinstance(tool, ToolEntity) and tool.category == category:
                results.append(tool)
        
        return results
    
    async def find_by_implementation(self, implementation_type: str) -> List[ToolEntity]:
        """Find tools by implementation type (mcp, internal, process, external)."""
        tools = await self.list(limit=1000)
        
        results = []
        for tool in tools:
            if isinstance(tool, ToolEntity) and tool.implementation == implementation_type:
                results.append(tool)
        
        return results
    
    async def find_requiring_validation(self) -> List[ToolEntity]:
        """Find tools that require validation before execution."""
        tools = await self.list(limit=1000)
        
        results = []
        for tool in tools:
            if isinstance(tool, ToolEntity) and tool.requires_validation:
                results.append(tool)
        
        return results
    
    async def find_by_permission(self, permission: str) -> List[ToolEntity]:
        """Find tools that require a specific permission."""
        tools = await self.list(limit=1000)
        
        results = []
        for tool in tools:
            if isinstance(tool, ToolEntity) and permission in tool.permissions:
                results.append(tool)
        
        return results
    
    async def find_process_triggers(self, process_name: str) -> List[ToolEntity]:
        """Find tools that trigger a specific process."""
        tools = await self.list(limit=1000)
        
        results = []
        for tool in tools:
            if isinstance(tool, ToolEntity) and tool.triggers_process == process_name:
                results.append(tool)
        
        return results
    
    async def update_parameters(self, tool_id: int, parameters: Dict[str, Any]) -> bool:
        """Update a tool's parameter schema."""
        tool = await self.get(tool_id)
        if not tool or not isinstance(tool, ToolEntity):
            return False
        
        return await self.update(tool, parameters=parameters)
    
    async def add_permission(self, tool_id: int, permission: str) -> bool:
        """Add a permission requirement to a tool."""
        tool = await self.get(tool_id)
        if not tool or not isinstance(tool, ToolEntity):
            return False
        
        if permission not in tool.permissions:
            updated_permissions = tool.permissions + [permission]
            return await self.update(tool, permissions=updated_permissions)
        
        return True
    
    async def remove_permission(self, tool_id: int, permission: str) -> bool:
        """Remove a permission requirement from a tool."""
        tool = await self.get(tool_id)
        if not tool or not isinstance(tool, ToolEntity):
            return False
        
        if permission in tool.permissions:
            updated_permissions = [p for p in tool.permissions if p != permission]
            return await self.update(tool, permissions=updated_permissions)
        
        return True
    
    async def record_execution(self, tool_id: int, success: bool, execution_time: float) -> bool:
        """Record tool execution statistics."""
        tool = await self.get(tool_id)
        if not tool or not isinstance(tool, ToolEntity):
            return False
        
        # Update execution statistics in metadata
        updated_metadata = tool.metadata.copy()
        updated_metadata['execution_count'] = updated_metadata.get('execution_count', 0) + 1
        
        if success:
            updated_metadata['success_count'] = updated_metadata.get('success_count', 0) + 1
        else:
            updated_metadata['failure_count'] = updated_metadata.get('failure_count', 0) + 1
        
        # Update average execution time
        total_time = updated_metadata.get('total_execution_time', 0.0) + execution_time
        updated_metadata['total_execution_time'] = total_time
        updated_metadata['average_execution_time'] = total_time / updated_metadata['execution_count']
        
        return await self.update(tool, metadata=updated_metadata)
    
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
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
    
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get tool-specific data."""
        cursor = await db.execute(
            "SELECT * FROM tools WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON fields
            for field in ['parameters', 'permissions']:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except:
                        data[field] = {} if field == 'parameters' else []
            
            # Convert category string to enum
            if 'category' in data:
                try:
                    data['category'] = ToolCategory(data['category'])
                except ValueError:
                    data['category'] = ToolCategory.SYSTEM
            
            return data
        return None
    
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update tool-specific fields."""
        if not isinstance(entity, ToolEntity):
            return
        
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
    
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete tool-specific record."""
        await db.execute("DELETE FROM tools WHERE id = ?", (entity_id,))