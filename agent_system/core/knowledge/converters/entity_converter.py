"""
Entity converter for creating knowledge entities from documentation.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..entity import (
    KnowledgeEntity, KnowledgeContent, KnowledgeRelationships,
    ContextTemplates, IsolationRequirements, KnowledgeMetadata
)
from .extraction_utils import ExtractionUtils

logger = logging.getLogger(__name__)


class EntityConverter:
    """Converts parsed documentation into knowledge entities."""
    
    def __init__(self, timestamp: str = None):
        """Initialize with optional timestamp."""
        self.timestamp = timestamp or datetime.now().isoformat()
        self.extractor = ExtractionUtils()
    
    def create_agent_entity(self, agent_name: str, content: str) -> Optional[KnowledgeEntity]:
        """Create agent knowledge entity from guide content."""
        # Extract sections using regex
        sections = self.extractor.extract_sections(content)
        
        if not sections.get("purpose"):
            logger.warning(f"Could not extract purpose for {agent_name}")
            return None
        
        # Extract various components
        core_concepts = self.extractor.extract_concepts_from_approach(sections.get("approach", ""))
        procedures = self.extractor.extract_procedures(content)
        examples = self.extractor.extract_examples(content)
        quality_criteria = self.extractor.extract_quality_criteria(sections.get("success", ""))
        common_pitfalls = self.extractor.extract_pitfalls(content)
        
        # Determine domain and frameworks
        domain = self.extractor.infer_domain_from_agent_name(agent_name)
        frameworks = self.extractor.infer_process_frameworks(agent_name)
        
        # Create the entity
        entity = KnowledgeEntity(
            id=f"agent_knowledge_{agent_name}",
            type="agent",
            name=f"{agent_name.replace('_', ' ').title()} Specialization",
            version="1.0.0",
            domain=domain,
            process_frameworks=frameworks,
            content=KnowledgeContent(
                summary=sections["purpose"][:300].strip() + "...",
                core_concepts=core_concepts[:10],
                procedures=procedures[:8],
                examples=examples[:5],
                quality_criteria=quality_criteria[:6],
                common_pitfalls=common_pitfalls[:4]
            ),
            relationships=KnowledgeRelationships(
                enables=[],  # Will be populated in relationship creation
                requires=self.extractor.extract_required_knowledge(content),
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"As {agent_name}: {sections['purpose'][:100].strip()}...",
                agent_context=f"{agent_name} specializes in {domain} using systematic approaches.",
                process_context=f"Follow {agent_name} procedures for {domain} tasks."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[f"{agent_name}_guide", f"{domain}_reference"],
                validation_criteria=[
                    "Can execute tasks independently",
                    "Has required domain knowledge",
                    "Understands quality requirements"
                ]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="agent_guide_conversion",
                tags=[agent_name, domain, "agent_specialization"],
                specialization_level="high"
            )
        )
        
        return entity
    
    def create_system_entity(
        self, 
        entity_id: str, 
        display_name: str, 
        content: str
    ) -> Optional[KnowledgeEntity]:
        """Create system/architecture knowledge entity."""
        sections = self.extractor.extract_sections(content)
        
        # Extract system concepts and principles
        system_concepts = self.extractor.extract_system_concepts(content, sections)
        principles = self.extractor.extract_principles(content)
        
        # Convert principles to procedures format
        procedures = []
        for principle in principles[:5]:
            procedures.append(f"{principle['name']}: {principle['description']}")
        
        # Extract examples from architecture docs
        examples = self.extractor.extract_examples(content)
        
        # Create quality criteria based on architecture type
        quality_criteria = self._extract_architecture_quality_criteria(entity_id, content)
        
        # Determine domain
        domain = self._determine_system_domain(entity_id)
        
        entity = KnowledgeEntity(
            id=entity_id,
            type="system",
            name=display_name,
            version="1.0.0",
            domain=domain,
            process_frameworks=["architectural_design", "system_implementation"],
            content=KnowledgeContent(
                summary=sections.get("overview", "System architecture component")[:300] + "...",
                core_concepts=system_concepts[:12],
                procedures=procedures,
                examples=examples[:4],
                quality_criteria=quality_criteria,
                common_pitfalls=self.extractor.extract_pitfalls(content)
            ),
            relationships=KnowledgeRelationships(
                enables=["systematic_development", "architectural_consistency"],
                requires=["process_first_understanding"],
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"Implementing {display_name} patterns",
                agent_context=f"Understanding of {display_name} required",
                process_context=f"Follow {display_name} guidelines"
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["system_architecture", entity_id],
                validation_criteria=[
                    "Understands architectural patterns",
                    "Can implement within guidelines"
                ]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="architecture_documentation",
                tags=[domain, "architecture", "system_design"],
                framework_type="foundational"
            )
        )
        
        return entity
    
    def create_process_entity(
        self,
        process_name: str,
        domain: str,
        steps: List[str],
        docstring: str = ""
    ) -> KnowledgeEntity:
        """Create process knowledge entity from code analysis."""
        # Clean process name for display
        display_name = process_name.replace('_', ' ').title()
        
        # Extract concepts from docstring
        concepts = []
        if docstring:
            # Extract key phrases from docstring
            doc_lines = docstring.strip().split('\n')
            for line in doc_lines[:5]:
                if len(line) > 10:
                    concepts.append(line.strip())
        
        # Quality criteria for processes
        quality_criteria = [
            "All steps execute successfully",
            "Output meets validation criteria",
            "Process completes within time limits",
            "No unhandled exceptions occur",
            "Results are reproducible"
        ]
        
        entity = KnowledgeEntity(
            id=f"process_knowledge_{process_name}",
            type="process",
            name=f"{display_name} Process",
            version="1.0.0",
            domain=domain,
            process_frameworks=[process_name, "systematic_execution"],
            content=KnowledgeContent(
                summary=docstring[:200] if docstring else f"{display_name} process implementation",
                core_concepts=concepts[:8],
                procedures=steps[:10],
                examples=[],
                quality_criteria=quality_criteria[:5],
                common_pitfalls=["Skipping validation steps", "Ignoring error conditions"]
            ),
            relationships=KnowledgeRelationships(
                enables=[f"{process_name}_execution"],
                requires=["process_framework_understanding"],
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"Executing {display_name} process",
                agent_context=f"Process executor for {domain}",
                process_context=f"Follow {process_name} implementation"
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[f"{process_name}_implementation", "process_guidelines"],
                validation_criteria=[
                    "Can execute process steps",
                    "Understands validation requirements"
                ]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="process_code_analysis",
                tags=[process_name, domain, "process_implementation"],
                code_based=True
            )
        )
        
        return entity
    
    def create_tool_entity(
        self,
        tool_name: str,
        category: str,
        content: str
    ) -> Optional[KnowledgeEntity]:
        """Create tool knowledge entity from documentation."""
        sections = self.extractor.extract_sections(content)
        
        # Extract tool-specific information
        capabilities = self._extract_tool_capabilities(content)
        parameters = self._extract_tool_parameters(content)
        usage_examples = self.extractor.extract_examples(content)
        
        # Create procedures from capabilities
        procedures = []
        for cap in capabilities[:5]:
            procedures.append(f"Use {tool_name} to {cap}")
        
        entity = KnowledgeEntity(
            id=f"tool_knowledge_{tool_name}_{category}",
            type="tool",
            name=f"{tool_name.replace('_', ' ').title()} Tool",
            version="1.0.0",
            domain=f"{category}_tools",
            process_frameworks=["tool_utilization", f"{category}_tool_framework"],
            content=KnowledgeContent(
                summary=sections.get("overview", f"{tool_name} tool capabilities")[:250] + "...",
                core_concepts=capabilities[:8],
                procedures=procedures,
                examples=usage_examples[:4],
                quality_criteria=[
                    "Tool executes without errors",
                    "Parameters are validated",
                    "Output matches expectations"
                ],
                common_pitfalls=["Missing required parameters", "Incorrect permission scope"]
            ),
            relationships=KnowledgeRelationships(
                enables=[f"{category}_capabilities"],
                requires=["tool_permission_model"],
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"Using {tool_name} for {category} operations",
                agent_context=f"Agent with {tool_name} access",
                process_context=f"Follow {category} tool guidelines"
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[f"{tool_name}_documentation", "tool_guidelines"],
                validation_criteria=[
                    "Understands tool parameters",
                    "Can handle tool responses"
                ]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="tool_documentation",
                tags=[tool_name, category, "tools"],
                tool_category=category
            )
        )
        
        return entity
    
    def create_initialization_task_entity(
        self,
        task_name: str,
        task_id: str,
        dependencies: List[str],
        outcomes: List[str]
    ) -> KnowledgeEntity:
        """Create knowledge entity for initialization tasks."""
        entity = KnowledgeEntity(
            id=f"init_task_{task_id}",
            type="pattern",
            name=task_name,
            version="1.0.0",
            domain="system_initialization",
            process_frameworks=["initialization_sequence", "bootstrap_process"],
            content=KnowledgeContent(
                summary=f"Initialization task: {task_name}",
                core_concepts=outcomes[:5],
                procedures=[f"Execute {task_name} after dependencies"],
                examples=[],
                quality_criteria=["All dependencies met", "Outcomes achieved"],
                common_pitfalls=["Skipping dependencies", "Incomplete execution"]
            ),
            relationships=KnowledgeRelationships(
                enables=outcomes,
                requires=dependencies,
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"Performing {task_name}",
                agent_context="System initialization context",
                process_context="Follow initialization sequence"
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["initialization_guide"] + dependencies,
                validation_criteria=["Dependencies satisfied", "Can produce outcomes"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="initialization_sequence",
                tags=["initialization", "bootstrap", task_id],
                sequence_order=int(task_id) if task_id.isdigit() else 0
            )
        )
        
        return entity
    
    def create_domain_entity(self, domain: str) -> KnowledgeEntity:
        """Create basic domain knowledge entity."""
        entity = KnowledgeEntity(
            id=f"domain_{domain}",
            type="domain",
            name=f"{domain.replace('_', ' ').title()} Domain",
            version="1.0.0",
            domain=domain,
            process_frameworks=[f"{domain}_framework"],
            content=KnowledgeContent(
                summary=f"Domain knowledge for {domain}",
                core_concepts=[f"{domain}_principles", f"{domain}_patterns"],
                procedures=[],
                examples=[],
                quality_criteria=["Domain expertise demonstrated"],
                common_pitfalls=[]
            ),
            relationships=KnowledgeRelationships(
                enables=[f"{domain}_tasks"],
                requires=[],
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"Working in {domain} domain",
                agent_context=f"Domain expert for {domain}",
                process_context=f"Follow {domain} best practices"
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[domain],
                validation_criteria=["Understands domain"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="domain_creation",
                tags=[domain, "domain_knowledge"],
                auto_generated=True
            )
        )
        
        return entity
    
    def _extract_architecture_quality_criteria(self, entity_id: str, content: str) -> List[str]:
        """Extract quality criteria specific to architecture types."""
        criteria = []
        
        if "entity" in entity_id:
            criteria.extend([
                "All entities follow standard interface",
                "Relationships properly defined",
                "CRUD operations consistent"
            ])
        elif "process" in entity_id:
            criteria.extend([
                "Process frameworks established before execution",
                "Isolated task success enabled",
                "Systematic decomposition achieved"
            ])
        elif "event" in entity_id:
            criteria.extend([
                "All events properly tracked",
                "Event data structured consistently",
                "Analytics queries performant"
            ])
        elif "runtime" in entity_id:
            criteria.extend([
                "Agent execution within boundaries",
                "State transitions valid",
                "Resource limits enforced"
            ])
        
        # Add general architecture criteria
        criteria.extend([
            "Architecture patterns followed",
            "Integration points well-defined"
        ])
        
        return criteria[:6]
    
    def _determine_system_domain(self, entity_id: str) -> str:
        """Determine domain for system entities."""
        if "entity" in entity_id:
            return "entity_management"
        elif "process" in entity_id:
            return "process_architecture"
        elif "event" in entity_id:
            return "event_tracking"
        elif "runtime" in entity_id:
            return "execution_runtime"
        else:
            return "system_architecture"
    
    def _extract_tool_capabilities(self, content: str) -> List[str]:
        """Extract tool capabilities from documentation."""
        capabilities = []
        
        # Look for capability patterns
        cap_patterns = [
            r"(?:Can|Able to|Capability:|Feature:)\s*([^.!?\n]+)",
            r"[*-]\s+([^*\n]+(?:create|read|update|delete|execute|analyze)[^*\n]+)"
        ]
        
        for pattern in cap_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:10]:
                cap = match.strip()
                if len(cap) > 10 and len(cap) < 100:
                    capabilities.append(cap)
        
        return capabilities[:8]
    
    def _extract_tool_parameters(self, content: str) -> List[Dict[str, str]]:
        """Extract tool parameters from documentation."""
        parameters = []
        
        # Look for parameter documentation
        import re
        param_section = re.search(
            r"(?:Parameters?|Arguments?|Inputs?):?\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if param_section:
            param_text = param_section.group(1)
            # Extract parameter definitions
            param_pattern = r"[*-]\s*`?(\w+)`?\s*[:-]\s*([^*\n]+)"
            matches = re.findall(param_pattern, param_text)
            
            for name, desc in matches[:10]:
                parameters.append({
                    "name": name.strip(),
                    "description": desc.strip()
                })
        
        return parameters