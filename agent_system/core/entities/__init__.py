"""Entity management module for the entity-based architecture."""

from agent_system.core.entities.base import Entity, EntityState
from .agent import AgentEntity
from .task import TaskEntity, TaskState
from .tool import ToolEntity, ToolCategory
from .context import ContextEntity, ContextCategory, ContextFormat
from .process import ProcessEntity, ProcessType
from .event import EventEntity
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