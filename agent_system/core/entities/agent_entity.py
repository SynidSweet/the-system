"""Agent entity implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import Entity, EntityState
from ..events.event_types import EntityType


class AgentEntity(Entity):
    """Entity representation of an agent."""
    
    def __init__(
        self,
        entity_id: int,
        name: str,
        instruction: str,
        context_documents: Optional[List[str]] = None,
        available_tools: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        version: str = "1.0.0",
        state: EntityState = EntityState.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            entity_type=EntityType.AGENT,
            version=version,
            state=state,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
        
        self.instruction = instruction
        self.context_documents = context_documents or []
        self.available_tools = available_tools or []
        self.permissions = permissions or []
        self.constraints = constraints or []
        
        # Agent-specific relationships
        self.specializations: List[int] = []  # Other agents this one specializes
        self.dependencies: List[int] = []     # Other agents this one depends on
    
    async def validate(self) -> bool:
        """Validate agent configuration."""
        # Basic validation
        if not self.name or not self.instruction:
            return False
        
        # Ensure instruction is meaningful
        if len(self.instruction) < 10:
            return False
        
        # Validate tools exist (would check against tool registry in real implementation)
        # For now, just ensure they're non-empty strings
        for tool in self.available_tools:
            if not tool or not isinstance(tool, str):
                return False
        
        return True
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert agent entity to dictionary."""
        base_dict = await super().to_dict()
        base_dict.update({
            "instruction": self.instruction,
            "context_documents": self.context_documents,
            "available_tools": self.available_tools,
            "permissions": self.permissions,
            "constraints": self.constraints,
            "specializations": self.specializations,
            "dependencies": self.dependencies
        })
        return base_dict
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'AgentEntity':
        """Create agent entity from dictionary."""
        entity = cls(
            entity_id=data["entity_id"],
            name=data["name"],
            instruction=data["instruction"],
            context_documents=data.get("context_documents", []),
            available_tools=data.get("available_tools", []),
            permissions=data.get("permissions", []),
            constraints=data.get("constraints", []),
            version=data.get("version", "1.0.0"),
            state=EntityState(data.get("state", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Restore relationships
        entity.relationships = data.get("relationships", {})
        entity.specializations = data.get("specializations", [])
        entity.dependencies = data.get("dependencies", [])
        
        return entity
    
    async def add_tool(self, tool_name: str) -> bool:
        """Add a tool to the agent's available tools."""
        if tool_name not in self.available_tools:
            self.available_tools.append(tool_name)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.AGENT,
                    self.entity_id,
                    update_type="tool_added",
                    tool_name=tool_name
                )
            
            return True
        return False
    
    async def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the agent's available tools."""
        if tool_name in self.available_tools:
            self.available_tools.remove(tool_name)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.AGENT,
                    self.entity_id,
                    update_type="tool_removed",
                    tool_name=tool_name
                )
            
            return True
        return False
    
    async def add_context(self, context_doc: str) -> bool:
        """Add a context document to the agent."""
        if context_doc not in self.context_documents:
            self.context_documents.append(context_doc)
            self.updated_at = datetime.now()
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EntityType.ENTITY_UPDATED,
                    EntityType.AGENT,
                    self.entity_id,
                    update_type="context_added",
                    context_doc=context_doc
                )
            
            return True
        return False
    
    async def update_instruction(self, new_instruction: str) -> bool:
        """Update the agent's instruction."""
        old_instruction = self.instruction
        self.instruction = new_instruction
        self.updated_at = datetime.now()
        
        if self.event_manager:
            await self.event_manager.log_event(
                EntityType.ENTITY_UPDATED,
                EntityType.AGENT,
                self.entity_id,
                update_type="instruction_updated",
                old_instruction=old_instruction,
                new_instruction=new_instruction
            )
        
        return True