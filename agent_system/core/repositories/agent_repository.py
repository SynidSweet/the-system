"""Agent-specific repository implementation."""

from typing import Dict, List, Optional, Any
import json

from .agent import AgentEntity
from ..events.event_types import EntityType
from ..events.event_manager import EventManager
from .base_repository import BaseRepository


class AgentRepository(BaseRepository[AgentEntity]):
    """Repository for agent entities with specialized agent operations."""
    
    def __init__(self, db_path: str, event_manager: Optional[EventManager] = None):
        super().__init__(
            db_path=db_path,
            entity_type=EntityType.AGENT,
            entity_class=AgentEntity,
            event_manager=event_manager
        )
    
    async def find_by_capability(self, tool_name: str) -> List[AgentEntity]:
        """Find agents that have access to a specific tool."""
        agents = await self.list(limit=1000)
        
        results = []
        for agent in agents:
            if tool_name in agent.available_tools:
                results.append(agent)
        
        return results
    
    async def find_by_context_document(self, document_name: str) -> List[AgentEntity]:
        """Find agents that use a specific context document."""
        agents = await self.list(limit=1000)
        
        results = []
        for agent in agents:
            if document_name in agent.context_documents:
                results.append(agent)
        
        return results
    
    async def get_agents_by_specialization(self, specialization_type: str) -> List[AgentEntity]:
        """Get agents by their specialization metadata."""
        agents = await self.list(limit=1000)
        
        results = []
        for agent in agents:
            specialization = agent.metadata.get('specialization')
            if specialization == specialization_type:
                results.append(agent)
        
        return results
    
    async def update_tools(self, agent_id: int, tools: List[str]) -> Optional[AgentEntity]:
        """Update an agent's available tools."""
        return await self.update(agent_id, {'available_tools': tools})
    
    async def add_context_document(self, agent_id: int, document_name: str) -> Optional[AgentEntity]:
        """Add a context document to an agent."""
        agent = await self.get(agent_id)
        if not agent:
            return None
        
        if document_name not in agent.context_documents:
            updated_docs = agent.context_documents + [document_name]
            return await self.update(agent_id, {'context_documents': updated_docs})
        
        return agent
    
    async def remove_context_document(self, agent_id: int, document_name: str) -> Optional[AgentEntity]:
        """Remove a context document from an agent."""
        agent = await self.get(agent_id)
        if not agent:
            return None
        
        if document_name in agent.context_documents:
            updated_docs = [doc for doc in agent.context_documents if doc != document_name]
            return await self.update(agent_id, {'context_documents': updated_docs})
        
        return agent
    
    # Implementation of abstract methods
    async def _insert_type_specific(self, db, entity_id: int, entity_data: Dict[str, Any]):
        """Insert agent-specific record."""
        await db.execute("""
            INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            entity_data.get('name', 'unnamed'),
            entity_data.get('instruction', ''),
            json.dumps(entity_data.get('context_documents', [])),
            json.dumps(entity_data.get('available_tools', [])),
            json.dumps(entity_data.get('permissions', [])),
            json.dumps(entity_data.get('constraints', []))
        ))
    
    async def _get_type_specific(self, db, entity_id: int) -> Optional[Dict[str, Any]]:
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
    
    async def _update_type_specific(self, db, entity_id: int, updates: Dict[str, Any]):
        """Update agent-specific fields."""
        # Get current agent data to merge with updates
        current_data = await self._get_type_specific(db, entity_id)
        if not current_data:
            return
        
        # Merge updates with current data
        final_data = {**current_data, **updates}
        
        await db.execute("""
            UPDATE agents SET
                instruction = ?,
                context_documents = ?,
                available_tools = ?,
                permissions = ?,
                constraints = ?
            WHERE id = ?
        """, (
            final_data.get('instruction', ''),
            json.dumps(final_data.get('context_documents', [])),
            json.dumps(final_data.get('available_tools', [])),
            json.dumps(final_data.get('permissions', [])),
            json.dumps(final_data.get('constraints', [])),
            entity_id
        ))
    
    async def _delete_type_specific(self, db, entity_id: int):
        """Delete agent-specific record."""
        await db.execute("DELETE FROM agents WHERE id = ?", (entity_id,))