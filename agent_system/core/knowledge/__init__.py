"""
Knowledge System for MVP Implementation

Provides file-based knowledge storage and context assembly for the agent system.
"""

from .entity import (
    KnowledgeEntity,
    KnowledgeContent,
    KnowledgeRelationships,
    ContextTemplates,
    IsolationRequirements,
    KnowledgeMetadata
)
from .storage import KnowledgeStorage
from .models import ContextPackage, ValidationResult, KnowledgeGap
from .engine import ContextAssemblyEngine

__all__ = [
    'KnowledgeEntity',
    'KnowledgeContent',
    'KnowledgeRelationships',
    'ContextTemplates',
    'IsolationRequirements',
    'KnowledgeMetadata',
    'KnowledgeStorage',
    'ContextAssemblyEngine',
    'ContextPackage',
    'ValidationResult',
    'KnowledgeGap'
]