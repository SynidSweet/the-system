"""Admin and system management endpoints."""

import asyncio
import json
from pathlib import Path
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from agent_system.config.database import DatabaseManager
from agent_system.core.runtime.state_machine import TaskState
from agent_system.api.exceptions import RuntimeError as AgentRuntimeError


logger = logging.getLogger(__name__)


# Configuration Models
class SystemConfig(BaseModel):
    max_parallel_tasks: int = 3
    step_mode: bool = False
    step_mode_threads: List[int] = []  # Specific threads in step mode
    manual_step_mode: bool = False  # Manual approval for each agent
    max_concurrent_agents: int = 3


class StepCommand(BaseModel):
    task_id: int
    action: str = "continue"  # continue, skip, abort


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


def get_app_state():
    """Get FastAPI app state"""
    from agent_system.api.main import app
    return app.state


# Helper function
async def monitor_initialization_completion(task_id: int):
    """Monitor initialization task and update system state when complete"""
    try:
        database = get_database()
        ws_manager = get_websocket_manager()
        app_state = get_app_state()
        
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            task = await database.tasks.get_by_id(task_id)
            if task and task.status in ["completed", "failed"]:
                app_state.initializing = False
                
                new_state = "ready" if task.status == "completed" else "uninitialized"
                
                # Broadcast state change
                await ws_manager.broadcast(json.dumps({
                    "type": "system_state_change",
                    "state": new_state
                }))
                
                logger.info(f"System initialization {task.status}. New state: {new_state}")
                break
                
    except Exception as e:
        logger.error(f"Error monitoring initialization: {e}")
        app_state.initializing = False


# Create router
router = APIRouter()


# System Statistics
@router.get("/system/stats")
async def get_system_stats(
    database: DatabaseManager = Depends(get_database),
    runtime = Depends(get_runtime_integration)
):
    """Get system statistics"""
    try:
        # Get database stats
        active_tasks = await database.tasks.get_active_tasks()
        recent_messages = await database.messages.get_recent_messages(50)
        
        # Get entity system stats
        entity_stats = {
            "entity_manager_active": True,
            "entities_cached": 0  # Could get from entity manager if needed
        }
        
        # Get runtime system stats
        runtime_stats = {}
        if runtime:
            runtime_stats = await runtime.get_runtime_statistics()
        
        # Calculate task stats from runtime
        task_stats = {
            "running_agents": len(runtime.runtime_engine.active_agents) if runtime and runtime.runtime_engine else 0,
            "queued_tasks": len([t for t in active_tasks if t.status == TaskState.QUEUED]),
            "max_concurrent_agents": runtime.runtime_engine.settings.max_concurrent_agents if runtime and runtime.runtime_engine else 5,
            "is_running": runtime is not None and runtime.runtime_engine is not None
        }
        
        return {
            "task_manager": task_stats,
            "database": {
                "active_tasks": len(active_tasks),
                "recent_messages": len(recent_messages)
            },
            "entity_system": entity_stats,
            "runtime_system": runtime_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Tools
@router.get("/system/tools")
async def list_tools():
    """List all available MCP tools with details"""
    try:
        from tools.base_tool import tool_registry
        
        tools_by_category = {}
        for category in ["core", "system", "custom"]:
            category_tools = []
            for tool in tool_registry.get_tools_by_category(category):
                category_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "permissions": tool.permissions,
                    "category": category
                })
            if category_tools:
                tools_by_category[category] = category_tools
        
        return {"tools": tools_by_category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System State Management
@router.get("/system/state")
async def get_system_state(
    database: DatabaseManager = Depends(get_database),
    app_state = Depends(get_app_state)
):
    """Get current system initialization state"""
    try:
        # Check if knowledge base exists
        knowledge_dir = Path("knowledge")
        has_knowledge = knowledge_dir.exists() and any(knowledge_dir.iterdir())
        
        # Check if core agents exist
        agents = await database.agents.get_all_active()
        has_agents = len(agents) >= 9  # We expect at least 9 core agents
        
        # Determine state
        if not has_knowledge or not has_agents:
            state = "uninitialized"
        elif hasattr(app_state, "initializing") and app_state.initializing:
            state = "initializing"
        else:
            state = "ready"
        
        return {
            "state": state,
            "has_knowledge": has_knowledge,
            "agent_count": len(agents),
            "expected_agents": 9
        }
    except Exception as e:
        logger.error(f"Error checking system state: {e}")
        return {"state": "uninitialized", "error": str(e)}


# System Initialization
@router.post("/system/initialize")
async def initialize_system(
    settings: dict,
    runtime = Depends(get_runtime_integration),
    ws_manager = Depends(get_websocket_manager),
    app_state = Depends(get_app_state)
):
    """Start system initialization with provided settings"""
    try:
        # Mark system as initializing
        app_state.initializing = True
        
        # Broadcast state change
        await ws_manager.broadcast(json.dumps({
            "type": "system_state_change",
            "state": "initializing"
        }))
        
        # Update system config with initialization settings
        if runtime and runtime.runtime_engine:
            runtime.runtime_engine.settings.manual_stepping_enabled = settings.get("manualStepMode", True)
            runtime.runtime_engine.settings.max_concurrent_agents = settings.get("maxConcurrentAgents", 1)
        
        # Create initialization task with proper process
        initialization_task_id = await runtime.create_task(
            instruction="Execute system initialization sequence including knowledge bootstrap and framework establishment",
            parent_task_id=None,
            agent_type="agent_selector",
            priority=1,
            process="system_initialization_process",
            metadata={
                "task_type": "system_initialization",
                "phase": "complete",
                "manual_mode": settings.get("manualStepMode", True),
                "initialization_task": True
            }
        )
        
        logger.info(f"Started system initialization with task {initialization_task_id}")
        
        # The actual initialization will be handled by tasks
        # Monitor completion via task status
        asyncio.create_task(monitor_initialization_completion(initialization_task_id))
        
        return {
            "message": "System initialization started",
            "task_id": initialization_task_id
        }
    except Exception as e:
        app_state.initializing = False
        raise HTTPException(status_code=500, detail=str(e))


# System Configuration
@router.get("/system/config")
async def get_system_config(runtime = Depends(get_runtime_integration)):
    """Get current system configuration"""
    max_concurrent = 5
    step_mode = False
    step_mode_threads = []
    manual_step_mode = False
    
    if runtime and runtime.runtime_engine:
        max_concurrent = runtime.runtime_engine.settings.max_concurrent_agents
        step_mode = runtime.runtime_engine.settings.manual_stepping_enabled
        step_mode_threads = getattr(runtime.runtime_engine.settings, "step_mode_threads", [])
        manual_step_mode = step_mode  # For now, same as step_mode
    
    return {
        "max_parallel_tasks": max_concurrent,
        "step_mode": step_mode,
        "step_mode_threads": step_mode_threads,
        "manual_step_mode": manual_step_mode,
        "max_concurrent_agents": max_concurrent
    }


@router.put("/system/config")
async def update_system_config(
    config: SystemConfig,
    runtime = Depends(get_runtime_integration),
    ws_manager = Depends(get_websocket_manager)
):
    """Update system configuration"""
    try:
        if runtime and runtime.runtime_engine:
            runtime.runtime_engine.settings.max_concurrent_agents = config.max_parallel_tasks
            runtime.runtime_engine.settings.manual_stepping_enabled = config.step_mode
            setattr(runtime.runtime_engine.settings, "step_mode_threads", config.step_mode_threads)
        
        # Broadcast configuration change
        await ws_manager.broadcast(json.dumps({
            "type": "config_updated",
            "config": config.model_dump()
        }))
        
        return {"message": "Configuration updated", "config": config.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Step Mode Management
@router.post("/system/step")
async def handle_step_command(
    command: StepCommand,
    runtime = Depends(get_runtime_integration)
):
    """Handle step mode commands"""
    try:
        if not runtime or not runtime.runtime_engine:
            raise AgentRuntimeError("Runtime engine not available")
        
        if command.action == "continue":
            # Continue task execution (release from manual hold)
            await runtime.runtime_engine.update_task_state(
                command.task_id,
                TaskState.READY_FOR_AGENT
            )
        elif command.action == "skip":
            # Skip task (mark as completed)
            await runtime.runtime_engine.update_task_state(
                command.task_id,
                TaskState.COMPLETED,
                {"skipped": True}
            )
        elif command.action == "abort":
            # Abort task (mark as failed)
            await runtime.runtime_engine.update_task_state(
                command.task_id,
                TaskState.FAILED,
                {"aborted": True}
            )
        else:
            raise ValueError(f"Unknown step action: {command.action}")
        
        return {"message": f"Step command '{command.action}' executed for task {command.task_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Admin Controls
@router.post("/admin/shutdown")
async def graceful_shutdown(ws_manager = Depends(get_websocket_manager)):
    """Initiate graceful system shutdown"""
    try:
        await ws_manager.broadcast("system_shutdown")
        # In a real implementation, this would trigger shutdown
        return {"message": "Graceful shutdown initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/restart")
async def restart_system(ws_manager = Depends(get_websocket_manager)):
    """Restart the system (for self-modifications)"""
    try:
        await ws_manager.broadcast("system_restart")
        # In a real implementation, this would trigger restart
        return {"message": "System restart initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))