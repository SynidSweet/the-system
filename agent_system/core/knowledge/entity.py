"""
Knowledge Entity Classes for MVP System

Defines the structure for knowledge entities with JSON serialization support.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path


@dataclass
class KnowledgeContent:
    """Content structure for knowledge entities."""
    summary: str
    core_concepts: List[str]
    procedures: List[str]
    examples: List[str]
    quality_criteria: List[str]
    common_pitfalls: List[str]


@dataclass
class KnowledgeRelationships:
    """Relationship structure for knowledge entities."""
    enables: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    enhances: List[str] = field(default_factory=list)
    specializes: List[str] = field(default_factory=list)
    generalizes: List[str] = field(default_factory=list)


@dataclass
class ContextTemplates:
    """Context template structure for knowledge entities."""
    task_context: str
    agent_context: str
    process_context: Optional[str] = None
    validation_context: Optional[str] = None
    learning_context: Optional[str] = None


@dataclass
class IsolationRequirements:
    """Isolation requirement structure for knowledge entities."""
    minimum_context: List[str]
    validation_criteria: List[str]


@dataclass
class KnowledgeMetadata:
    """Metadata structure for knowledge entities."""
    created_at: str
    last_updated: str
    usage_count: int = 0
    effectiveness_score: float = 0.0
    source: str = "manual_creation"
    tags: List[str] = field(default_factory=list)
    priority: str = "medium"
    # Optional metadata fields
    complexity_level: Optional[str] = None
    automation_potential: Optional[str] = None
    specialization_level: Optional[str] = None
    confidence_level: Optional[str] = None
    applicability_scope: Optional[str] = None
    change_frequency: Optional[str] = None


class KnowledgeEntity:
    """Knowledge entity with full structure and JSON serialization support."""
    
    def __init__(
        self,
        id: str,
        type: str,
        name: str,
        version: str,
        domain: str,
        process_frameworks: List[str],
        content: KnowledgeContent,
        relationships: KnowledgeRelationships,
        context_templates: ContextTemplates,
        isolation_requirements: IsolationRequirements,
        metadata: KnowledgeMetadata
    ):
        # Validate type
        valid_types = ["domain", "process", "agent", "tool", "pattern", "system"]
        if type not in valid_types:
            raise ValueError(f"Invalid type '{type}'. Must be one of: {valid_types}")
        
        self.id = id
        self.type = type
        self.name = name
        self.version = version
        self.domain = domain
        self.process_frameworks = process_frameworks
        self.content = content
        self.relationships = relationships
        self.context_templates = context_templates
        self.isolation_requirements = isolation_requirements
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "process_frameworks": self.process_frameworks,
            "content": asdict(self.content),
            "relationships": asdict(self.relationships),
            "context_templates": asdict(self.context_templates),
            "isolation_requirements": asdict(self.isolation_requirements),
            "metadata": asdict(self.metadata)
        }
        
        # Remove None values from optional metadata fields
        metadata = result["metadata"]
        for key in list(metadata.keys()):
            if metadata[key] is None:
                del metadata[key]
        
        # Remove None values from optional context templates
        templates = result["context_templates"]
        for key in list(templates.keys()):
            if templates[key] is None:
                del templates[key]
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntity':
        """Create from dictionary loaded from JSON."""
        return cls(
            id=data["id"],
            type=data["type"],
            name=data["name"],
            version=data["version"],
            domain=data["domain"],
            process_frameworks=data["process_frameworks"],
            content=KnowledgeContent(**data["content"]),
            relationships=KnowledgeRelationships(**data["relationships"]),
            context_templates=ContextTemplates(**data["context_templates"]),
            isolation_requirements=IsolationRequirements(**data["isolation_requirements"]),
            metadata=KnowledgeMetadata(**data["metadata"])
        )
    
    def update_usage(self):
        """Update usage tracking."""
        self.metadata.usage_count += 1
        self.metadata.last_updated = datetime.now().isoformat()
    
    def update_effectiveness(self, score: float):
        """Update effectiveness score (0.0-1.0)."""
        if not 0.0 <= score <= 1.0:
            raise ValueError("Effectiveness score must be between 0.0 and 1.0")
        
        # Moving average: new_score = 0.8 * old_score + 0.2 * new_measurement
        self.metadata.effectiveness_score = (
            0.8 * self.metadata.effectiveness_score + 0.2 * score
        )
        self.metadata.last_updated = datetime.now().isoformat()
    
    def add_relationship(self, relationship_type: str, entity_id: str):
        """Add a relationship to another entity."""
        valid_relationships = [
            "enables", "requires", "related", 
            "enhances", "specializes", "generalizes"
        ]
        
        if relationship_type not in valid_relationships:
            raise ValueError(
                f"Invalid relationship type '{relationship_type}'. "
                f"Must be one of: {valid_relationships}"
            )
        
        relationship_list = getattr(self.relationships, relationship_type)
        if entity_id not in relationship_list:
            relationship_list.append(entity_id)
            self.metadata.last_updated = datetime.now().isoformat()
    
    def remove_relationship(self, relationship_type: str, entity_id: str):
        """Remove a relationship to another entity."""
        relationship_list = getattr(self.relationships, relationship_type, None)
        if relationship_list and entity_id in relationship_list:
            relationship_list.remove(entity_id)
            self.metadata.last_updated = datetime.now().isoformat()
    
    def get_all_relationships(self) -> Dict[str, List[str]]:
        """Get all relationships as a dictionary."""
        return {
            "enables": self.relationships.enables,
            "requires": self.relationships.requires,
            "related": self.relationships.related,
            "enhances": self.relationships.enhances,
            "specializes": self.relationships.specializes,
            "generalizes": self.relationships.generalizes
        }
    
    def matches_domain(self, domain: str) -> bool:
        """Check if entity matches the given domain."""
        return self.domain == domain
    
    def matches_framework(self, framework: str) -> bool:
        """Check if entity applies to the given process framework."""
        return framework in self.process_frameworks
    
    def __repr__(self) -> str:
        """String representation of the entity."""
        return (
            f"KnowledgeEntity(id='{self.id}', type='{self.type}', "
            f"name='{self.name}', domain='{self.domain}')"
        )