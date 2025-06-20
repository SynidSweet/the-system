"""Entity management module for the entity-based architecture."""

from agent_system.core.entities.base import Entity, EntityState
from agent_system.core.entities.agent_entity import AgentEntity
from agent_system.core.entities.task_entity import TaskEntity, TaskState
from agent_system.core.entities.tool_entity import ToolEntity, ToolCategory
from agent_system.core.entities.context_entity import ContextEntity, ContextCategory, ContextFormat
from agent_system.core.entities.process_entity import ProcessEntity, ProcessType
from agent_system.core.entities.event_entity import EventEntity
from agent_system.core.entities.entity_manager import EntityManager

__all__ = [
    # Base classes
    'Entity',
    'EntityState',
    
    # Entity types
    'AgentEntity',
    'TaskEntity',
    'ToolEntity',
    'ContextEntity',
    'ProcessEntity',
    'EventEntity',
    
    # Enums
    'TaskState',
    'ToolCategory',
    'ContextCategory',
    'ContextFormat',
    'ProcessType',
    
    # Manager
    'EntityManager',
]