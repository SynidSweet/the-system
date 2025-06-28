"""Entity management module for the entity-based architecture."""

from .base import Entity, EntityState
from .agent_entity import AgentEntity
from .task_entity import TaskEntity, TaskState
from .tool_entity import ToolEntity, ToolCategory
from .context_entity import ContextEntity, ContextCategory, ContextFormat
from .process_entity import ProcessEntity, ProcessType
from .event_entity import EventEntity
from .entity_manager import EntityManager

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