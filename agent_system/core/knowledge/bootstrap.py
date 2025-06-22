"""
Bootstrap Conversion System for Knowledge Base

Converts existing documentation into structured knowledge entities.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .entity import (
    KnowledgeEntity, KnowledgeContent, KnowledgeRelationships,
    ContextTemplates, IsolationRequirements, KnowledgeMetadata
)
from .storage import KnowledgeStorage

logger = logging.getLogger(__name__)


class DocumentationConverter:
    """Converts documentation files to knowledge entities."""
    
    def __init__(self, docs_dir: str, storage: KnowledgeStorage):
        """Initialize with documentation directory and storage."""
        self.docs_dir = Path(docs_dir)
        self.storage = storage
        self.timestamp = datetime.now().isoformat()
        self.converted_count = 0
        self.failed_conversions = []
    
    def convert_all_documentation(self) -> Dict[str, Any]:
        """Convert all documentation to knowledge entities."""
        logger.info("Starting documentation conversion to knowledge entities...")
        
        # Convert different types of documentation
        self._convert_agent_guides()
        self._convert_architecture_docs()
        self._convert_system_principles()
        self._convert_process_documentation()
        self._convert_tool_documentation()
        
        # Create initial relationships
        self._create_initial_relationships()
        
        # Create system initialization tasks as knowledge
        self._convert_initialization_tasks()
        
        logger.info(f"Documentation conversion complete! Converted {self.converted_count} entities.")
        
        return {
            "converted": self.converted_count,
            "failed": len(self.failed_conversions),
            "failed_files": self.failed_conversions
        }
    
    def _convert_agent_guides(self):
        """Convert agent guide files to agent knowledge entities."""
        logger.info("Converting agent guides...")
        
        # Look for agent guide files in context_documents directory
        agent_guides_dir = self.docs_dir / "context_documents"
        if not agent_guides_dir.exists():
            logger.warning(f"Agent guides directory not found: {agent_guides_dir}")
            return
        
        agent_guides = list(agent_guides_dir.glob("*_agent_guide.md"))
        
        for guide_path in agent_guides:
            try:
                content = guide_path.read_text(encoding='utf-8')
                agent_name = guide_path.stem.replace("_guide", "")
                
                entity = self._create_agent_knowledge_entity(agent_name, content)
                if entity:
                    self.storage.save_entity(entity)
                    self.converted_count += 1
                    logger.info(f"Converted: {agent_name}")
                
            except Exception as e:
                logger.error(f"Error converting {guide_path}: {e}")
                self.failed_conversions.append(str(guide_path))
    
    def _create_agent_knowledge_entity(self, agent_name: str, content: str) -> Optional[KnowledgeEntity]:
        """Create agent knowledge entity from guide content."""
        
        # Extract sections using regex
        sections = self._extract_sections(content)
        
        if not sections.get("purpose"):
            logger.warning(f"Could not extract purpose for {agent_name}")
            return None
        
        # Extract core concepts from approach section
        core_concepts = self._extract_concepts_from_approach(sections.get("approach", ""))
        
        # Extract procedures
        procedures = self._extract_procedures(content)
        
        # Extract examples
        examples = self._extract_examples(content)
        
        # Extract quality criteria from success metrics
        quality_criteria = self._extract_quality_criteria(sections.get("success", ""))
        
        # Extract common pitfalls
        common_pitfalls = self._extract_pitfalls(content)
        
        # Determine domain and frameworks
        domain = self._infer_domain_from_agent_name(agent_name)
        frameworks = self._infer_process_frameworks(agent_name)
        
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
                requires=self._extract_required_knowledge(content),
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
    
    def _convert_architecture_docs(self):
        """Convert architecture documents to system knowledge."""
        logger.info("Converting architecture documents...")
        
        arch_docs = [
            ("entity_architecture.md", "system_entity_architecture", "Entity Framework Architecture"),
            ("process_architecture.md", "system_process_architecture", "Process Architecture"),
            ("event_system_guide.md", "system_event_architecture", "Event System Architecture"),
            ("runtime_specification.md", "system_runtime_architecture", "Runtime Architecture")
        ]
        
        docs_dir = self.docs_dir / "docs"
        
        for doc_name, entity_id, display_name in arch_docs:
            doc_path = docs_dir / doc_name
            
            # Also check with updated_ prefix
            if not doc_path.exists():
                doc_path = docs_dir / f"updated_{doc_name}"
            
            if doc_path.exists():
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    entity = self._create_system_knowledge_entity(
                        entity_id, display_name, content
                    )
                    if entity:
                        self.storage.save_entity(entity)
                        self.converted_count += 1
                        logger.info(f"Converted: {entity_id}")
                except Exception as e:
                    logger.error(f"Error converting {doc_path}: {e}")
                    self.failed_conversions.append(str(doc_path))
    
    def _create_system_knowledge_entity(
        self, 
        entity_id: str, 
        display_name: str, 
        content: str
    ) -> Optional[KnowledgeEntity]:
        """Create system knowledge entity from architecture document."""
        
        sections = self._extract_sections(content)
        
        # Extract overview
        overview = (
            sections.get("overview") or 
            sections.get("concept") or 
            sections.get("purpose") or 
            ""
        )
        
        if not overview:
            logger.warning(f"Could not extract overview for {entity_id}")
            # Try to extract from first paragraph
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    overview = line.strip()
                    break
        
        # Extract core concepts
        core_concepts = self._extract_system_concepts(content, sections)
        
        # Extract procedures if any
        procedures = self._extract_procedures(content)
        
        entity = KnowledgeEntity(
            id=entity_id,
            type="system",
            name=display_name,
            version="1.0.0",
            domain="system_architecture",
            process_frameworks=["system_operation", "architecture_compliance"],
            content=KnowledgeContent(
                summary=overview[:400].strip() + "..." if len(overview) > 400 else overview,
                core_concepts=core_concepts[:12],
                procedures=procedures[:6],
                examples=[],
                quality_criteria=[
                    "System follows architectural principles",
                    "Components integrate correctly",
                    "Performance meets requirements"
                ],
                common_pitfalls=[
                    "Violating architectural constraints",
                    "Ignoring system principles"
                ]
            ),
            relationships=KnowledgeRelationships(
                enables=["all_system_operations"],
                requires=[],
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"System architecture context: {overview[:100]}...",
                agent_context="System operation requires understanding of architectural principles.",
                validation_context="Validate against architectural constraints."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["system_architecture_overview"],
                validation_criteria=[
                    "Understands system structure",
                    "Can work within architectural constraints"
                ]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="architecture_doc_conversion",
                tags=["system", "architecture", "core"],
                priority="critical"
            )
        )
        
        return entity
    
    def _convert_system_principles(self):
        """Convert project principles to foundational system knowledge."""
        logger.info("Converting system principles...")
        
        # Look for project principles
        principles_paths = [
            self.docs_dir / "docs" / "project_principles.md",
            self.docs_dir / "docs" / "updated_project_principles.md",
            self.docs_dir / "project_philosophy.md"
        ]
        
        content = None
        for path in principles_paths:
            if path.exists():
                content = path.read_text(encoding='utf-8')
                break
        
        if not content:
            logger.warning("Project principles document not found")
            return
        
        try:
            # Extract fundamental principles
            principles = self._extract_principles(content)
            
            entity = KnowledgeEntity(
                id="system_core_principles",
                type="system",
                name="Core System Principles",
                version="1.0.0",
                domain="system_architecture",
                process_frameworks=["system_operation", "self_improvement"],
                content=KnowledgeContent(
                    summary="Fundamental principles that guide all system operations and evolution",
                    core_concepts=[p["title"] for p in principles],
                    procedures=[p["description"] for p in principles],
                    examples=[],
                    quality_criteria=[
                        "System follows all core principles",
                        "Principles guide decision making",
                        "No ad-hoc solutions"
                    ],
                    common_pitfalls=[
                        "Ignoring principles for convenience",
                        "Ad-hoc solutions without systematic approach",
                        "Task-first instead of process-first thinking"
                    ]
                ),
                relationships=KnowledgeRelationships(
                    enables=["all_system_operations"],
                    requires=[],
                    related=["system_entity_architecture", "system_process_architecture"]
                ),
                context_templates=ContextTemplates(
                    task_context="All operations must follow core system principles: process-first approach, entity-based architecture, systematic learning.",
                    agent_context="System operation requires adherence to fundamental principles in all decisions and actions.",
                    process_context="Establish systematic frameworks before execution.",
                    validation_context="Validate all operations against core principles."
                ),
                isolation_requirements=IsolationRequirements(
                    minimum_context=["core_principles_complete"],
                    validation_criteria=[
                        "Understands and applies core principles",
                        "Makes principle-guided decisions"
                    ]
                ),
                metadata=KnowledgeMetadata(
                    created_at=self.timestamp,
                    last_updated=self.timestamp,
                    source="principles_conversion",
                    priority="critical",
                    tags=["core", "principles", "foundation"]
                )
            )
            
            self.storage.save_entity(entity)
            self.converted_count += 1
            logger.info("Converted: system_core_principles")
            
        except Exception as e:
            logger.error(f"Error converting principles: {e}")
            self.failed_conversions.append("project_principles")
    
    def _convert_process_documentation(self):
        """Convert process documentation to process knowledge entities."""
        logger.info("Converting process documentation...")
        
        # Define key processes to look for
        processes = [
            ("process_discovery_process", "Process Discovery Framework"),
            ("task_breakdown_process", "Task Breakdown Process"),
            ("quality_evaluation_process", "Quality Evaluation Process"),
            ("optimization_review_process", "Optimization Review Process"),
            ("neutral_task_process", "Neutral Task Process")
        ]
        
        # Look in processes directory
        processes_dir = self.docs_dir / "processes"
        if not processes_dir.exists():
            processes_dir = self.docs_dir / "core" / "processes"
        
        for process_id, display_name in processes:
            # Try to find the process file
            process_file = processes_dir / f"{process_id}.py"
            
            if process_file.exists():
                try:
                    content = process_file.read_text(encoding='utf-8')
                    entity = self._create_process_knowledge_from_code(
                        process_id, display_name, content
                    )
                    if entity:
                        self.storage.save_entity(entity)
                        self.converted_count += 1
                        logger.info(f"Converted: {process_id}")
                except Exception as e:
                    logger.error(f"Error converting {process_file}: {e}")
                    self.failed_conversions.append(str(process_file))
    
    def _create_process_knowledge_from_code(
        self,
        process_id: str,
        display_name: str,
        code_content: str
    ) -> Optional[KnowledgeEntity]:
        """Create process knowledge entity from process code."""
        
        # Extract docstring
        docstring_match = re.search(r'"""(.*?)"""', code_content, re.DOTALL)
        summary = ""
        if docstring_match:
            summary = docstring_match.group(1).strip().split('\n')[0]
        
        # Extract phases/steps from code
        phases = re.findall(r'# Phase \d+: (.+)', code_content)
        steps = re.findall(r'# Step \d+: (.+)', code_content)
        procedures = phases + steps
        
        # Determine domain
        domain = "system_operation"
        if "task" in process_id:
            domain = "task_management"
        elif "quality" in process_id:
            domain = "quality_assurance"
        elif "optimization" in process_id:
            domain = "optimization"
        
        entity = KnowledgeEntity(
            id=f"process_{process_id}",
            type="process",
            name=display_name,
            version="1.0.0",
            domain=domain,
            process_frameworks=[process_id],
            content=KnowledgeContent(
                summary=summary or f"Process framework for {display_name}",
                core_concepts=[
                    "Systematic framework establishment",
                    "Process compliance validation",
                    "Isolated task success"
                ],
                procedures=procedures[:8],
                examples=[],
                quality_criteria=[
                    "Process executes successfully",
                    "All steps complete correctly",
                    "Output meets requirements"
                ],
                common_pitfalls=[
                    "Skipping process steps",
                    "Inadequate validation"
                ]
            ),
            relationships=KnowledgeRelationships(),
            context_templates=ContextTemplates(
                task_context=f"Execute {display_name} following established procedures.",
                agent_context=f"Process execution requires systematic approach.",
                process_context=f"Follow {process_id} framework for execution."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[f"{process_id}_framework"],
                validation_criteria=["Can execute process steps independently"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="process_code_conversion",
                tags=[process_id, domain, "process"]
            )
        )
        
        return entity
    
    def _convert_tool_documentation(self):
        """Convert tool documentation to tool knowledge entities."""
        logger.info("Converting tool documentation...")
        
        # Look for tool documentation
        tool_docs = [
            ("mvp_tooling_guide.md", "tooling_system", "MVP Tooling System"),
            ("internal_tools_documentation.md", "internal_tools", "Internal Tools"),
            ("mcp_integration_guide.md", "mcp_tools", "MCP Tool Integration")
        ]
        
        docs_dir = self.docs_dir / "docs"
        
        for doc_name, base_id, display_name in tool_docs:
            doc_path = docs_dir / doc_name
            
            if doc_path.exists():
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    entity = self._create_tool_knowledge_entity(
                        base_id, display_name, content
                    )
                    if entity:
                        self.storage.save_entity(entity)
                        self.converted_count += 1
                        logger.info(f"Converted: tool_{base_id}")
                except Exception as e:
                    logger.error(f"Error converting {doc_path}: {e}")
                    self.failed_conversions.append(str(doc_path))
    
    def _create_tool_knowledge_entity(
        self,
        entity_id: str,
        display_name: str,
        content: str
    ) -> Optional[KnowledgeEntity]:
        """Create tool knowledge entity from documentation."""
        
        sections = self._extract_sections(content)
        overview = sections.get("overview", "Tool system for agent capabilities")
        
        # Extract tool categories and procedures
        tool_sections = re.findall(r'### (.+?)\n(.+?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        procedures = [section[0].strip() for section in tool_sections[:8]]
        
        entity = KnowledgeEntity(
            id=f"tool_{entity_id}",
            type="tool",
            name=display_name,
            version="1.0.0",
            domain="system_operation",
            process_frameworks=["tool_management", "capability_provision"],
            content=KnowledgeContent(
                summary=overview[:300] + "..." if len(overview) > 300 else overview,
                core_concepts=[
                    "Tool-based capability provision",
                    "Permission-based access",
                    "Usage tracking"
                ],
                procedures=procedures,
                examples=[],
                quality_criteria=[
                    "Tools work reliably",
                    "Permissions enforced correctly",
                    "Usage tracked accurately"
                ],
                common_pitfalls=[
                    "Permission bypass",
                    "Tool misuse",
                    "Performance issues"
                ]
            ),
            relationships=KnowledgeRelationships(),
            context_templates=ContextTemplates(
                task_context="When using tools: Ensure proper permissions, follow usage guidelines.",
                agent_context="Tool usage requires understanding of capabilities and permissions."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["tool_capabilities_reference"],
                validation_criteria=["Can use tools correctly"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="tool_documentation_conversion",
                tags=["tools", "capabilities", "system"]
            )
        )
        
        return entity
    
    def _convert_initialization_tasks(self):
        """Convert system initialization tasks to knowledge entities."""
        logger.info("Converting initialization tasks...")
        
        # Create domain knowledge for system initialization
        entity = KnowledgeEntity(
            id="domain_system_initialization",
            type="domain",
            name="System Initialization Domain",
            version="1.0.0",
            domain="system_initialization",
            process_frameworks=["initialization_sequence", "validation_process"],
            content=KnowledgeContent(
                summary="Knowledge domain for system initialization and bootstrap validation",
                core_concepts=[
                    "Bootstrap validation phases",
                    "Framework establishment sequence",
                    "Capability validation procedures",
                    "Self-improvement setup"
                ],
                procedures=[
                    "Phase 1: Bootstrap validation (Tasks 1-3)",
                    "Phase 2: Framework establishment (Tasks 4-8)",
                    "Phase 3: Capability validation (Tasks 9-12)",
                    "Phase 4: Self-improvement setup (Tasks 13-15)"
                ],
                examples=[
                    "Knowledge base validation",
                    "Context assembly testing",
                    "Entity framework validation",
                    "End-to-end system test"
                ],
                quality_criteria=[
                    "All initialization phases complete successfully",
                    "System frameworks operational",
                    "Knowledge base comprehensive",
                    "Self-improvement mechanisms active"
                ],
                common_pitfalls=[
                    "Skipping validation steps",
                    "Incomplete framework establishment",
                    "Missing critical knowledge",
                    "Inadequate error handling"
                ]
            ),
            relationships=KnowledgeRelationships(
                enables=["system_autonomous_operation"],
                requires=["system_core_principles", "system_entity_architecture"]
            ),
            context_templates=ContextTemplates(
                task_context="System initialization requires systematic validation and framework establishment.",
                agent_context="Follow initialization sequence for systematic startup."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["initialization_sequence", "validation_criteria"],
                validation_criteria=["Can execute initialization autonomously"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="initialization_tasks_conversion",
                tags=["initialization", "bootstrap", "system"],
                priority="critical"
            )
        )
        
        self.storage.save_entity(entity)
        self.converted_count += 1
        logger.info("Converted: domain_system_initialization")
    
    def _create_initial_relationships(self):
        """Create initial relationships between knowledge entities."""
        logger.info("Creating initial knowledge relationships...")
        
        # Agent to domain mappings
        agent_domain_mappings = {
            "agent_knowledge_agent_selector": ["task_routing", "agent_capabilities"],
            "agent_knowledge_planning_agent": ["task_decomposition", "workflow_design"],
            "agent_knowledge_context_addition": ["knowledge_management"],
            "agent_knowledge_tool_addition": ["system_operation"],
            "agent_knowledge_task_evaluator": ["quality_assurance"],
            "agent_knowledge_documentation_agent": ["knowledge_management"],
            "agent_knowledge_review_agent": ["optimization"],
            "agent_knowledge_process_discovery": ["system_initialization"]
        }
        
        # Create relationships
        for agent_id, domains in agent_domain_mappings.items():
            agent_entity = self.storage.load_entity(agent_id)
            if agent_entity:
                # Add enables relationships
                for domain in domains:
                    domain_id = f"domain_{domain}"
                    if not self.storage.load_entity(domain_id):
                        # Create basic domain entity if it doesn't exist
                        self._create_basic_domain_entity(domain)
                    
                    agent_entity.add_relationship("enables", domain_id)
                
                # Add requires relationships to system principles
                agent_entity.add_relationship("requires", "system_core_principles")
                
                self.storage.save_entity(agent_entity)
        
        # System knowledge relationships
        system_entities = [
            "system_entity_architecture",
            "system_process_architecture",
            "system_event_architecture",
            "system_runtime_architecture"
        ]
        
        for entity_id in system_entities:
            entity = self.storage.load_entity(entity_id)
            if entity:
                entity.add_relationship("requires", "system_core_principles")
                entity.add_relationship("enables", "system_operation")
                self.storage.save_entity(entity)
    
    def _create_basic_domain_entity(self, domain: str):
        """Create a basic domain entity if it doesn't exist."""
        entity = KnowledgeEntity(
            id=f"domain_{domain}",
            type="domain",
            name=f"{domain.replace('_', ' ').title()} Domain",
            version="1.0.0",
            domain=domain,
            process_frameworks=[],
            content=KnowledgeContent(
                summary=f"Knowledge domain for {domain.replace('_', ' ')}",
                core_concepts=[],
                procedures=[],
                examples=[],
                quality_criteria=[],
                common_pitfalls=[]
            ),
            relationships=KnowledgeRelationships(),
            context_templates=ContextTemplates(
                task_context=f"Operating in {domain} domain.",
                agent_context=f"Domain knowledge for {domain}."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[],
                validation_criteria=[]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="auto_generated",
                tags=[domain, "domain"]
            )
        )
        
        self.storage.save_entity(entity)
        self.converted_count += 1
    
    # Helper methods for extraction
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract major sections from markdown content."""
        sections = {}
        
        # Common section patterns
        patterns = [
            (r'## Core Purpose\n(.+?)(?=\n##|\n#|\Z)', 'purpose'),
            (r'## Fundamental Approach\n(.+?)(?=\n##|\n#|\Z)', 'approach'),
            (r'## Success Metrics\n(.+?)(?=\n##|\n#|\Z)', 'success'),
            (r'## Overview\n(.+?)(?=\n##|\n#|\Z)', 'overview'),
            (r'## Core Concept\n(.+?)(?=\n##|\n#|\Z)', 'concept'),
            (r'## Purpose\n(.+?)(?=\n##|\n#|\Z)', 'purpose'),
            (r'## Architecture\n(.+?)(?=\n##|\n#|\Z)', 'architecture'),
            (r'## Principles\n(.+?)(?=\n##|\n#|\Z)', 'principles'),
            (r'## Key(.+?)(?=\n##|\n#|\Z)', 'key'),
            (r'## Core(.+?)(?=\n##|\n#|\Z)', 'core'),
            (r'## Fundamental(.+?)(?=\n##|\n#|\Z)', 'fundamental')
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[key] = match.group(1).strip()
        
        return sections
    
    def _extract_concepts_from_approach(self, approach_text: str) -> List[str]:
        """Extract core concepts from approach section."""
        concepts = []
        
        # Extract bullet points
        bullet_points = re.findall(r'^- (.+)$', approach_text, re.MULTILINE)
        concepts.extend(bullet_points)
        
        # Extract ### subsections
        subsections = re.findall(r'^### (.+)$', approach_text, re.MULTILINE)
        concepts.extend(subsections)
        
        # Extract "Think in X" patterns
        think_patterns = re.findall(r'Think in (.+?)[,\.]', approach_text, re.IGNORECASE)
        for pattern in think_patterns:
            concepts.append(f"Think in {pattern}")
        
        return concepts
    
    def _extract_procedures(self, content: str) -> List[str]:
        """Extract procedures from content."""
        procedures = []
        
        # Look for phases
        phases = re.findall(r'(?:Phase|Step) \d+: (.+)', content)
        procedures.extend(phases)
        
        # Look for numbered lists
        numbered = re.findall(r'^\d+\. (.+)$', content, re.MULTILINE)
        procedures.extend(numbered[:5])  # Limit to avoid too many
        
        # Look for workflow sections
        workflows = re.findall(r'### (?:Workflow|Process|Procedure)[:\s]*(.+)', content)
        procedures.extend(workflows)
        
        return procedures
    
    def _extract_examples(self, content: str) -> List[str]:
        """Extract examples from content."""
        examples = []
        
        # Look for example sections
        example_sections = re.findall(
            r'(?:Example|e\.g\.|For example)[:\s]*(.+?)(?=\n|$)', 
            content, 
            re.IGNORECASE
        )
        examples.extend([ex.strip() for ex in example_sections[:5]])
        
        # Look for code blocks that might be examples
        code_blocks = re.findall(r'```[^`]*```', content)
        if code_blocks:
            examples.append("Code examples available")
        
        return examples
    
    def _extract_quality_criteria(self, success_text: str) -> List[str]:
        """Extract quality criteria from success metrics."""
        criteria = []
        
        # Extract bullet points
        bullets = re.findall(r'^- (.+)$', success_text, re.MULTILINE)
        criteria.extend(bullets)
        
        # Look for "when" patterns
        when_patterns = re.findall(r'when (.+?)(?:\n|$)', success_text, re.IGNORECASE)
        criteria.extend(when_patterns)
        
        # Look for success indicators
        if "success" in success_text.lower():
            success_lines = [
                line.strip() for line in success_text.split('\n')
                if line.strip() and 'success' in line.lower()
            ]
            criteria.extend(success_lines[:3])
        
        return criteria
    
    def _extract_pitfalls(self, content: str) -> List[str]:
        """Extract common pitfalls from content."""
        pitfalls = []
        
        # Look for pitfall sections
        pitfall_section = re.search(
            r'(?:Common Pitfalls|Things to Avoid|Don\'t|Avoid)(.+?)(?=\n##|\n#|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if pitfall_section:
            text = pitfall_section.group(1)
            bullets = re.findall(r'^- (.+)$', text, re.MULTILINE)
            pitfalls.extend(bullets)
        
        # Look for "don't" or "avoid" patterns
        dont_patterns = re.findall(
            r'(?:Don\'t|Avoid|Never) (.+?)(?:\.|$)',
            content,
            re.IGNORECASE
        )
        pitfalls.extend(dont_patterns[:3])
        
        return pitfalls
    
    def _extract_required_knowledge(self, content: str) -> List[str]:
        """Extract required knowledge from content."""
        required = []
        
        # Look for context document mentions
        context_docs = re.findall(r'context.*?:\s*\[([^\]]+)\]', content, re.IGNORECASE)
        for doc_list in context_docs:
            docs = [d.strip().strip('"\'') for d in doc_list.split(',')]
            required.extend(docs)
        
        # Look for tool mentions
        tools = re.findall(r'(?:tool|using)\s+`([^`]+)`', content, re.IGNORECASE)
        required.extend([f"tool_{t}" for t in tools[:3]])
        
        return list(set(required))  # Remove duplicates
    
    def _extract_system_concepts(self, content: str, sections: Dict[str, str]) -> List[str]:
        """Extract core concepts from system documentation."""
        concepts = []
        
        # Check principles section
        if sections.get("principles"):
            bullets = re.findall(r'^- (.+)$', sections["principles"], re.MULTILINE)
            concepts.extend(bullets)
        
        # Look for key concepts
        if sections.get("key") or sections.get("core"):
            text = sections.get("key") or sections.get("core")
            bullets = re.findall(r'^- (.+)$', text, re.MULTILINE)
            concepts.extend(bullets)
        
        # Look for ### sections that might be concepts
        subsections = re.findall(r'^### (.+)$', content, re.MULTILINE)
        for subsection in subsections[:8]:
            if len(subsection) < 50:  # Avoid long descriptions
                concepts.append(subsection)
        
        return concepts
    
    def _extract_principles(self, content: str) -> List[Dict[str, str]]:
        """Extract principles from project principles document."""
        principles = []
        
        # Look for fundamental principles section
        principles_section = re.search(
            r'## Fundamental Principles(.+?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        
        if principles_section:
            text = principles_section.group(1)
            
            # Extract principle patterns: ### Title \n Description
            principle_matches = re.findall(
                r'### (.+?)\n(.+?)(?=\n###|\n##|\Z)',
                text,
                re.DOTALL
            )
            
            for title, description in principle_matches:
                # Clean up description - get first paragraph or bullet points
                desc_lines = description.strip().split('\n')
                clean_desc = []
                
                for line in desc_lines:
                    if line.strip():
                        if line.startswith('-') or line.startswith('*'):
                            clean_desc.append(line.strip())
                        else:
                            clean_desc.append(line.strip())
                            break  # Just first paragraph
                
                principles.append({
                    "title": title.strip(),
                    "description": ' '.join(clean_desc)[:200]
                })
        
        return principles
    
    def _infer_domain_from_agent_name(self, agent_name: str) -> str:
        """Infer domain from agent name."""
        domain_mapping = {
            "agent_selector": "task_routing",
            "planning_agent": "task_decomposition",
            "context_addition": "knowledge_management",
            "tool_addition": "capability_management",
            "task_evaluator": "quality_assurance",
            "summary_agent": "communication",
            "documentation_agent": "knowledge_management",
            "review_agent": "system_improvement",
            "process_discovery": "system_initialization",
            "feedback_agent": "coordination",
            "investigator_agent": "analysis",
            "optimizer_agent": "optimization",
            "recovery_agent": "system_resilience"
        }
        return domain_mapping.get(agent_name, "general")
    
    def _infer_process_frameworks(self, agent_name: str) -> List[str]:
        """Infer relevant process frameworks for agent."""
        framework_mapping = {
            "agent_selector": ["task_routing", "agent_assignment"],
            "planning_agent": ["task_breakdown", "workflow_design"],
            "context_addition": ["knowledge_provision", "context_assembly"],
            "tool_addition": ["capability_discovery", "tool_assignment"],
            "task_evaluator": ["quality_evaluation", "performance_assessment"],
            "summary_agent": ["information_synthesis", "communication"],
            "documentation_agent": ["knowledge_capture", "documentation_creation"],
            "review_agent": ["system_analysis", "improvement_planning"],
            "process_discovery": ["framework_establishment", "domain_analysis"],
            "feedback_agent": ["coordination", "communication"],
            "investigator_agent": ["analysis", "research"],
            "optimizer_agent": ["performance_optimization", "system_improvement"],
            "recovery_agent": ["error_recovery", "system_resilience"]
        }
        return framework_mapping.get(agent_name, ["general"])


def bootstrap_knowledge_system(docs_dir: str = ".", knowledge_dir: str = "knowledge"):
    """Main function to bootstrap the knowledge system."""
    # Initialize storage
    storage = KnowledgeStorage(knowledge_dir)
    
    # Initialize converter
    converter = DocumentationConverter(docs_dir, storage)
    
    # Run conversion
    results = converter.convert_all_documentation()
    
    logger.info("\nKnowledge bootstrap complete!")
    logger.info(f"Created knowledge entities in: {storage.knowledge_dir}")
    
    # Validate the conversion
    stats = storage.get_statistics()
    logger.info(f"Total knowledge entities created: {stats['total_entities']}")
    logger.info(f"Entities by type: {stats['entities_by_type']}")
    
    # Check for relationship issues
    missing_rels = storage.validate_relationships()
    if missing_rels:
        logger.warning(f"Found {len(missing_rels)} entities with missing relationships")
    
    return results