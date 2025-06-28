"""Task-specific entity manager."""

from typing import Dict, List, Optional, Any
import json
import aiosqlite

from agent_system.core.entities.base import Entity
from .task import TaskEntity, TaskState
from agent_system.core.events.event_types import EntityType
from agent_system.core.events.event_manager import EventManager
from .base_manager import BaseManager


class TaskManager(BaseManager):
    """Manager for task entities with specialized task operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.TASK,
            entity_class=TaskEntity,
            event_manager=event_manager
        )
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search tasks by instruction, name, or result."""
        if not fields:
            fields = ['name', 'instruction']
        
        return await super().search(search_term, fields, limit)
    
    async def find_by_status(self, task_state: TaskState) -> List[TaskEntity]:
        """Find tasks by their current status."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if isinstance(task, TaskEntity) and task.task_state == task_state:
                results.append(task)
        
        return results
    
    async def find_by_tree(self, tree_id: int) -> List[TaskEntity]:
        """Find all tasks in a task tree."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if isinstance(task, TaskEntity) and task.tree_id == tree_id:
                results.append(task)
        
        return results
    
    async def find_children(self, parent_task_id: int) -> List[TaskEntity]:
        """Find all direct children of a task."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if isinstance(task, TaskEntity) and task.parent_task_id == parent_task_id:
                results.append(task)
        
        return results
    
    async def find_by_agent(self, agent_name: str) -> List[TaskEntity]:
        """Find all tasks assigned to a specific agent."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if isinstance(task, TaskEntity) and task.assigned_agent == agent_name:
                results.append(task)
        
        return results
    
    async def find_by_priority(self, priority: str) -> List[TaskEntity]:
        """Find tasks by priority level."""
        tasks = await self.list(limit=1000)
        
        results = []
        for task in tasks:
            if isinstance(task, TaskEntity) and task.priority == priority:
                results.append(task)
        
        return results
    
    async def find_ready_for_execution(self) -> List[TaskEntity]:
        """Find tasks ready for agent execution."""
        return await self.find_by_status(TaskState.READY_FOR_AGENT)
    
    async def find_waiting_on_dependencies(self) -> List[TaskEntity]:
        """Find tasks waiting on dependencies."""
        return await self.find_by_status(TaskState.WAITING_ON_DEPENDENCIES)
    
    async def update_status(self, task_id: int, new_status: TaskState) -> bool:
        """Update a task's status."""
        task = await self.get(task_id)
        if not task or not isinstance(task, TaskEntity):
            return False
        
        return await self.update(task, task_state=new_status)
    
    async def assign_agent(self, task_id: int, agent_name: str) -> bool:
        """Assign an agent to a task."""
        task = await self.get(task_id)
        if not task or not isinstance(task, TaskEntity):
            return False
        
        return await self.update(task, assigned_agent=agent_name)
    
    async def set_result(self, task_id: int, result: Dict[str, Any]) -> bool:
        """Set the result of a completed task."""
        task = await self.get(task_id)
        if not task or not isinstance(task, TaskEntity):
            return False
        
        return await self.update(task, result=result, task_state=TaskState.COMPLETED)
    
    async def set_error(self, task_id: int, error: str) -> bool:
        """Set error for a failed task."""
        task = await self.get(task_id)
        if not task or not isinstance(task, TaskEntity):
            return False
        
        return await self.update(task, error=error, task_state=TaskState.FAILED)
    
    async def add_subtask(self, parent_task_id: int, subtask_id: int) -> bool:
        """Add a subtask to a parent task."""
        parent_task = await self.get(parent_task_id)
        if not parent_task or not isinstance(parent_task, TaskEntity):
            return False
        
        if subtask_id not in parent_task.subtask_ids:
            updated_subtasks = parent_task.subtask_ids + [subtask_id]
            # Update metadata to store subtask IDs
            updated_metadata = parent_task.metadata.copy()
            updated_metadata['subtask_ids'] = updated_subtasks
            return await self.update(parent_task, metadata=updated_metadata)
        
        return True
    
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
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
    
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get task-specific data."""
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON fields
            for field in ['result', 'metadata']:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except:
                        data[field] = {}
            
            # Map database fields to entity fields
            if 'status' in data:
                data['task_state'] = data['status']
            
            return data
        return None
    
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update task-specific fields."""
        if not isinstance(entity, TaskEntity):
            return
        
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
    
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete task-specific record."""
        await db.execute("DELETE FROM tasks WHERE id = ?", (entity_id,))