#!/usr/bin/env python3
"""
FastAPI application for the self-improving agent system.

This provides:
- REST API endpoints for task submission and management
- WebSocket connections for real-time updates
- Admin endpoints for system control
- Health checks and monitoring
"""

import asyncio
import sys
from pathlib import Path
from contextlib import asynccontextmanager
import logging

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import json
import logging
from typing import Optional
from datetime import datetime

from api.models import TaskSubmission, TaskResponse, TaskStatus
from core.database_manager import database
from core.websocket_messages import WebSocketMessage, MessageType
from core.event_integration import event_integration
from core.entities.entity_manager import EntityManager
from core.runtime.runtime_integration import initialize_runtime_integration, get_runtime_integration, RuntimeIntegration
from core.runtime.state_machine import TaskState
from config.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    print("🚀 Starting Agent System API...")
    
    # Initialize database
    await database.initialize()
    
    # Create basic schema if tables don't exist
    try:
        # Test if agents table exists
        await database.execute_query("SELECT 1 FROM agents LIMIT 1")
    except:
        # Tables don't exist, create them with full entity-based schema
        print("📋 Creating database schema...")
        
        # Read and execute the init schema
        from pathlib import Path
        schema_path = Path(__file__).parent.parent / "init_schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            from config.database import db_manager
            await db_manager.execute_script(schema_sql)
            print("✅ Database schema created from init_schema.sql")
        else:
            # Fallback: create minimal schema if init_schema.sql not found
            print("⚠️  init_schema.sql not found, creating minimal schema")
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    state TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    instruction TEXT,
                    context_documents TEXT DEFAULT '[]',
                    available_tools TEXT DEFAULT '[]',
                    permissions TEXT DEFAULT '[]',
                    constraints TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create other required tables
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_task_id INTEGER,
                    tree_id INTEGER,
                    agent_id INTEGER,
                    instruction TEXT,
                    status TEXT DEFAULT 'created',
                    result TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    message_type TEXT,
                    content TEXT,
                    metadata TEXT DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    source TEXT,
                    target TEXT,
                    data TEXT DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    type TEXT,
                    config TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS context_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    title TEXT,
                    category TEXT DEFAULT 'general',
                    content TEXT,
                    format TEXT DEFAULT 'markdown',
                    version TEXT DEFAULT '1.0.0'
                )
            """)
            
            await database.execute_command("""
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    category TEXT DEFAULT 'system',
                    implementation TEXT,
                    parameters TEXT DEFAULT '{}',
                    permissions TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            print("✅ Minimal database schema created")
    
    # Initialize event system integration
    await event_integration.initialize()
    
    # Initialize entity system (Phase 3)
    print("🔄 Initializing Entity Management Layer...")
    from core.entities.entity_manager import EntityManager
    entity_manager = EntityManager(
        db_path="data/agent_system.db",
        event_manager=event_integration.event_manager
    )
    print("✅ Entity system initialized")
    
    # Initialize runtime system (Phase 4)
    print("🔄 Initializing Process Framework & Runtime Engine...")
    global runtime_integration
    runtime_integration = await initialize_runtime_integration(
        event_manager=event_integration.event_manager,
        entity_manager=entity_manager,
        mode="runtime_first"  # Force runtime-only mode
    )
    print("✅ Runtime engine initialized with process framework (runtime-only mode)")
    
    # Initialize tool system (Phase 5)
    print("🔄 Initializing Optional Tooling System...")
    from tools.mcp_servers.startup import initialize_tool_system
    global tool_system_manager
    tool_system_manager = await initialize_tool_system(
        db_manager=database,
        entity_manager=entity_manager,
        config={
            "allowed_file_paths": ["/home/ubuntu/system.petter.ai"],
            "github": {},
            "user_interface": {}
        }
    )
    print("✅ Tool system initialized with MCP servers")
    
    # Initialize and register legacy tools
    from tools import initialize_tools
    initialize_tools()
    
    # Self-improvement engine removed in Phase 8 cleanup
    # Functionality integrated into entity framework and event system
    
    # No need to start old task manager - runtime engine handles everything
    
    print("✅ Agent System API is ready!")
    
    yield
    
    # Cleanup
    print("🛑 Shutting down Agent System API...")
    
    # Shutdown tool system
    if tool_system_manager:
        from tools.mcp_servers.startup import shutdown_tool_system
        await shutdown_tool_system()
    
    # Shutdown runtime
    if runtime_integration:
        await runtime_integration.shutdown()
    
    await event_integration.shutdown()
    await database.disconnect()
    print("✅ Shutdown complete")


# Global runtime integration instance
runtime_integration: Optional[RuntimeIntegration] = None

# Global tool system manager
tool_system_manager = None


# Create FastAPI app
app = FastAPI(
    title="Self-Improving Agent System",
    description="A recursive agent system that can solve complex problems by breaking them down and spawning specialized agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://system.petter.ai",
        "http://system.petter.ai",
        "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Improvement dashboard removed in Phase 8 cleanup
# Self-improvement now integrated into entity framework


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)
    
    async def broadcast_message(self, ws_message: WebSocketMessage):
        """Broadcast a structured WebSocket message"""
        await self.broadcast(ws_message.to_json())
    
    async def broadcast_user_message(self, message_data: dict):
        """Broadcast user message to all connected clients"""
        import json
        message_json = json.dumps(message_data)
        await self.broadcast(message_json)


manager = ConnectionManager()

# Websocket manager is now global
# (Previously was: task_manager.websocket_manager = manager)


# API Routes

@app.get("/")
async def root():
    """Welcome message"""
    return {
        "message": "Welcome to the Self-Improving Agent System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """System health check"""
    try:
        # Check database
        agents = await database.agents.get_all_active()
        
        # Check runtime integration if available
        runtime_stats = {}
        runtime = get_runtime_integration()
        if runtime:
            runtime_stats = {
                "processes_registered": len(runtime.process_registry.processes) if runtime.process_registry else 0
            }
        
        return {
            "status": "healthy",
            "database": "connected",
            "active_agents": len(agents),
            "runtime": runtime_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Task Management Endpoints

@app.post("/tasks", response_model=TaskResponse)
async def submit_task(submission: TaskSubmission):
    """Submit a new task for execution"""
    try:
        if not runtime_integration:
            raise RuntimeError("Runtime integration not initialized")
        
        # Create task using the runtime engine
        # Filter out parameters that TaskEntity doesn't accept
        task_params = {
            "instruction": submission.instruction,
            "parent_task_id": None,
            "priority": f"priority_{submission.priority}" if submission.priority else "normal",
        }
        
        # Add metadata with agent_type and max_execution_time if provided
        metadata = submission.metadata or {}
        if submission.agent_type:
            metadata["requested_agent_type"] = submission.agent_type
        if submission.max_execution_time:
            metadata["max_execution_time"] = submission.max_execution_time
        
        if metadata:
            task_params["metadata"] = metadata
        
        task_id = await runtime_integration.create_task(**task_params)
        
        # Get task details for response
        task = await database.tasks.get_by_id(task_id)
        if not task:
            raise RuntimeError(f"Task {task_id} not found after creation")
        
        # Broadcast task creation to WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "task_created",
            "task_id": task_id,
            "tree_id": task.get("tree_id", task_id)  # Use task_id as tree_id if not set
        }))
        
        return TaskResponse(
            task_id=str(task_id),
            tree_id=str(task.get("tree_id", task_id)),
            status=TaskStatus(task.get("status", "created")),
            created_at=datetime.fromisoformat(task.get("created_at", datetime.now().isoformat())),
            instruction=submission.instruction,
            agent_type=submission.agent_type,
            metadata=submission.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks/active")
async def get_active_tasks():
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
            trees[task.tree_id]["tasks"].append(task)
        
        return {"active_trees": list(trees.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/all")
async def get_all_task_trees():
    """Get all task trees including completed ones"""
    try:
        # Get all root tasks (tasks with no parent)
        all_tasks = await database.tasks.get_all_root_tasks()
        
        # For each root task, get the full tree
        trees = []
        for root_task in all_tasks:
            # Get all tasks in this tree (root_task is a dict)
            tree_id = root_task.get("tree_id", root_task.get("id"))
            tree_tasks = await database.tasks.get_by_tree_id(str(tree_id))
            
            # Calculate tree metadata
            has_running_tasks = any(task.get("status") in ["running", "agent_responding", "waiting_on_dependencies"] for task in tree_tasks)
            has_completed_tasks = any(task.get("status") in ["completed", "failed"] for task in tree_tasks)
            
            # Build tree structure
            tree = {
                "tree_id": tree_id,
                "tasks": tree_tasks,  # Already dicts from database
                "started_at": None,  # Tasks table doesn't have created_at column
                "created_at": "2025-06-25T20:00:00",  # Default timestamp for display
                "status": root_task.get("status"),
                "has_running_tasks": has_running_tasks,
                "has_completed_tasks": has_completed_tasks,
                "task_count": len(tree_tasks),
                "instruction": root_task.get("instruction", ""),
                "root_instruction": root_task.get("instruction", "No instruction")
            }
            trees.append(tree)
        
        return {"all_trees": trees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/tree/{tree_id}")
async def get_task_tree(tree_id: int):
    """Get all tasks in a tree with hierarchical structure"""
    try:
        tasks = await database.tasks.get_by_tree_id(tree_id)
        
        # Build hierarchical structure
        task_dict = {task.get('id'): task for task in tasks}
        
        # Add children to each task
        for task in tasks:
            task_dict[task.id]["children"] = []
        
        for task in tasks:
            if task.parent_task_id and task.parent_task_id in task_dict:
                task_dict[task.parent_task_id]["children"].append(task_dict[task.id])
        
        # Return root tasks (no parent)
        root_tasks = [task_dict[task.id] for task in tasks if not task.parent_task_id]
        
        return {"tree_id": tree_id, "tasks": root_tasks}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks/tree/{tree_id}/messages")
async def get_tree_messages(tree_id: int):
    """Get all messages for a task tree"""
    try:
        # Get all tasks in the tree (returns list of dicts)
        tree_tasks = await database.tasks.get_by_tree_id(str(tree_id))
        task_ids = [task.get("id") for task in tree_tasks if task.get("id")]
        
        # Get all messages for these tasks
        messages = []
        for task_id in task_ids:
            task_messages = await database.messages.get_by_task_id(str(task_id))
            for msg in task_messages:
                # Get task info for agent name (msg is a dict)
                task = next((t for t in tree_tasks if t.get("id") == task_id), None)
                agent_name = "Unknown"
                if task and task.get("agent_id"):
                    agent = await database.agents.get_by_id(str(task.get("agent_id")))
                    if agent:
                        agent_name = agent.get("name", "Unknown")
                
                # Convert to WebSocket message format based on message type
                msg_type = msg.get("message_type", "").lower()
                
                # Build content based on message type
                content = {}
                msg_content = msg.get("content", "")
                if msg_type == "system_event" and msg_content.startswith("Starting task execution:"):
                    # This is an agent_started message
                    ws_msg_type = "agent_started"
                    instruction = msg_content.replace("Starting task execution: ", "")
                    content = {
                        "instruction": instruction,
                        "status": "initializing"
                    }
                elif msg_type == "error" and msg_content.startswith("Task failed:"):
                    # This is an error message
                    ws_msg_type = "agent_error"
                    error_msg = msg_content.replace("Task failed: ", "")
                    content = {"error": error_msg}
                elif msg_type == "tool_call":
                    ws_msg_type = "agent_tool_call"
                    # Parse metadata if it's a string
                    metadata = msg.get("metadata", {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    content = {
                        "tool_name": metadata.get("tool_name", ""),
                        "tool_input": metadata.get("parameters", {})
                    }
                elif msg_type == "tool_response":
                    ws_msg_type = "agent_tool_result"
                    tool_result = msg_content.replace("Tool result: ", "")
                    # Parse metadata if it's a string
                    metadata = msg.get("metadata", {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    content = {
                        "tool_name": metadata.get("tool_name", ""),
                        "tool_output": tool_result,
                        "success": metadata.get("success", True)
                    }
                elif msg_type == "agent_response":
                    ws_msg_type = "agent_thinking"
                    content = {"thought": msg_content}
                else:
                    # Default format
                    ws_msg_type = msg_type
                    # Parse metadata if it's a string
                    metadata = msg.get("metadata", {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    content = metadata if metadata else {"message": msg_content}
                
                ws_msg = {
                    "type": ws_msg_type,
                    "task_id": task_id,
                    "tree_id": tree_id,
                    "agent_name": agent_name,
                    "content": content,
                    "timestamp": msg.get("timestamp")
                }
                messages.append(ws_msg)
        
        # Sort by timestamp
        messages.sort(key=lambda x: x["timestamp"] or "")
        
        return {"tree_id": tree_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: int):
    """Get detailed status of a specific task"""
    try:
        # Convert to string for database lookup
        task = await database.tasks.get_by_id(str(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get task tree info
        tree_id = task.get("tree_id", task_id)
        tree_tasks = await database.tasks.get_by_tree_id(str(tree_id))
        
        # Get recent messages
        messages = await database.messages.get_by_task_id(str(task_id))
        recent_messages = messages[-5:] if messages else []
        
        # Get runtime status if available
        runtime_active = False
        if runtime_integration and runtime_integration.runtime_engine:
            runtime_active = task_id in runtime_integration.runtime_engine.active_agents
        
        return {
            "task": task,
            "tree_info": {
                "tree_id": tree_id,
                "total_tasks": len(tree_tasks),
                "completed_tasks": len([t for t in tree_tasks if t.get("status") == "completed"]),
                "failed_tasks": len([t for t in tree_tasks if t.get("status") == "failed"]),
                "active_tasks": len([t for t in tree_tasks if t.get("status") in ["running", "queued", "created"]])
            },
            "recent_messages": recent_messages,
            "is_running": runtime_active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/tree/{tree_id}")
async def cancel_task_tree(tree_id: int):
    """Cancel all tasks in a tree"""
    try:
        # Get all tasks in the tree
        tree_tasks = await database.tasks.get_by_tree_id(tree_id)
        
        # Cancel each task
        for task in tree_tasks:
            if task.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]:
                await database.tasks.update_status(task.id, TaskStatus.CANCELLED)
                
                # Also update runtime state if available
                if runtime_integration and runtime_integration.runtime_engine:
                    await runtime_integration.runtime_engine.update_task_state(
                        task.id,
                        TaskState.FAILED,
                        {"reason": "Tree cancelled"}
                    )
        
        await manager.broadcast(f"tree_cancelled:{tree_id}")
        return {"message": f"Task tree {tree_id} cancelled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# User Message Endpoints

@app.get("/user-messages")
async def get_user_messages():
    """Get recent user messages"""
    try:
        messages = await database.user_messages.get_recent_messages(50)
        return {
            "messages": [
                {
                    "id": msg.id,
                    "task_id": msg.task_id,
                    "agent_name": msg.agent_name,
                    "message": msg.message,
                    "message_type": msg.message_type.value,
                    "priority": msg.priority.value,
                    "requires_response": msg.requires_response,
                    "suggested_actions": msg.suggested_actions,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "read_at": msg.read_at.isoformat() if msg.read_at else None,
                    "responded_at": msg.responded_at.isoformat() if msg.responded_at else None,
                    "user_response": msg.user_response
                }
                for msg in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user-messages/unread")
async def get_unread_user_messages():
    """Get unread user messages"""
    try:
        messages = await database.user_messages.get_unread_messages()
        return {
            "messages": [
                {
                    "id": msg.id,
                    "task_id": msg.task_id,
                    "agent_name": msg.agent_name,
                    "message": msg.message,
                    "message_type": msg.message_type.value,
                    "priority": msg.priority.value,
                    "requires_response": msg.requires_response,
                    "suggested_actions": msg.suggested_actions,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user-messages/{message_id}/read")
async def mark_message_read(message_id: int):
    """Mark a user message as read"""
    try:
        success = await database.user_messages.mark_as_read(message_id)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        await manager.broadcast(f"message_read:{message_id}")
        return {"message": "Message marked as read"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/user-messages/{message_id}/respond")
async def respond_to_message(message_id: int, response: dict):
    """Respond to a user message"""
    try:
        user_response = response.get("response", "").strip()
        if not user_response:
            raise HTTPException(status_code=400, detail="Response cannot be empty")
        
        success = await database.user_messages.add_user_response(message_id, user_response)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        await manager.broadcast(f"message_responded:{message_id}")
        return {"message": "Response recorded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Agent Management Endpoints

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    try:
        agents = await database.agents.get_all_active()
        # Parse JSON fields to proper arrays
        for agent in agents:
            if isinstance(agent, dict):
                # Parse JSON string fields to arrays
                if "available_tools" in agent and isinstance(agent["available_tools"], str):
                    try:
                        agent["available_tools"] = json.loads(agent["available_tools"])
                    except:
                        agent["available_tools"] = []
                if "context_documents" in agent and isinstance(agent["context_documents"], str):
                    try:
                        agent["context_documents"] = json.loads(agent["context_documents"])
                    except:
                        agent["context_documents"] = []
                if "permissions" in agent and isinstance(agent["permissions"], str):
                    try:
                        agent["permissions"] = json.loads(agent["permissions"])
                    except:
                        agent["permissions"] = []
                if "constraints" in agent and isinstance(agent["constraints"], str):
                    try:
                        agent["constraints"] = json.loads(agent["constraints"])
                    except:
                        agent["constraints"] = []
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get specific agent configuration"""
    try:
        agent = await database.agents.get_by_name(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Parse JSON fields to proper arrays
        if isinstance(agent, dict):
            if "available_tools" in agent and isinstance(agent["available_tools"], str):
                try:
                    agent["available_tools"] = json.loads(agent["available_tools"])
                except:
                    agent["available_tools"] = []
            if "context_documents" in agent and isinstance(agent["context_documents"], str):
                try:
                    agent["context_documents"] = json.loads(agent["context_documents"])
                except:
                    agent["context_documents"] = []
            if "permissions" in agent and isinstance(agent["permissions"], str):
                try:
                    agent["permissions"] = json.loads(agent["permissions"])
                except:
                    agent["permissions"] = []
            if "constraints" in agent and isinstance(agent["constraints"], str):
                try:
                    agent["constraints"] = json.loads(agent["constraints"])
                except:
                    agent["constraints"] = []
        
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/agents/{agent_name}")
async def update_agent(agent_name: str, agent_update: dict):
    """Update agent configuration"""
    try:
        agent = await database.agents.get_by_name(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update allowed fields
        if "instruction" in agent_update:
            agent.instruction = agent_update["instruction"]
        if "available_tools" in agent_update:
            agent.available_tools = agent_update["available_tools"]
        if "context_documents" in agent_update:
            agent.context_documents = agent_update["context_documents"]
        if "model_config" in agent_update:
            agent.model_config = agent_update["model_config"]
        if "permissions" in agent_update:
            agent.permissions = agent_update["permissions"]
        
        success = await database.agents.update(agent)
        if success:
            return {"message": "Agent updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Context Documents Endpoints

@app.get("/documents")
async def list_documents():
    """List all context documents"""
    try:
        from config.database import db_manager
        query = "SELECT name, title, category, format, LENGTH(content) as size FROM context_documents ORDER BY category, name"
        results = await db_manager.execute_query(query)
        return {"documents": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{doc_name}")
async def get_document(doc_name: str):
    """Get specific document content"""
    try:
        doc = await database.context_documents.get_by_name(doc_name)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/documents/{doc_name}")
async def update_document(doc_name: str, doc_update: dict):
    """Update document content"""
    try:
        if "content" not in doc_update:
            raise HTTPException(status_code=400, detail="Content field is required")
        
        success = await database.context_documents.update_content(
            doc_name, 
            doc_update["content"],
            doc_update.get("updated_by", 0)
        )
        
        if success:
            return {"message": "Document updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Information Endpoints

@app.get("/system/state")
async def get_system_state():
    """Get current system initialization state"""
    try:
        # Check if we have a properly initialized system
        agents = await database.agents.get_all_active()
        
        # System is initialized if we have more than just the bootstrap agents
        # init_schema.sql creates 8 agents, so we need at least 8
        if len(agents) >= 8:
            # Check if agents have proper instructions (not just placeholders)
            agent_names = [a.get('name') for a in agents]
            required_agents = ['agent_selector', 'task_breakdown', 'context_addition', 
                             'tool_addition', 'task_evaluator', 'documentation_agent',
                             'summary_agent', 'review_agent']
            
            if all(name in agent_names for name in required_agents):
                return {"state": "ready"}
        
        return {"state": "uninitialized"}
    except Exception as e:
        logger.error(f"Error checking system state: {e}")
        return {"state": "uninitialized"}


@app.post("/system/initialize")
async def initialize_system(settings: dict = None):
    """Initialize the system with initialization tasks"""
    try:
        if not runtime_integration:
            raise RuntimeError("Runtime integration not initialized")
        
        # Submit the system initialization task
        from core.initialization_tasks import get_initialization_tasks
        
        # Create the main initialization task
        task_params = {
            "instruction": "Execute system initialization process with comprehensive framework establishment",
            "metadata": {
                "type": "system_initialization",
                "settings": settings or {},
                "initialization_tasks": [task.to_dict() for task in get_initialization_tasks()]
            }
        }
        
        task = await runtime_integration.runtime_engine.create_task(**task_params)
        
        # The initialization process will handle creating all subtasks
        return {
            "status": "initializing",
            "task_id": task.id,
            "message": "System initialization started"
        }
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/stats")
async def get_system_stats():
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
        runtime_integration_local = get_runtime_integration()
        if runtime_integration_local:
            runtime_stats = await runtime_integration_local.get_runtime_statistics()
        
        # Calculate task stats from runtime
        task_stats = {
            "running_agents": len(runtime_integration_local.runtime_engine.active_agents) if runtime_integration_local and runtime_integration_local.runtime_engine else 0,
            "queued_tasks": len([t for t in active_tasks if t.status == TaskStatus.QUEUED]),
            "max_concurrent_agents": runtime_integration_local.runtime_engine.settings.max_concurrent_agents if runtime_integration_local and runtime_integration_local.runtime_engine else 5,
            "is_running": runtime_integration_local is not None and runtime_integration_local.runtime_engine is not None
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


@app.get("/system/tools")
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


# Admin Endpoints

@app.post("/admin/shutdown")
async def graceful_shutdown():
    """Initiate graceful system shutdown"""
    try:
        await manager.broadcast("system_shutdown")
        # In a real implementation, this would trigger shutdown
        return {"message": "Graceful shutdown initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Models

class SystemConfig(BaseModel):
    max_parallel_tasks: int = 3
    step_mode: bool = False
    step_mode_threads: list[int] = []  # Specific threads in step mode
    manual_step_mode: bool = False  # Manual approval for each agent
    max_concurrent_agents: int = 3

class StepCommand(BaseModel):
    task_id: int
    action: str = "continue"  # continue, skip, abort


# Configuration Endpoints

@app.get("/system/state")
async def get_system_state():
    """Get current system initialization state"""
    # Check if system has been initialized
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
        elif hasattr(app.state, "initializing") and app.state.initializing:
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


@app.post("/system/initialize")
async def initialize_system(settings: dict):
    """Start system initialization with provided settings"""
    try:
        # Mark system as initializing
        app.state.initializing = True
        
        # Broadcast state change
        await manager.broadcast(json.dumps({
            "type": "system_state_change",
            "state": "initializing"
        }))
        
        # Update system config with initialization settings
        if runtime_integration and runtime_integration.runtime_engine:
            runtime_integration.runtime_engine.settings.manual_stepping_enabled = settings.get("manualStepMode", True)
            runtime_integration.runtime_engine.settings.max_concurrent_agents = settings.get("maxConcurrentAgents", 1)
        
        # Create initialization task with proper process
        initialization_task_id = await runtime_integration.create_task(
            instruction="Execute system initialization sequence including knowledge bootstrap and framework establishment",
            parent_task_id=None,
            process="system_initialization_process",
            metadata={
                "task_type": "system_initialization",
                "phase": "complete", 
                "manual_mode": settings.get("manualStepMode", True),
                "initialization_task": True,
                "assigned_agent": "agent_selector",
                "priority": 1
            }
        )
        
        logger.info(f"Started system initialization with task {initialization_task_id}")
        
        # The actual initialization will be handled by tasks
        # Monitor completion via task status
        asyncio.create_task(monitor_initialization_completion(initialization_task_id))
        
        return {
            "message": "System initialization started",
            "task_id": initialization_task_id,
            "settings": settings
        }
    except Exception as e:
        app.state.initializing = False
        logger.error(f"Error starting initialization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def monitor_initialization_completion(task_id: int):
    """Monitor initialization task and update system state when complete"""
    try:
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            task = await database.tasks.get_by_id(task_id)
            if task and task.status in ["completed", "failed"]:
                app.state.initializing = False
                
                new_state = "ready" if task.status == "completed" else "uninitialized"
                
                # Broadcast state change
                await manager.broadcast(json.dumps({
                    "type": "system_state_change",
                    "state": new_state
                }))
                
                logger.info(f"System initialization {task.status}. New state: {new_state}")
                break
                
    except Exception as e:
        logger.error(f"Error monitoring initialization: {e}")
        app.state.initializing = False


@app.get("/system/config")
async def get_system_config():
    """Get current system configuration"""
    max_concurrent = 5
    step_mode = False
    step_mode_threads = []
    manual_step_mode = False
    
    if runtime_integration and runtime_integration.runtime_engine:
        max_concurrent = runtime_integration.runtime_engine.settings.max_concurrent_agents
        step_mode = runtime_integration.runtime_engine.settings.manual_stepping_enabled
        step_mode_threads = getattr(runtime_integration.runtime_engine.settings, "step_mode_threads", [])
        manual_step_mode = step_mode  # For now, same as step_mode
    
    return {
        "max_parallel_tasks": max_concurrent,
        "step_mode": step_mode,
        "step_mode_threads": step_mode_threads,
        "manual_step_mode": manual_step_mode,
        "max_concurrent_agents": max_concurrent
    }


@app.put("/system/config")
async def update_system_config(config: SystemConfig):
    """Update system configuration"""
    try:
        if runtime_integration and runtime_integration.runtime_engine:
            runtime_integration.runtime_engine.settings.max_concurrent_agents = config.max_parallel_tasks
            runtime_integration.runtime_engine.settings.manual_stepping_enabled = config.step_mode
            setattr(runtime_integration.runtime_engine.settings, "step_mode_threads", config.step_mode_threads)
        
        # Broadcast configuration change
        await manager.broadcast(json.dumps({
            "type": "config_updated",
            "config": config.model_dump()
        }))
        
        return {"message": "Configuration updated", "config": config.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/system/step")
async def handle_step_command(command: StepCommand):
    """Handle step mode commands"""
    try:
        if not runtime_integration or not runtime_integration.runtime_engine:
            raise RuntimeError("Runtime engine not available")
        
        if command.action == "continue":
            # Continue task execution (release from manual hold)
            await runtime_integration.runtime_engine.update_task_state(
                command.task_id,
                TaskState.READY_FOR_AGENT
            )
        elif command.action == "skip":
            # Skip task (mark as completed)
            await runtime_integration.runtime_engine.update_task_state(
                command.task_id,
                TaskState.COMPLETED,
                {"skipped": True}
            )
        elif command.action == "abort":
            # Abort task (mark as failed)
            await runtime_integration.runtime_engine.update_task_state(
                command.task_id,
                TaskState.FAILED,
                {"aborted": True}
            )
        else:
            raise ValueError(f"Unknown step action: {command.action}")
        
        return {"message": f"Step command '{command.action}' executed for task {command.task_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/restart")
async def restart_system():
    """Restart the system (for self-modifications)"""
    try:
        await manager.broadcast("system_restart")
        # In a real implementation, this would trigger restart
        return {"message": "System restart initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Handle client commands
            try:
                command = json.loads(data)
                if command.get("type") == "continue_step":
                    task_id = command.get("task_id")
                    if task_id and runtime_integration and runtime_integration.runtime_engine:
                        await runtime_integration.runtime_engine.update_task_state(
                            task_id,
                            TaskState.READY_FOR_AGENT
                        )
                        await manager.send_personal_message(
                            json.dumps({"type": "step_continued", "task_id": task_id}),
                            websocket
                        )
            except json.JSONDecodeError:
                # Echo back for backward compatibility
                await manager.send_personal_message(f"Echo: {data}", websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Static files for web interface (production-ready)
from pathlib import Path
import os

# Check if web build exists
web_build_path = Path(__file__).parent.parent / "web" / "build"
web_static_path = web_build_path / "static"
web_index_path = web_build_path / "index.html"

if web_build_path.exists() and web_index_path.exists():
    # Production build available
    app.mount("/static", StaticFiles(directory=str(web_static_path)), name="static")
    
    @app.get("/app", response_class=HTMLResponse)
    async def serve_app():
        """Serve the React app"""
        try:
            with open(web_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        except Exception as e:
            return HTMLResponse(
                content=f"<h1>Error loading web interface</h1><p>{str(e)}</p>",
                status_code=500
            )
    
    # Serve React app for any unmatched routes (SPA routing)
    @app.get("/app/{path:path}", response_class=HTMLResponse)
    async def serve_app_routes(path: str):
        """Serve React app for client-side routing"""
        return await serve_app()
        
    print(f"✅ Web interface available at /app")
        
else:
    # Web interface not built yet - provide helpful placeholder
    @app.get("/app", response_class=HTMLResponse)
    async def serve_placeholder():
        """Enhanced placeholder for web interface"""
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Self-Improving Agent System - Process-First Architecture</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; line-height: 1.6; }
                    .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .status { background: #e8f5e8; padding: 15px; border-radius: 6px; margin: 10px 0; }
                    .warning { background: #fff3e0; padding: 15px; border-radius: 6px; margin: 10px 0; }
                    .links { background: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
                    .links a { display: inline-block; margin: 5px 10px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                    .links a:hover { background: #0056b3; }
                    .api-test { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px; }
                    textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }
                    button { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                    button:hover { background: #218838; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🤖 Self-Improving Agent System</h1>
                    <p><strong>Process-First Foundation</strong> - 9 Specialized Agents with Framework Establishment</p>
                </div>
                
                <div class="warning">
                    <h3>⚠️ Web Interface Not Built</h3>
                    <p>To build the production web interface, run:</p>
                    <code>cd web && npm install && npm run build</code>
                </div>
                
                <div class="status">
                    <h3>✅ API Server Running</h3>
                    <p>Process-first foundation with systematic framework establishment, 9 agents, and isolated task success is operational.</p>
                </div>
                
                <div class="links">
                    <h3>Available Endpoints</h3>
                    <a href="/docs" target="_blank">📚 API Documentation</a>
                    <a href="/health" target="_blank">🏥 System Health</a>
                    <a href="/agents" target="_blank">🤖 List Agents</a>
                    <a href="/tasks/active" target="_blank">📋 Active Tasks</a>
                    <a href="/system/stats" target="_blank">📊 System Stats</a>
                </div>
                
                <div class="api-test">
                    <h3>🚀 Quick API Test</h3>
                    <p>Test the system by submitting an advanced task:</p>
                    <form action="/tasks" method="post" style="margin-top: 10px;">
                        <textarea name="instruction" placeholder="Enter an advanced task for the complete foundation:

Examples:
- Build a comprehensive performance monitoring dashboard with real-time analytics
- Build comprehensive process framework library for common domains
- Create framework validation suite for process completeness verification  
- Implement isolation testing to verify independent subtask success" rows="8"></textarea><br><br>
                        <button type="submit">Submit Task for Framework Analysis</button>
                    </form>
                    <p style="margin-top: 15px;"><small><strong>Note:</strong> All tasks undergo process discovery and framework establishment before execution.</small></p>
                </div>
                
                <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 14px;">
                    <p>Process-First Foundation v2.0 | 9 Agents | Framework-Driven Execution | Isolated Task Success!</p>
                </footer>
            </body>
        </html>
        """)
    
    print(f"⚠️  Web interface not built - placeholder available at /app")


if __name__ == "__main__":
    # Check if we have API keys configured
    if not settings.anthropic_api_key and not settings.openai_api_key:
        print("⚠️  Warning: No AI API keys configured!")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables")
        print("   Or create a .env file with your API keys")
    
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting server on http://{host}:{port}")
    print(f"API docs available at http://{host}:{port}/docs")
    print(f"Web interface at http://{host}:{port}/app")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug_mode,
        log_level="info"
    )