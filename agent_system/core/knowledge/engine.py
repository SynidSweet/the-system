"""
Context Assembly Engine for MVP Knowledge System

Assembles complete context packages for tasks and validates their completeness.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import logging
import re
from datetime import datetime

from .storage import KnowledgeStorage
from .entity import KnowledgeEntity

logger = logging.getLogger(__name__)


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


class ContextAssemblyEngine:
    """Engine for assembling context packages from knowledge entities."""
    
    def __init__(self, storage: KnowledgeStorage):
        """Initialize with knowledge storage."""
        self.storage = storage
        self._domain_keywords = self._load_domain_keywords()
    
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
            domain = self._infer_domain_from_task(task_instruction)
            logger.info(f"Inferred domain: {domain}")
        
        # Get relevant knowledge entities
        relevant_entities = self._get_relevant_entities(task_instruction, agent_type, domain)
        logger.info(f"Found {len(relevant_entities)} relevant entities")
        
        # Build context text
        context_text = self._build_context_text(
            relevant_entities, 
            task_instruction, 
            agent_type,
            max_context_size
        )
        
        # Validate completeness
        validation = self.validate_context_completeness(
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
        failed_task_result: Optional[str] = None
    ) -> List[KnowledgeGap]:
        """Identify missing knowledge that prevents task success."""
        gaps = []
        
        # Assemble context to find missing requirements
        context_package = self.assemble_context_for_task(task_instruction, agent_type)
        
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
            error_patterns = self._analyze_failure_patterns(failed_task_result)
            
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
            patterns = self._extract_execution_patterns(task_instruction, result)
            
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
    
    def _infer_domain_from_task(self, task_instruction: str) -> str:
        """Infer domain from task instruction using keyword matching."""
        task_lower = task_instruction.lower()
        domain_scores = {}
        
        for domain, keywords in self._domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            # Return domain with highest score
            return max(domain_scores, key=domain_scores.get)
        
        return "general"
    
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
    
    def _build_context_text(
        self,
        entities: List[KnowledgeEntity],
        task_instruction: str,
        agent_type: str,
        max_size: int = 10000
    ) -> str:
        """Build comprehensive context text from knowledge entities."""
        context_parts = []
        current_size = 0
        
        # Start with task context
        context_parts.append(f"# Task Context")
        context_parts.append(f"Task: {task_instruction}")
        context_parts.append(f"Agent: {agent_type}")
        context_parts.append("")
        
        # Add agent-specific context first
        agent_entities = [e for e in entities if e.type == "agent"]
        for entity in agent_entities:
            section = self._format_agent_context(entity)
            section_size = len(section)
            
            if current_size + section_size < max_size:
                context_parts.extend(section)
                current_size += section_size
        
        # Add system principles
        system_entities = [e for e in entities if e.type == "system"]
        for entity in system_entities[:2]:  # Limit system context
            section = self._format_system_context(entity)
            section_size = len("\n".join(section))
            
            if current_size + section_size < max_size:
                context_parts.extend(section)
                current_size += section_size
        
        # Add domain knowledge
        domain_entities = [e for e in entities if e.type == "domain"]
        for entity in domain_entities:
            section = self._format_domain_context(entity)
            section_size = len("\n".join(section))
            
            if current_size + section_size < max_size:
                context_parts.extend(section)
                current_size += section_size
        
        # Add process frameworks
        process_entities = [e for e in entities if e.type == "process"]
        for entity in process_entities:
            section = self._format_process_context(entity)
            section_size = len("\n".join(section))
            
            if current_size + section_size < max_size:
                context_parts.extend(section)
                current_size += section_size
        
        # Add relevant patterns
        pattern_entities = [e for e in entities if e.type == "pattern"]
        for entity in pattern_entities[:3]:  # Limit patterns
            section = self._format_pattern_context(entity)
            section_size = len("\n".join(section))
            
            if current_size + section_size < max_size:
                context_parts.extend(section)
                current_size += section_size
        
        # Add tool knowledge if relevant
        tool_entities = [e for e in entities if e.type == "tool"]
        for entity in tool_entities[:3]:  # Limit tools
            section = self._format_tool_context(entity)
            section_size = len("\n".join(section))
            
            if current_size + section_size < max_size:
                context_parts.extend(section)
                current_size += section_size
        
        return "\n".join(context_parts)
    
    def _format_agent_context(self, entity: KnowledgeEntity) -> List[str]:
        """Format agent knowledge entity for context."""
        parts = []
        parts.append(f"## Agent Specialization: {entity.name}")
        parts.append(entity.content.summary)
        parts.append("")
        
        if entity.content.core_concepts:
            parts.append("### Core Concepts:")
            for concept in entity.content.core_concepts[:5]:
                parts.append(f"- {concept}")
            parts.append("")
        
        if entity.content.procedures:
            parts.append("### Key Procedures:")
            for proc in entity.content.procedures[:4]:
                parts.append(f"- {proc}")
            parts.append("")
        
        if entity.content.quality_criteria:
            parts.append("### Success Criteria:")
            for criteria in entity.content.quality_criteria[:3]:
                parts.append(f"- {criteria}")
            parts.append("")
        
        return parts
    
    def _format_system_context(self, entity: KnowledgeEntity) -> List[str]:
        """Format system knowledge entity for context."""
        parts = []
        parts.append(f"## System Knowledge: {entity.name}")
        parts.append(entity.content.summary)
        
        if entity.content.core_concepts:
            parts.append("### Principles:")
            for concept in entity.content.core_concepts[:4]:
                parts.append(f"- {concept}")
        
        parts.append("")
        return parts
    
    def _format_domain_context(self, entity: KnowledgeEntity) -> List[str]:
        """Format domain knowledge entity for context."""
        parts = []
        parts.append(f"## Domain: {entity.name}")
        parts.append(entity.content.summary[:200] + "...")
        
        if entity.content.procedures:
            parts.append("### Procedures:")
            for proc in entity.content.procedures[:3]:
                parts.append(f"- {proc}")
        
        parts.append("")
        return parts
    
    def _format_process_context(self, entity: KnowledgeEntity) -> List[str]:
        """Format process knowledge entity for context."""
        parts = []
        parts.append(f"## Process Framework: {entity.name}")
        parts.append(entity.content.summary[:200] + "...")
        
        if entity.content.procedures:
            parts.append("### Steps:")
            for proc in entity.content.procedures[:4]:
                parts.append(f"- {proc}")
        
        parts.append("")
        return parts
    
    def _format_pattern_context(self, entity: KnowledgeEntity) -> List[str]:
        """Format pattern knowledge entity for context."""
        parts = []
        parts.append(f"## Success Pattern: {entity.name}")
        parts.append(entity.content.summary[:150] + "...")
        
        if entity.content.quality_criteria:
            parts.append("### When to use:")
            for criteria in entity.content.quality_criteria[:2]:
                parts.append(f"- {criteria}")
        
        parts.append("")
        return parts
    
    def _format_tool_context(self, entity: KnowledgeEntity) -> List[str]:
        """Format tool knowledge entity for context."""
        parts = []
        parts.append(f"## Tool: {entity.name}")
        parts.append(entity.content.summary[:150] + "...")
        parts.append("")
        return parts
    
    def _analyze_failure_patterns(self, failure_result: str) -> List[str]:
        """Analyze failure result for knowledge gap patterns."""
        patterns = []
        
        # Common failure indicators
        if "not found" in failure_result.lower():
            patterns.append("Missing resource or knowledge")
        if "permission" in failure_result.lower():
            patterns.append("Permission or access knowledge gap")
        if "unknown" in failure_result.lower() or "undefined" in failure_result.lower():
            patterns.append("Undefined concept or procedure")
        if "failed to" in failure_result.lower():
            patterns.append("Procedure execution knowledge gap")
        if "error" in failure_result.lower():
            patterns.append("Error handling knowledge gap")
        
        return patterns
    
    def _extract_execution_patterns(
        self,
        task_instruction: str,
        result: str
    ) -> Dict[str, Any]:
        """Extract patterns from successful execution."""
        patterns = {
            "task_pattern": "",
            "success_indicators": [],
            "variables": {}
        }
        
        # Extract task pattern (simplified)
        task_words = task_instruction.lower().split()
        if len(task_words) > 0:
            # Identify action verbs
            action_verbs = ["create", "update", "analyze", "implement", "design", 
                          "build", "test", "validate", "optimize", "review"]
            for verb in action_verbs:
                if verb in task_words:
                    patterns["task_pattern"] = f"{verb}_based_task"
                    break
        
        # Extract success indicators from result
        if "success" in result.lower():
            patterns["success_indicators"].append("explicit_success")
        if "complet" in result.lower():
            patterns["success_indicators"].append("completion_indicator")
        if "created" in result.lower() or "updated" in result.lower():
            patterns["success_indicators"].append("artifact_creation")
        
        # Extract potential variables (simplified)
        # Look for quoted strings or specific patterns
        quoted_strings = re.findall(r'"([^"]*)"', task_instruction)
        if quoted_strings:
            patterns["variables"]["targets"] = quoted_strings
        
        return patterns
    
    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """Load domain keywords for inference."""
        return {
            "software_development": [
                "code", "develop", "implement", "programming", "software",
                "function", "class", "module", "debug", "compile", "build"
            ],
            "system_architecture": [
                "system", "architecture", "design", "framework", "structure",
                "component", "integration", "infrastructure"
            ],
            "task_management": [
                "task", "project", "plan", "organize", "coordinate",
                "schedule", "milestone", "deadline", "workflow"
            ],
            "quality_assurance": [
                "test", "validate", "quality", "review", "evaluate",
                "verify", "audit", "check", "assessment"
            ],
            "knowledge_management": [
                "document", "knowledge", "context", "information",
                "guide", "reference", "learn", "teach"
            ],
            "data_processing": [
                "data", "process", "analyze", "transform", "pipeline",
                "etl", "database", "query", "aggregate"
            ],
            "optimization": [
                "optimize", "improve", "enhance", "performance",
                "efficiency", "refactor", "streamline"
            ],
            "deployment": [
                "deploy", "release", "publish", "launch", "rollout",
                "production", "staging", "environment"
            ]
        }