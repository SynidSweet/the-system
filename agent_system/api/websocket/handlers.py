"""WebSocket connection management and real-time communication."""

import json
import logging
from typing import List

from fastapi import WebSocket, WebSocketDisconnect

from ...core.websocket_messages import WebSocketMessage
from ...core.runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to connected clients."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_message(self, ws_message: WebSocketMessage):
        """Broadcast a structured WebSocket message."""
        await self.broadcast(ws_message.to_json())
    
    async def broadcast_user_message(self, message_data: dict):
        """Broadcast user message to all connected clients."""
        message_json = json.dumps(message_data)
        await self.broadcast(message_json)


# Global connection manager instance
manager = ConnectionManager()


def get_websocket_manager() -> ConnectionManager:
    """Get the global WebSocket connection manager."""
    return manager


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates and client commands."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Handle client commands
            try:
                command = json.loads(data)
                await handle_websocket_command(command, websocket)
            except json.JSONDecodeError:
                # Echo back for backward compatibility
                await manager.send_personal_message(f"Echo: {data}", websocket)
            except Exception as e:
                logger.error(f"Error handling WebSocket command: {e}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": str(e)}),
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        manager.disconnect(websocket)


async def handle_websocket_command(command: dict, websocket: WebSocket):
    """Handle incoming WebSocket commands from clients."""
    command_type = command.get("type")
    
    if command_type == "continue_step":
        await handle_continue_step_command(command, websocket)
    elif command_type == "ping":
        await manager.send_personal_message(
            json.dumps({"type": "pong", "timestamp": command.get("timestamp")}),
            websocket
        )
    else:
        logger.warning(f"Unknown WebSocket command type: {command_type}")
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"Unknown command type: {command_type}"}),
            websocket
        )


async def handle_continue_step_command(command: dict, websocket: WebSocket):
    """Handle step continuation commands from clients."""
    task_id = command.get("task_id")
    if not task_id:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "task_id is required for continue_step command"}),
            websocket
        )
        return
    
    try:
        # Get runtime integration
        from ..main import runtime_integration
        
        if runtime_integration and runtime_integration.runtime_engine:
            await runtime_integration.runtime_engine.update_task_state(
                task_id,
                TaskState.READY_FOR_AGENT
            )
            await manager.send_personal_message(
                json.dumps({"type": "step_continued", "task_id": task_id}),
                websocket
            )
            logger.info(f"Step continued for task {task_id}")
        else:
            await manager.send_personal_message(
                json.dumps({"type": "error", "message": "Runtime integration not available"}),
                websocket
            )
    except Exception as e:
        logger.error(f"Error continuing step for task {task_id}: {e}")
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"Failed to continue step: {str(e)}"}),
            websocket
        )