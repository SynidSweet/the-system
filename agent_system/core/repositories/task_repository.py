"""Task-specific repository implementation."""

from typing import Dict, List, Optional, Any
import json

from .task import TaskEntity
from ..events.event_types import EntityType
from ..events.event_manager import EventManager
from .base_repository import BaseRepository


class TaskRepository(BaseRepository[TaskEntity]):
    """Repository for task entities with specialized task operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.TASK,
            entity_class=TaskEntity,
            event_manager=event_manager
        )
    
    async def find_by_status(self, status: str) -> List[TaskEntity]:
        """Find tasks by their current status."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if task.metadata.get('status') == status:
                results.append(task)
        
        return results
    
    async def find_by_agent(self, agent_id: int) -> List[TaskEntity]:
        """Find tasks assigned to a specific agent."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if task.metadata.get('agent_id') == agent_id:
                results.append(task)
        
        return results
    
    async def find_by_tree_id(self, tree_id: str) -> List[TaskEntity]:
        """Find all tasks in a task tree."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if task.metadata.get('tree_id') == tree_id:
                results.append(task)
        
        return results
    
    async def find_children(self, parent_task_id: int) -> List[TaskEntity]:
        """Find all child tasks of a parent task."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if task.metadata.get('parent_task_id') == parent_task_id:
                results.append(task)
        
        return results
    
    async def update_status(self, task_id: int, status: str) -> Optional[TaskEntity]:
        """Update a task's status."""
        task = await self.get(task_id)
        if not task:
            return None
        
        updated_metadata = task.metadata.copy()
        updated_metadata['status'] = status
        
        return await self.update(task_id, {'metadata': updated_metadata})
    
    async def assign_agent(self, task_id: int, agent_id: int) -> Optional[TaskEntity]:
        """Assign a task to an agent."""
        task = await self.get(task_id)
        if not task:
            return None
        
        updated_metadata = task.metadata.copy()
        updated_metadata['agent_id'] = agent_id
        
        return await self.update(task_id, {'metadata': updated_metadata})
    
    # Implementation of abstract methods
    async def _insert_type_specific(self, db, entity_id: int, entity_data: Dict[str, Any]):
        """Insert task-specific record."""
        await db.execute("""
            INSERT INTO tasks (id, parent_task_id, tree_id, agent_id, instruction, status, result, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            entity_data.get('parent_task_id'),
            entity_data.get('tree_id', ''),
            entity_data.get('agent_id'),
            entity_data.get('instruction', ''),
            entity_data.get('status', 'pending'),
            entity_data.get('result', ''),
            json.dumps(entity_data.get('task_metadata', {}))
        ))
    
    async def _get_type_specific(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get task-specific data."""
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON metadata
            if 'metadata' in data and data['metadata']:
                try:
                    data['task_metadata'] = json.loads(data['metadata'])
                except:
                    data['task_metadata'] = {}
            else:
                data['task_metadata'] = {}
            return data
        return None
    
    async def _update_type_specific(self, db, entity_id: int, updates: Dict[str, Any]):
        """Update task-specific fields."""
        # Get current task data to merge with updates
        current_data = await self._get_type_specific(db, entity_id)
        if not current_data:
            return
        
        # Merge updates with current data
        final_data = {**current_data, **updates}
        
        await db.execute("""
            UPDATE tasks SET
                parent_task_id = ?,
                tree_id = ?,
                agent_id = ?,
                instruction = ?,
                status = ?,
                result = ?,
                metadata = ?
            WHERE id = ?
        """, (
            final_data.get('parent_task_id'),
            final_data.get('tree_id', ''),
            final_data.get('agent_id'),
            final_data.get('instruction', ''),
            final_data.get('status', 'pending'),
            final_data.get('result', ''),
            json.dumps(final_data.get('task_metadata', {})),
            entity_id
        ))
    
    async def _delete_type_specific(self, db, entity_id: int):
        """Delete task-specific record."""
        await db.execute("DELETE FROM tasks WHERE id = ?", (entity_id,))