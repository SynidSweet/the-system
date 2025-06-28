"""
Knowledge Storage Manager for MVP System

Provides file-based storage for knowledge entities with search and retrieval capabilities.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Set, Any
import logging
from datetime import datetime

from .entity import KnowledgeEntity

logger = logging.getLogger(__name__)


class KnowledgeStorage:
    """File-based storage manager for knowledge entities."""
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        """Initialize storage with the knowledge directory."""
        self.knowledge_dir = Path(knowledge_dir)
        self.ensure_directories()
        self._entity_cache: Dict[str, KnowledgeEntity] = {}
        self._index: Dict[str, str] = {}  # entity_id -> subdirectory mapping
        self._build_index()
    
    def ensure_directories(self):
        """Create knowledge directory structure if it doesn't exist."""
        subdirs = ["domains", "processes", "agents", "tools", "patterns", "system", "templates"]
        for subdir in subdirs:
            (self.knowledge_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def _build_index(self):
        """Build an index of entity IDs to their subdirectories."""
        self._index.clear()
        for subdir in ["domains", "processes", "agents", "tools", "patterns", "system"]:
            type_dir = self.knowledge_dir / subdir
            if type_dir.exists():
                for file_path in type_dir.glob("*.json"):
                    self._index[file_path.stem] = subdir
    
    def save_entity(self, entity: KnowledgeEntity) -> bool:
        """Save knowledge entity to appropriate subdirectory."""
        try:
            subdir = self._get_subdir_for_type(entity.type)
            file_path = self.knowledge_dir / subdir / f"{entity.id}.json"
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Update last_updated timestamp
            entity.metadata.last_updated = datetime.now().isoformat()
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entity.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update cache and index
            self._entity_cache[entity.id] = entity
            self._index[entity.id] = subdir
            
            logger.info(f"Saved knowledge entity: {entity.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving entity {entity.id}: {e}")
            return False
    
    def load_entity(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """Load knowledge entity by ID."""
        # Check cache first
        if entity_id in self._entity_cache:
            return self._entity_cache[entity_id]
        
        # Check index for location
        if entity_id in self._index:
            subdir = self._index[entity_id]
            file_path = self.knowledge_dir / subdir / f"{entity_id}.json"
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    entity = KnowledgeEntity.from_dict(data)
                    self._entity_cache[entity_id] = entity
                    return entity
                except Exception as e:
                    logger.error(f"Error loading entity {entity_id}: {e}")
                    return None
        
        # Search all subdirectories if not in index
        for subdir in ["domains", "processes", "agents", "tools", "patterns", "system"]:
            file_path = self.knowledge_dir / subdir / f"{entity_id}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    entity = KnowledgeEntity.from_dict(data)
                    self._entity_cache[entity_id] = entity
                    self._index[entity_id] = subdir
                    return entity
                except Exception as e:
                    logger.error(f"Error loading entity {entity_id}: {e}")
                    return None
        
        return None
    
    def delete_entity(self, entity_id: str) -> bool:
        """Delete a knowledge entity."""
        if entity_id in self._index:
            subdir = self._index[entity_id]
            file_path = self.knowledge_dir / subdir / f"{entity_id}.json"
            
            try:
                if file_path.exists():
                    file_path.unlink()
                
                # Remove from cache and index
                self._entity_cache.pop(entity_id, None)
                self._index.pop(entity_id, None)
                
                logger.info(f"Deleted knowledge entity: {entity_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting entity {entity_id}: {e}")
                return False
        
        return False
    
    def list_entities_by_type(self, entity_type: str) -> List[str]:
        """List all entity IDs of a specific type."""
        subdir = self._get_subdir_for_type(entity_type)
        type_dir = self.knowledge_dir / subdir
        
        if not type_dir.exists():
            return []
        
        return [f.stem for f in type_dir.glob("*.json")]
    
    def list_all_entities(self) -> Iterator[KnowledgeEntity]:
        """Iterate through all knowledge entities."""
        for subdir in ["domains", "processes", "agents", "tools", "patterns", "system"]:
            type_dir = self.knowledge_dir / subdir
            if type_dir.exists():
                for file_path in type_dir.glob("*.json"):
                    entity = self.load_entity(file_path.stem)
                    if entity:
                        yield entity
    
    def search_entities(
        self, 
        query: str, 
        entity_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeEntity]:
        """Search entities by content with optional filters."""
        results = []
        query_lower = query.lower()
        
        for entity in self.list_all_entities():
            # Apply type filter
            if entity_type and entity.type != entity_type:
                continue
            
            # Apply domain filter
            if domain and entity.domain != domain:
                continue
            
            # Search in multiple fields
            searchable_text = " ".join([
                entity.id.lower(),
                entity.name.lower(),
                entity.domain.lower(),
                entity.content.summary.lower(),
                " ".join(entity.content.core_concepts).lower(),
                " ".join(entity.metadata.tags).lower()
            ])
            
            if query_lower in searchable_text:
                results.append(entity)
                
                if len(results) >= limit:
                    break
        
        # Sort by relevance (simple scoring based on query occurrence)
        results.sort(
            key=lambda e: searchable_text.count(query_lower),
            reverse=True
        )
        
        return results
    
    def get_entities_by_domain(self, domain: str) -> List[KnowledgeEntity]:
        """Get all entities for a specific domain."""
        return [
            entity for entity in self.list_all_entities() 
            if entity.matches_domain(domain)
        ]
    
    def get_entities_by_process_framework(self, framework: str) -> List[KnowledgeEntity]:
        """Get all entities that apply to a specific process framework."""
        return [
            entity for entity in self.list_all_entities()
            if entity.matches_framework(framework)
        ]
    
    def get_related_entities(self, entity_id: str) -> Dict[str, List[KnowledgeEntity]]:
        """Get all entities related to the given entity."""
        entity = self.load_entity(entity_id)
        if not entity:
            return {}
        
        related = {
            "enables": [],
            "requires": [],
            "related": [],
            "enhances": [],
            "specializes": [],
            "generalizes": []
        }
        
        relationships = entity.get_all_relationships()
        
        for rel_type, entity_ids in relationships.items():
            for rel_id in entity_ids:
                rel_entity = self.load_entity(rel_id)
                if rel_entity:
                    related[rel_type].append(rel_entity)
        
        return related
    
    def validate_relationships(self) -> Dict[str, List[str]]:
        """Validate all entity relationships and return missing entities."""
        missing_relationships = {}
        
        for entity in self.list_all_entities():
            missing = []
            relationships = entity.get_all_relationships()
            
            for rel_type, entity_ids in relationships.items():
                for rel_id in entity_ids:
                    if not self.load_entity(rel_id):
                        missing.append(f"{rel_type}: {rel_id}")
            
            if missing:
                missing_relationships[entity.id] = missing
        
        return missing_relationships
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        stats = {
            "total_entities": 0,
            "entities_by_type": {},
            "entities_by_domain": {},
            "avg_relationships": 0,
            "avg_effectiveness": 0,
            "most_used_entities": [],
            "least_effective_entities": []
        }
        
        entities = list(self.list_all_entities())
        stats["total_entities"] = len(entities)
        
        # Count by type and domain
        type_counts = {}
        domain_counts = {}
        total_relationships = 0
        total_effectiveness = 0
        
        for entity in entities:
            # Type counts
            type_counts[entity.type] = type_counts.get(entity.type, 0) + 1
            
            # Domain counts
            domain_counts[entity.domain] = domain_counts.get(entity.domain, 0) + 1
            
            # Relationship counts
            relationships = entity.get_all_relationships()
            for rel_list in relationships.values():
                total_relationships += len(rel_list)
            
            # Effectiveness
            total_effectiveness += entity.metadata.effectiveness_score
        
        stats["entities_by_type"] = type_counts
        stats["entities_by_domain"] = domain_counts
        
        if entities:
            stats["avg_relationships"] = total_relationships / len(entities)
            stats["avg_effectiveness"] = total_effectiveness / len(entities)
            
            # Most used entities
            entities.sort(key=lambda e: e.metadata.usage_count, reverse=True)
            stats["most_used_entities"] = [
                {"id": e.id, "name": e.name, "usage_count": e.metadata.usage_count}
                for e in entities[:10]
            ]
            
            # Least effective entities
            entities.sort(key=lambda e: e.metadata.effectiveness_score)
            stats["least_effective_entities"] = [
                {"id": e.id, "name": e.name, "effectiveness": e.metadata.effectiveness_score}
                for e in entities[:10] if e.metadata.effectiveness_score < 0.5
            ]
        
        return stats
    
    def export_to_graph_format(self) -> Dict[str, Any]:
        """Export knowledge base to a format suitable for graph databases."""
        nodes = []
        edges = []
        
        for entity in self.list_all_entities():
            # Create node
            node = {
                "id": entity.id,
                "labels": [entity.type, entity.domain],
                "properties": {
                    "name": entity.name,
                    "version": entity.version,
                    "summary": entity.content.summary,
                    "usage_count": entity.metadata.usage_count,
                    "effectiveness_score": entity.metadata.effectiveness_score,
                    "created_at": entity.metadata.created_at,
                    "last_updated": entity.metadata.last_updated
                }
            }
            nodes.append(node)
            
            # Create edges
            relationships = entity.get_all_relationships()
            for rel_type, target_ids in relationships.items():
                for target_id in target_ids:
                    edge = {
                        "source": entity.id,
                        "target": target_id,
                        "type": rel_type,
                        "properties": {}
                    }
                    edges.append(edge)
        
        return {"nodes": nodes, "edges": edges}
    
    def _get_subdir_for_type(self, entity_type: str) -> str:
        """Map entity type to storage subdirectory."""
        type_mapping = {
            "domain": "domains",
            "process": "processes",
            "agent": "agents",
            "tool": "tools",
            "pattern": "patterns",
            "system": "system"
        }
        return type_mapping.get(entity_type, "system")
    
    def clear_cache(self):
        """Clear the entity cache."""
        self._entity_cache.clear()
        logger.info("Knowledge entity cache cleared")