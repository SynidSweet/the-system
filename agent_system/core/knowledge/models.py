"""
Data Models for Context Assembly Engine

Core data structures used throughout the knowledge system.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContextPackage:
    """Complete context package for a task."""
    task_id: int
    agent_type: str
    domain: str
    context_documents: List[str]
    context_text: str
    completeness_score: float
    missing_requirements: List[str]
    knowledge_sources: List[str]
    assembled_at: str = ""
    
    def __post_init__(self):
        if not self.assembled_at:
            self.assembled_at = datetime.now().isoformat()


@dataclass
class ValidationResult:
    """Result of context validation."""
    is_complete: bool
    completeness_score: float
    missing_requirements: List[str]
    isolation_capable: bool
    recommendations: List[str]


@dataclass
class KnowledgeGap:
    """Identified knowledge gap."""
    gap_type: str
    description: str
    priority: str
    context: Dict[str, Any]