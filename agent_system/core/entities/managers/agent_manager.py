"""Agent-specific entity manager."""

from typing import Dict, List, Optional, Any
import json
import aiosqlite

from ..base import Entity
from ..agent import AgentEntity
from ...events.event_types import EntityType
from ...events.event_manager import EventManager
from .base_manager import BaseManager


class AgentManager(BaseManager):
    """Manager for agent entities with specialized agent operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.AGENT,
            entity_class=AgentEntity,
            event_manager=event_manager
        )
    
    async def search(
        self,
        search_term: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Search agents by instruction, name, or available tools."""
        if not fields:
            fields = ['name', 'instruction']
        
        return await super().search(search_term, fields, limit)
    
    async def find_by_capability(self, tool_name: str) -> List[AgentEntity]:
        """Find agents that have access to a specific tool."""
        agents = await self.list(limit=1000)
        
        results = []
        for agent in agents:
            if isinstance(agent, AgentEntity) and tool_name in agent.available_tools:
                results.append(agent)
        
        return results
    
    async def find_by_context_document(self, document_name: str) -> List[AgentEntity]:
        """Find agents that use a specific context document."""
        agents = await self.list(limit=1000)
        
        results = []
        for agent in agents:
            if isinstance(agent, AgentEntity) and document_name in agent.context_documents:
                results.append(agent)
        
        return results
    
    async def get_agents_by_specialization(self, specialization_type: str) -> List[AgentEntity]:
        """Get agents by their specialization metadata."""
        agents = await self.list(limit=1000)
        
        results = []
        for agent in agents:
            if isinstance(agent, AgentEntity):
                specialization = agent.metadata.get('specialization')
                if specialization == specialization_type:
                    results.append(agent)
        
        return results
    
    async def update_tools(self, agent_id: int, tools: List[str]) -> bool:
        """Update an agent's available tools."""
        agent = await self.get(agent_id)
        if not agent or not isinstance(agent, AgentEntity):
            return False
        
        return await self.update(agent, available_tools=tools)
    
    async def add_context_document(self, agent_id: int, document_name: str) -> bool:
        """Add a context document to an agent."""
        agent = await self.get(agent_id)
        if not agent or not isinstance(agent, AgentEntity):
            return False
        
        if document_name not in agent.context_documents:
            updated_docs = agent.context_documents + [document_name]
            return await self.update(agent, context_documents=updated_docs)
        
        return True
    
    async def remove_context_document(self, agent_id: int, document_name: str) -> bool:
        """Remove a context document from an agent."""
        agent = await self.get(agent_id)
        if not agent or not isinstance(agent, AgentEntity):
            return False
        
        if document_name in agent.context_documents:
            updated_docs = [doc for doc in agent.context_documents if doc != document_name]
            return await self.update(agent, context_documents=updated_docs)
        
        return True
    
    async def _create_type_specific_record(self, db, entity_id: int, name: str, **kwargs):
        """Create agent-specific record."""
        await db.execute("""
            INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            name,
            kwargs['instruction'],
            json.dumps(kwargs.get('context_documents', [])),
            json.dumps(kwargs.get('available_tools', [])),
            json.dumps(kwargs.get('permissions', [])),
            json.dumps(kwargs.get('constraints', []))
        ))
    
    async def _get_type_specific_data(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get agent-specific data."""
        cursor = await db.execute(
            "SELECT * FROM agents WHERE id = ?",
            (entity_id,)
        )
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON fields
            for field in ['context_documents', 'available_tools', 'permissions', 'constraints']:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except:
                        data[field] = []
            return data
        return None
    
    async def _update_type_specific_record(self, db, entity: Entity, **updates):
        """Update agent-specific fields."""
        if not isinstance(entity, AgentEntity):
            return
        
        if any(field in updates for field in ['instruction', 'context_documents', 
                                              'available_tools', 'permissions', 'constraints']):
            await db.execute("""
                UPDATE agents SET
                    instruction = ?,
                    context_documents = ?,
                    available_tools = ?,
                    permissions = ?,
                    constraints = ?
                WHERE id = ?
            """, (
                updates.get('instruction', entity.instruction),
                json.dumps(updates.get('context_documents', entity.context_documents)),
                json.dumps(updates.get('available_tools', entity.available_tools)),
                json.dumps(updates.get('permissions', entity.permissions)),
                json.dumps(updates.get('constraints', entity.constraints)),
                entity.entity_id
            ))
    
    async def _delete_type_specific_record(self, db, entity_id: int):
        """Delete agent-specific record."""
        await db.execute("DELETE FROM agents WHERE id = ?", (entity_id,))