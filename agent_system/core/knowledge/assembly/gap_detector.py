"""
Knowledge Gap Detector

Identifies missing knowledge that prevents task success and validates context completeness.
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..entity import KnowledgeEntity
from ..storage import KnowledgeStorage
from ..models import ValidationResult, KnowledgeGap
from .analysis_utils import AnalysisUtils

logger = logging.getLogger(__name__)


class GapDetector:
    """Detects knowledge gaps and validates context completeness."""
    
    def __init__(self, storage: KnowledgeStorage):
        """Initialize with knowledge storage."""
        self.storage = storage
    
    def validate_context_completeness(
        self,
        entities: List[KnowledgeEntity],
        task_instruction: str,
        agent_type: str
    ) -> ValidationResult:
        """Validate if context is complete for isolated task success."""
        logger.info(f"Validating context completeness for {agent_type}")
        
        # Get agent-specific knowledge requirements
        agent_entity_id = f"agent_knowledge_{agent_type}"
        agent_entity = self.storage.load_entity(agent_entity_id)
        
        if not agent_entity:
            logger.warning(f"Agent knowledge for {agent_type} not found")
            return ValidationResult(
                is_complete=False,
                completeness_score=0.0,
                missing_requirements=[f"Agent knowledge for {agent_type} not found"],
                isolation_capable=False,
                recommendations=[f"Create knowledge entity: {agent_entity_id}"]
            )
        
        # Check isolation requirements
        required_context = agent_entity.isolation_requirements.minimum_context
        available_context = []
        
        # Collect available context from all entities
        for entity in entities:
            available_context.append(entity.id)
            available_context.append(entity.domain)
            available_context.extend(entity.process_frameworks)
            available_context.extend(entity.metadata.tags)
        
        available_context = list(set(available_context))  # Remove duplicates
        
        # Find missing requirements
        missing_requirements = []
        for requirement in required_context:
            # Check if requirement is satisfied by any available context
            requirement_satisfied = False
            
            for context_item in available_context:
                if (requirement.lower() in context_item.lower() or 
                    context_item.lower() in requirement.lower()):
                    requirement_satisfied = True
                    break
            
            if not requirement_satisfied:
                missing_requirements.append(requirement)
        
        # Calculate completeness score
        if required_context:
            completeness_score = 1.0 - (len(missing_requirements) / len(required_context))
        else:
            completeness_score = 1.0
        
        # Check if task can succeed in isolation
        isolation_capable = completeness_score >= 0.8 and len(missing_requirements) == 0
        
        # Generate recommendations
        recommendations = []
        if missing_requirements:
            recommendations.append(
                f"Add context for: {', '.join(missing_requirements)}"
            )
        if completeness_score < 0.8:
            recommendations.append(
                "Context may be insufficient for isolated task success"
            )
        if not entities:
            recommendations.append(
                "No relevant knowledge entities found - consider creating domain knowledge"
            )
        
        logger.info(f"Context validation: score={completeness_score:.2f}, missing={len(missing_requirements)}")
        
        return ValidationResult(
            is_complete=len(missing_requirements) == 0,
            completeness_score=completeness_score,
            missing_requirements=missing_requirements,
            isolation_capable=isolation_capable,
            recommendations=recommendations
        )
    
    def identify_knowledge_gaps(
        self,
        task_instruction: str,
        agent_type: str,
        failed_task_result: Optional[str] = None,
        context_package=None
    ) -> List[KnowledgeGap]:
        """Identify missing knowledge that prevents task success."""
        gaps = []
        
        # Use provided context package or assemble new one
        if not context_package:
            # Import here to avoid circular dependency
            from .context_assembler import ContextAssembler
            assembler = ContextAssembler(self.storage)
            context_package = assembler.assemble_context_for_task(task_instruction, agent_type)
        
        # Gap 1: Missing context requirements
        if context_package.missing_requirements:
            for req in context_package.missing_requirements:
                gaps.append(KnowledgeGap(
                    gap_type="missing_context",
                    description=f"Required context not found: {req}",
                    priority="high",
                    context={
                        "requirement": req,
                        "agent_type": agent_type,
                        "task_instruction": task_instruction
                    }
                ))
        
        # Gap 2: Low context completeness
        if context_package.completeness_score < 0.8:
            gaps.append(KnowledgeGap(
                gap_type="incomplete_context",
                description=f"Context completeness too low: {context_package.completeness_score:.2f}",
                priority="high" if context_package.completeness_score < 0.5 else "medium",
                context={
                    "completeness_score": context_package.completeness_score,
                    "available_sources": context_package.knowledge_sources
                }
            ))
        
        # Gap 3: Failed task analysis
        if failed_task_result:
            # Analyze failure for patterns
            error_patterns = AnalysisUtils.analyze_failure_patterns(failed_task_result)
            
            for pattern in error_patterns:
                gaps.append(KnowledgeGap(
                    gap_type="execution_failure_pattern",
                    description=f"Knowledge gap identified from failure: {pattern}",
                    priority="high",
                    context={
                        "failure_pattern": pattern,
                        "task_result": failed_task_result[:500]
                    }
                ))
        
        # Gap 4: Missing domain knowledge
        if not context_package.knowledge_sources:
            gaps.append(KnowledgeGap(
                gap_type="missing_domain_knowledge",
                description=f"No knowledge entities found for domain: {context_package.domain}",
                priority="critical",
                context={
                    "domain": context_package.domain,
                    "agent_type": agent_type
                }
            ))
        
        return gaps
    
    def create_context_template(
        self,
        successful_execution: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a context template from a successful execution."""
        try:
            # Extract key information from successful execution
            task_instruction = successful_execution.get("instruction", "")
            agent_type = successful_execution.get("agent_type", "")
            result = successful_execution.get("result", "")
            context_used = successful_execution.get("context_documents", [])
            
            # Analyze patterns in the successful execution
            patterns = AnalysisUtils.extract_execution_patterns(task_instruction, result)
            
            # Create template
            template = {
                "id": f"template_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "agent_type": agent_type,
                "task_pattern": patterns.get("task_pattern", ""),
                "context_requirements": context_used,
                "success_indicators": patterns.get("success_indicators", []),
                "variable_mappings": patterns.get("variables", {}),
                "created_from": successful_execution.get("task_id", 0),
                "created_at": datetime.now().isoformat()
            }
            
            return template
            
        except Exception as e:
            logger.error(f"Error creating context template: {e}")
            return None