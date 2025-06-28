"""Process-specific entity manager."""

from typing import Dict, List, Optional, Any
import json
import aiosqlite

from agent_system.core.entities.base import Entity
from .process import ProcessEntity, ProcessType
from agent_system.core.events.event_types import EntityType
from agent_system.core.events.event_manager import EventManager
from .base_manager import BaseManager


class ProcessManager(BaseManager):
    """Manager for process entities with specialized process operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.PROCESS,
            entity_class=ProcessEntity,
            event_manager=event_manager
        )
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search processes by name, description, or implementation path."""
        if not fields:
            fields = ['name', 'description', 'implementation_path']
        
        return await super().search(search_term, fields, limit)
    
    async def find_by_type(self, process_type: ProcessType) -> List[ProcessEntity]:
        """Find processes by their type."""
        processes = await self.list(limit=1000)
        
        results = []
        for process in processes:
            if isinstance(process, ProcessEntity) and process.process_type == process_type:
                results.append(process)
        
        return results
    
    async def find_by_trigger(self, trigger: str) -> List[ProcessEntity]:
        """Find processes triggered by a specific event or tool."""
        processes = await self.list(limit=1000)
        
        results = []
        for process in processes:
            if isinstance(process, ProcessEntity) and trigger in (process.triggers or []):
                results.append(process)
        
        return results
    
    async def find_requiring_tool(self, tool_name: str) -> List[ProcessEntity]:
        """Find processes that require a specific tool."""
        processes = await self.list(limit=1000)
        
        results = []
        for process in processes:
            if isinstance(process, ProcessEntity) and tool_name in (process.required_tools or []):
                results.append(process)
        
        return results
    
    async def find_requiring_context(self, context_name: str) -> List[ProcessEntity]:
        """Find processes that require specific context."""
        processes = await self.list(limit=1000)
        
        results = []
        for process in processes:
            if isinstance(process, ProcessEntity) and context_name in (process.required_context or []):
                results.append(process)
        
        return results
    
    async def find_rollback_capable(self) -> List[ProcessEntity]:
        """Find processes that support rollback."""
        processes = await self.list(limit=1000)
        
        results = []
        for process in processes:
            if isinstance(process, ProcessEntity) and process.can_rollback:
                results.append(process)
        
        return results
    
    async def get_default_process(self) -> Optional[ProcessEntity]:
        """Get the default neutral task process."""
        default_processes = await self.find_by_type(ProcessType.DEFAULT)
        return default_processes[0] if default_processes else None
    
    async def add_trigger(self, process_id: int, trigger: str) -> bool:
        """Add a trigger to a process."""
        process = await self.get(process_id)
        if not process or not isinstance(process, ProcessEntity):
            return False
        
        current_triggers = process.triggers or []
        if trigger not in current_triggers:
            updated_triggers = current_triggers + [trigger]
            return await self.update(process, triggers=updated_triggers)
        
        return True
    
    async def remove_trigger(self, process_id: int, trigger: str) -> bool:
        """Remove a trigger from a process."""
        process = await self.get(process_id)
        if not process or not isinstance(process, ProcessEntity):
            return False
        
        current_triggers = process.triggers or []
        if trigger in current_triggers:
            updated_triggers = [t for t in current_triggers if t != trigger]
            return await self.update(process, triggers=updated_triggers)
        
        return True
    
    async def update_parameters_schema(self, process_id: int, schema: Dict[str, Any]) -> bool:
        """Update a process's parameter schema."""
        process = await self.get(process_id)
        if not process or not isinstance(process, ProcessEntity):
            return False
        
        return await self.update(process, parameters_schema=schema)
    
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
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
    
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get process-specific data."""
        cursor = await db.execute(
            "SELECT * FROM processes WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON fields
            for field in ['parameters', 'steps', 'rollback_steps', 'permissions']:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except:
                        data[field] = {} if field == 'parameters' else []
            
            # Map database fields to entity fields
            if 'parameters' in data:
                data['parameters_schema'] = data['parameters']
            
            return data
        return None
    
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update process-specific fields."""
        if not isinstance(entity, ProcessEntity):
            return
        
        if any(field in updates for field in ['description', 'parameters_schema']):
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
    
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete process-specific record."""
        await db.execute("DELETE FROM processes WHERE id = ?", (entity_id,))