"""Task-related API endpoints for task management and monitoring."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from agent_system.core.entities import TaskEntity, TaskState
from agent_system.config.database import DatabaseManager
from agent_system.api.exceptions import (
    EntityNotFoundError, 
    ValidationError, 
    RuntimeError as AgentRuntimeError
)


# Request/Response models
class TaskSubmission(BaseModel):
    instruction: str
    agent_type: Optional[str] = None
    priority: int = 0
    max_execution_time: int = 300


class TaskResponse(BaseModel):
    task_id: int
    tree_id: int
    status: TaskState
    created_at: datetime


# Type alias for backward compatibility
TaskStatus = TaskState

# Dependencies
def get_database():
    """Get database instance"""
    from agent_system.api.main import database
    return database


def get_runtime_integration():
    """Get runtime integration instance"""
    from agent_system.api.startup import get_runtime_integration as _get_runtime
    return _get_runtime()


def get_websocket_manager():
    """Get WebSocket connection manager"""
    from agent_system.api.websocket.handlers import manager
    return manager


# Create router
router = APIRouter()


@router.post("", response_model=TaskResponse)
async def submit_task(
    submission: TaskSubmission,
    database: DatabaseManager = Depends(get_database),
    runtime = Depends(get_runtime_integration),
    ws_manager = Depends(get_websocket_manager)
):
    """Submit a new task for execution"""
    if not runtime:
        raise AgentRuntimeError("Runtime integration not initialized")
    
    # Validate submission
    if not submission.instruction.strip():
        raise ValidationError("Task instruction cannot be empty")
    
    # Create task using the runtime engine
    task_id = await runtime.create_task(
        instruction=submission.instruction,
        parent_task_id=None,
        agent_type=submission.agent_type,
        priority=submission.priority,
        max_execution_time=submission.max_execution_time
    )
    
    # Get task details for response
    task = await database.tasks.get_by_id(task_id)
    if not task:
        raise EntityNotFoundError(f"Task {task_id} not found after creation")
    
    # Broadcast task creation to WebSocket clients
    await ws_manager.broadcast(json.dumps({
        "type": "task_created",
        "task_id": task_id,
        "tree_id": task.tree_id
    }))
    
    return TaskResponse(
        task_id=task_id,
        tree_id=task.tree_id,
        status=task.status,
        created_at=task.created_at
    )


@router.get("/active")
async def get_active_tasks(database: DatabaseManager = Depends(get_database)):
    """Get all active task trees"""
    try:
        # Get active tasks from database directly
        active_tasks = await database.tasks.get_active_tasks()
        
        # Group by tree_id
        trees = {}
        for task in active_tasks:
            if task.tree_id not in trees:
                trees[task.tree_id] = {
                    "tree_id": task.tree_id,
                    "tasks": [],
                    "started_at": task.created_at,
                    "status": "active"
                }
            trees[task.tree_id]["tasks"].append(task.model_dump())
        
        return {"active_trees": list(trees.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_task_trees(database: DatabaseManager = Depends(get_database)):
    """Get all task trees including completed ones"""
    try:
        # Get all root tasks (tasks with no parent)
        all_tasks = await database.tasks.get_all_root_tasks()
        
        # For each root task, get the full tree
        trees = []
        for root_task in all_tasks:
            # Get all tasks in this tree
            tree_tasks = await database.tasks.get_by_tree_id(root_task.tree_id)
            
            # Build tree structure
            tree = {
                "tree_id": root_task.tree_id,
                "tasks": [task.model_dump() for task in tree_tasks],
                "started_at": root_task.created_at.isoformat() if root_task.created_at else None,
                "status": root_task.status.value if hasattr(root_task.status, 'value') else root_task.status
            }
            trees.append(tree)
        
        return {"all_trees": trees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree/{tree_id}")
async def get_task_tree(tree_id: int, database: DatabaseManager = Depends(get_database)):
    """Get all tasks in a tree with hierarchical structure"""
    try:
        tasks = await database.tasks.get_by_tree_id(tree_id)
        
        # Build hierarchical structure
        task_dict = {task.id: task.model_dump() for task in tasks}
        
        # Add children to each task
        for task in tasks:
            task_dict[task.id]["children"] = []
        
        # Link children to parents
        root_tasks = []
        for task in tasks:
            if task.parent_task_id and task.parent_task_id in task_dict:
                task_dict[task.parent_task_id]["children"].append(task_dict[task.id])
            else:
                root_tasks.append(task_dict[task.id])
        
        return {"tree_id": tree_id, "tasks": root_tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree/{tree_id}/messages")
async def get_tree_messages(tree_id: int, database: DatabaseManager = Depends(get_database)):
    """Get all messages for tasks in a tree"""
    try:
        # Get all tasks in the tree
        tasks = await database.tasks.get_by_tree_id(tree_id)
        task_ids = [task.id for task in tasks]
        
        # Get messages for all tasks
        all_messages = []
        for task_id in task_ids:
            messages = await database.messages.get_by_task_id(task_id)
            
            # Add task context to each message
            for msg in messages:
                msg_dict = msg.model_dump()
                msg_dict["task_id"] = task_id
                
                # Find the task for this message
                task = next((t for t in tasks if t.id == task_id), None)
                if task:
                    msg_dict["task_instruction"] = task.instruction[:100] + "..." if len(task.instruction) > 100 else task.instruction
                
                all_messages.append(msg_dict)
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x.get("timestamp", ""))
        
        return {
            "tree_id": tree_id,
            "message_count": len(all_messages),
            "messages": all_messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task_status(
    task_id: int,
    database: DatabaseManager = Depends(get_database),
    runtime = Depends(get_runtime_integration)
):
    """Get detailed status of a specific task"""
    try:
        task = await database.tasks.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get task tree info
        tree_tasks = await database.tasks.get_by_tree_id(task.tree_id)
        
        # Get recent messages
        messages = await database.messages.get_by_task_id(task_id)
        recent_messages = messages[-5:] if messages else []
        
        # Get runtime status if available
        runtime_active = False
        if runtime and runtime.runtime_engine:
            runtime_active = task_id in runtime.runtime_engine.active_agents
        
        return {
            "task": task.model_dump(),
            "tree_info": {
                "tree_id": task.tree_id,
                "total_tasks": len(tree_tasks),
                "completed_tasks": len([t for t in tree_tasks if t.status == TaskStatus.COMPLETE]),
                "failed_tasks": len([t for t in tree_tasks if t.status == TaskStatus.FAILED]),
                "active_tasks": len([t for t in tree_tasks if t.status in [TaskStatus.RUNNING, TaskStatus.QUEUED]])
            },
            "recent_messages": [msg.model_dump() for msg in recent_messages],
            "is_running": runtime_active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tree/{tree_id}")
async def cancel_task_tree(
    tree_id: int,
    database: DatabaseManager = Depends(get_database),
    runtime = Depends(get_runtime_integration),
    ws_manager = Depends(get_websocket_manager)
):
    """Cancel all tasks in a tree"""
    try:
        # Get all tasks in the tree
        tree_tasks = await database.tasks.get_by_tree_id(tree_id)
        
        # Cancel each task
        for task in tree_tasks:
            if task.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]:
                await database.tasks.update_status(task.id, TaskStatus.CANCELLED)
                
                # Also update runtime state if available
                if runtime and runtime.runtime_engine:
                    await runtime.runtime_engine.update_task_state(
                        task.id,
                        TaskState.FAILED,
                        {"reason": "Tree cancelled"}
                    )
        
        await ws_manager.broadcast(f"tree_cancelled:{tree_id}")
        return {"message": f"Task tree {tree_id} cancelled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))