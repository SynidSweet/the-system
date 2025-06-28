"""Entity CRUD endpoints for agents, documents, and user messages."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from config.database import DatabaseManager
from ..exceptions import EntityNotFoundError, ValidationError


# Request models
class AgentUpdate(BaseModel):
    instruction: str = None
    available_tools: List[str] = None
    context_documents: List[str] = None
    model_configuration: Dict[str, Any] = None
    permissions: Dict[str, Any] = None


class DocumentUpdate(BaseModel):
    content: str
    updated_by: int = 0


class UserMessageResponse(BaseModel):
    response: str


# Dependencies
def get_database():
    """Get database instance"""
    from ..main import database
    return database


def get_websocket_manager():
    """Get WebSocket connection manager"""
    from ..websocket.handlers import manager
    return manager


# Create router
router = APIRouter()


# Agent Endpoints
@router.get("/agents")
async def list_agents(database: DatabaseManager = Depends(get_database)):
    """List all available agents"""
    try:
        agents = await database.agents.get_all_active()
        return {"agents": [agent.model_dump() for agent in agents]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}")
async def get_agent(agent_name: str, database: DatabaseManager = Depends(get_database)):
    """Get specific agent configuration"""
    try:
        agent = await database.agents.get_by_name(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}")
async def update_agent(
    agent_name: str, 
    agent_update: AgentUpdate,
    database: DatabaseManager = Depends(get_database)
):
    """Update agent configuration"""
    try:
        agent = await database.agents.get_by_name(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update allowed fields
        if agent_update.instruction is not None:
            agent.instruction = agent_update.instruction
        if agent_update.available_tools is not None:
            agent.available_tools = agent_update.available_tools
        if agent_update.context_documents is not None:
            agent.context_documents = agent_update.context_documents
        if agent_update.model_config is not None:
            agent.model_config = agent_update.model_config
        if agent_update.permissions is not None:
            agent.permissions = agent_update.permissions
        
        success = await database.agents.update(agent)
        if success:
            return {"message": "Agent updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Document Endpoints
@router.get("/documents")
async def list_documents(database: DatabaseManager = Depends(get_database)):
    """List all context documents"""
    try:
        from config.database import db_manager
        query = "SELECT name, title, category, format, LENGTH(content) as size, created_at, updated_at FROM context_documents ORDER BY category, name"
        results = await db_manager.execute_query(query)
        return {"documents": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_name}")
async def get_document(doc_name: str, database: DatabaseManager = Depends(get_database)):
    """Get specific document content"""
    try:
        doc = await database.context_documents.get_by_name(doc_name)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/documents/{doc_name}")
async def update_document(
    doc_name: str, 
    doc_update: DocumentUpdate,
    database: DatabaseManager = Depends(get_database)
):
    """Update document content"""
    try:
        if not doc_update.content:
            raise HTTPException(status_code=400, detail="Content field is required")
        
        success = await database.context_documents.update_content(
            doc_name, 
            doc_update.content,
            doc_update.updated_by
        )
        
        if success:
            return {"message": "Document updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# User Message Endpoints
@router.get("/user-messages")
async def get_user_messages(database: DatabaseManager = Depends(get_database)):
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


@router.get("/user-messages/unread")
async def get_unread_user_messages(database: DatabaseManager = Depends(get_database)):
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


@router.post("/user-messages/{message_id}/read")
async def mark_message_read(
    message_id: int,
    database: DatabaseManager = Depends(get_database),
    ws_manager = Depends(get_websocket_manager)
):
    """Mark a user message as read"""
    try:
        success = await database.user_messages.mark_as_read(message_id)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        await ws_manager.broadcast(f"message_read:{message_id}")
        return {"message": "Message marked as read"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/user-messages/{message_id}/respond")
async def respond_to_message(
    message_id: int, 
    response: UserMessageResponse,
    database: DatabaseManager = Depends(get_database),
    ws_manager = Depends(get_websocket_manager)
):
    """Respond to a user message"""
    try:
        user_response = response.response.strip()
        if not user_response:
            raise HTTPException(status_code=400, detail="Response cannot be empty")
        
        success = await database.user_messages.add_user_response(message_id, user_response)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        await ws_manager.broadcast(f"message_responded:{message_id}")
        return {"message": "Response recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))