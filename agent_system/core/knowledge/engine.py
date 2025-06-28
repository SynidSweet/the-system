"""
Context Assembly Engine for MVP Knowledge System

Assembles complete context packages for tasks and validates their completeness.
Refactored into modular components while maintaining backward compatibility.
"""

from typing import Dict, List, Optional, Any
import logging

from .storage import KnowledgeStorage
from .models import ContextPackage, ValidationResult, KnowledgeGap
from .assembly import ContextAssembler, GapDetector, ContextFormatter, AnalysisUtils

logger = logging.getLogger(__name__)


class ContextAssemblyEngine:
    """Engine for assembling context packages from knowledge entities.
    
    This is the main public interface that coordinates the modular components
    while maintaining backward compatibility with existing code.
    """
    
    def __init__(self, storage: KnowledgeStorage):
        """Initialize with knowledge storage."""
        self.storage = storage
        self.assembler = ContextAssembler(storage)
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
        return self.assembler.assemble_context_for_task(
            task_instruction=task_instruction,
            agent_type=agent_type,
            domain=domain,
            task_id=task_id,
            max_context_size=max_context_size
        )
    
    def validate_context_completeness(
        self,
        entities: List,
        task_instruction: str,
        agent_type: str
    ) -> ValidationResult:
        """Validate if context is complete for isolated task success."""
        return self.gap_detector.validate_context_completeness(
            entities=entities,
            task_instruction=task_instruction,
            agent_type=agent_type
        )
    
    def identify_knowledge_gaps(
        self,
        task_instruction: str,
        agent_type: str,
        failed_task_result: Optional[str] = None
    ) -> List[KnowledgeGap]:
        """Identify missing knowledge that prevents task success."""
        return self.gap_detector.identify_knowledge_gaps(
            task_instruction=task_instruction,
            agent_type=agent_type,
            failed_task_result=failed_task_result
        )
    
    def create_context_template(
        self,
        successful_execution: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a context template from a successful execution."""
        return self.gap_detector.create_context_template(successful_execution)
    
    # Private methods delegated to utility classes for backward compatibility
    def _infer_domain_from_task(self, task_instruction: str) -> str:
        """Infer domain from task instruction using keyword matching."""
        return AnalysisUtils.infer_domain_from_task(task_instruction, self._domain_keywords)
    
    def _get_relevant_entities(
        self,
        task_instruction: str,
        agent_type: str,
        domain: str,
        limit: int = 20
    ) -> List:
        """Get knowledge entities relevant to the task."""
        return self.assembler._get_relevant_entities(task_instruction, agent_type, domain, limit)
    
    def _build_context_text(
        self,
        entities: List,
        task_instruction: str,
        agent_type: str,
        max_size: int = 10000
    ) -> str:
        """Build comprehensive context text from knowledge entities."""
        return self.formatter.build_context_text(entities, task_instruction, agent_type, max_size)
    
    def _analyze_failure_patterns(self, failure_result: str) -> List[str]:
        """Analyze failure result for knowledge gap patterns."""
        return AnalysisUtils.analyze_failure_patterns(failure_result)
    
    def _extract_execution_patterns(
        self,
        task_instruction: str,
        result: str
    ) -> Dict[str, Any]:
        """Extract patterns from successful execution."""
        return AnalysisUtils.extract_execution_patterns(task_instruction, result)
    
    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """Load domain keywords for inference."""
        return AnalysisUtils.load_domain_keywords()


# Backward compatibility exports
__all__ = [
    "ContextAssemblyEngine",
    "ContextPackage", 
    "ValidationResult",
    "KnowledgeGap"
]