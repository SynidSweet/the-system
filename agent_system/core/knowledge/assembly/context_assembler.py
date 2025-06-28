"""
Context Assembler

Core engine for assembling context packages from knowledge entities.
"""

from typing import List, Optional, Set
import logging

from ..entity import KnowledgeEntity
from ..storage import KnowledgeStorage
from ..models import ContextPackage
from .gap_detector import GapDetector
from .context_formatter import ContextFormatter
from .analysis_utils import AnalysisUtils

logger = logging.getLogger(__name__)


class ContextAssembler:
    """Engine for assembling context packages from knowledge entities."""
    
    def __init__(self, storage: KnowledgeStorage):
        """Initialize with knowledge storage."""
        self.storage = storage
        self.gap_detector = GapDetector(storage)
        self.formatter = ContextFormatter()
        self._domain_keywords = AnalysisUtils.load_domain_keywords()
    
    def assemble_context_for_task(
        self,
        task_instruction: str,
        agent_type: str,
        domain: Optional[str] = None,
        task_id: int = 0,
        max_context_size: int = 10000
    ) -> ContextPackage:
        """Assemble complete context package for a task."""
        logger.info(f"Assembling context for agent {agent_type} on task: {task_instruction[:100]}...")
        
        # Determine domain if not provided
        if not domain:
            domain = AnalysisUtils.infer_domain_from_task(task_instruction, self._domain_keywords)
            logger.info(f"Inferred domain: {domain}")
        
        # Get relevant knowledge entities
        relevant_entities = self._get_relevant_entities(task_instruction, agent_type, domain)
        logger.info(f"Found {len(relevant_entities)} relevant entities")
        
        # Build context text
        context_text = self.formatter.build_context_text(
            relevant_entities, 
            task_instruction, 
            agent_type,
            max_context_size
        )
        
        # Validate completeness
        validation = self.gap_detector.validate_context_completeness(
            relevant_entities, 
            task_instruction, 
            agent_type
        )
        
        # Create context documents list
        context_documents = [entity.id for entity in relevant_entities]
        
        # Update usage statistics
        for entity in relevant_entities:
            entity.update_usage()
            self.storage.save_entity(entity)
        
        return ContextPackage(
            task_id=task_id,
            agent_type=agent_type,
            domain=domain,
            context_documents=context_documents,
            context_text=context_text,
            completeness_score=validation.completeness_score,
            missing_requirements=validation.missing_requirements,
            knowledge_sources=[entity.id for entity in relevant_entities]
        )
    
    def _get_relevant_entities(
        self,
        task_instruction: str,
        agent_type: str,
        domain: str,
        limit: int = 20
    ) -> List[KnowledgeEntity]:
        """Get knowledge entities relevant to the task."""
        relevant_entities = []
        seen_ids = set()
        
        # Priority 1: Agent-specific knowledge
        agent_entity_id = f"agent_knowledge_{agent_type}"
        agent_entity = self.storage.load_entity(agent_entity_id)
        if agent_entity and agent_entity.id not in seen_ids:
            relevant_entities.append(agent_entity)
            seen_ids.add(agent_entity.id)
        
        # Priority 2: Domain knowledge
        domain_entities = self.storage.get_entities_by_domain(domain)
        for entity in domain_entities[:5]:  # Limit domain entities
            if entity.id not in seen_ids:
                relevant_entities.append(entity)
                seen_ids.add(entity.id)
        
        # Priority 3: Process frameworks used by agent
        if agent_entity:
            for framework in agent_entity.process_frameworks:
                framework_entities = self.storage.get_entities_by_process_framework(framework)
                for entity in framework_entities[:3]:  # Limit per framework
                    if entity.id not in seen_ids:
                        relevant_entities.append(entity)
                        seen_ids.add(entity.id)
        
        # Priority 4: System knowledge
        system_entities = self.storage.list_entities_by_type("system")
        for entity_id in system_entities[:3]:  # Core system knowledge
            entity = self.storage.load_entity(entity_id)
            if entity and entity.id not in seen_ids:
                relevant_entities.append(entity)
                seen_ids.add(entity.id)
        
        # Priority 5: Search for task-relevant knowledge
        search_results = self.storage.search_entities(task_instruction, limit=10)
        for entity in search_results:
            if entity.id not in seen_ids and len(relevant_entities) < limit:
                relevant_entities.append(entity)
                seen_ids.add(entity.id)
        
        # Priority 6: Include related entities
        related_to_include = []
        for entity in relevant_entities[:5]:  # Only check first 5 to avoid explosion
            related = self.storage.get_related_entities(entity.id)
            for rel_type in ["requires", "enables"]:
                for rel_entity in related.get(rel_type, [])[:2]:
                    if rel_entity.id not in seen_ids:
                        related_to_include.append(rel_entity)
                        seen_ids.add(rel_entity.id)
        
        relevant_entities.extend(related_to_include[:5])  # Limit related entities
        
        # Sort by relevance (usage count and effectiveness)
        relevant_entities.sort(
            key=lambda e: (e.metadata.usage_count * 0.3 + e.metadata.effectiveness_score * 0.7),
            reverse=True
        )
        
        return relevant_entities[:limit]