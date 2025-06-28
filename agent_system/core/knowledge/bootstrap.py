"""
Bootstrap Conversion System for Knowledge Base

Converts existing documentation into structured knowledge entities.
This is the refactored version using modular converters.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .storage import KnowledgeStorage
from .converters import (
    DocumentationParser,
    EntityConverter,
    RelationshipBuilder,
    ExtractionUtils
)

logger = logging.getLogger(__name__)


class DocumentationConverter:
    """Orchestrates documentation conversion to knowledge entities."""
    
    def __init__(self, docs_dir: str, storage: KnowledgeStorage):
        """Initialize with documentation directory and storage."""
        self.docs_dir = Path(docs_dir)
        self.storage = storage
        self.timestamp = datetime.now().isoformat()
        
        # Initialize modular components
        self.parser = DocumentationParser(self.docs_dir)
        self.converter = EntityConverter(self.timestamp)
        self.relationship_builder = RelationshipBuilder()
        
        # Tracking
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
        
        # Build all relationships
        relationship_count = self.relationship_builder.build_all_relationships()
        
        logger.info(f"Documentation conversion complete! Converted {self.converted_count} entities.")
        logger.info(f"Created {relationship_count} entity relationships.")
        
        return {
            "converted": self.converted_count,
            "failed": len(self.failed_conversions),
            "failed_files": self.failed_conversions,
            "relationships": relationship_count
        }
    
    def _convert_agent_guides(self):
        """Convert agent guide files to agent knowledge entities."""
        logger.info("Converting agent guides...")
        
        agent_guides = self.parser.find_agent_guides()
        
        for guide_path in agent_guides:
            try:
                content = self.parser.read_file_safely(guide_path)
                if not content:
                    continue
                
                agent_name = self.parser.extract_agent_name_from_guide(guide_path)
                
                entity = self.converter.create_agent_entity(agent_name, content)
                if entity:
                    self.storage.save_entity(entity)
                    self.relationship_builder.add_entity(entity)
                    self.converted_count += 1
                    logger.info(f"Converted: {agent_name}")
                
            except Exception as e:
                logger.error(f"Error converting {guide_path}: {e}")
                self.failed_conversions.append(str(guide_path))
    
    def _convert_architecture_docs(self):
        """Convert architecture documents to system knowledge."""
        logger.info("Converting architecture documents...")
        
        arch_docs = self.parser.find_architecture_docs()
        
        for doc_name, entity_id, display_name in arch_docs:
            doc_path = self.parser.find_or_create_architecture_doc(doc_name)
            
            if doc_path:
                try:
                    content = self.parser.read_file_safely(doc_path)
                    if not content:
                        continue
                    
                    entity = self.converter.create_system_entity(
                        entity_id, display_name, content
                    )
                    if entity:
                        self.storage.save_entity(entity)
                        self.relationship_builder.add_entity(entity)
                        self.converted_count += 1
                        logger.info(f"Converted: {entity_id}")
                        
                except Exception as e:
                    logger.error(f"Error converting {doc_path}: {e}")
                    self.failed_conversions.append(str(doc_path))
    
    def _convert_system_principles(self):
        """Convert system principles documentation."""
        logger.info("Converting system principles...")
        
        # Look for principles documentation
        principle_files = [
            "context_documents/system_core_principles.md",
            "docs/process_first_architecture.md",
            "docs/updated_system_principles.md"
        ]
        
        for principle_file in principle_files:
            principle_path = self.docs_dir / principle_file
            if principle_path.exists():
                try:
                    content = self.parser.read_file_safely(principle_path)
                    if not content:
                        continue
                    
                    entity = self.converter.create_system_entity(
                        "system_core_principles",
                        "System Core Principles",
                        content
                    )
                    
                    if entity:
                        # Override type to pattern for principles
                        entity.type = "pattern"
                        self.storage.save_entity(entity)
                        self.relationship_builder.add_entity(entity)
                        self.converted_count += 1
                        logger.info("Converted: system_core_principles")
                        break
                        
                except Exception as e:
                    logger.error(f"Error converting {principle_path}: {e}")
                    self.failed_conversions.append(str(principle_path))
    
    def _convert_process_documentation(self):
        """Convert process documentation from code and docs."""
        logger.info("Converting process documentation...")
        
        process_files = self.parser.find_process_files()
        
        for process_file in process_files:
            try:
                content = self.parser.read_file_safely(process_file)
                if not content:
                    continue
                
                process_name = self.parser.extract_process_name_from_file(process_file)
                entity = self._create_process_knowledge_from_code(
                    process_name, content
                )
                
                if entity:
                    self.storage.save_entity(entity)
                    self.relationship_builder.add_entity(entity)
                    self.converted_count += 1
                    logger.info(f"Converted: {process_name}")
                    
            except Exception as e:
                logger.error(f"Error converting {process_file}: {e}")
                self.failed_conversions.append(str(process_file))
    
    def _create_process_knowledge_from_code(
        self,
        process_name: str,
        code_content: str
    ) -> Optional[KnowledgeEntity]:
        """Create process knowledge from Python code."""
        # Extract docstring
        docstring_match = re.search(r'"""(.*?)"""', code_content, re.DOTALL)
        docstring = docstring_match.group(1).strip() if docstring_match else ""
        
        # Extract process steps from method names
        method_pattern = r"async def (\w+)\(self.*?\):"
        methods = re.findall(method_pattern, code_content)
        
        # Filter and format process steps
        steps = []
        for method in methods:
            if not method.startswith("_") and method not in ["__init__", "__str__"]:
                step = method.replace("_", " ").title()
                steps.append(f"{step} in {process_name} process")
        
        # Determine domain
        domain = "process_implementation"
        if "discovery" in process_name:
            domain = "process_discovery"
        elif "evaluation" in process_name:
            domain = "task_evaluation"
        elif "planning" in process_name:
            domain = "task_planning"
        
        return self.converter.create_process_entity(
            process_name, domain, steps[:10], docstring
        )
    
    def _convert_tool_documentation(self):
        """Convert tool documentation to knowledge entities."""
        logger.info("Converting tool documentation...")
        
        tool_docs = self.parser.find_tool_docs()
        
        for tool_doc_path in tool_docs:
            try:
                content = self.parser.read_file_safely(tool_doc_path)
                if not content:
                    continue
                
                # Extract tool name from path
                tool_name = tool_doc_path.stem.replace("_tools", "")
                category = self.parser.extract_tool_category_from_path(tool_doc_path)
                
                entity = self.converter.create_tool_entity(
                    tool_name, category, content
                )
                
                if entity:
                    self.storage.save_entity(entity)
                    self.relationship_builder.add_entity(entity)
                    self.converted_count += 1
                    logger.info(f"Converted: {tool_name} ({category})")
                    
            except Exception as e:
                logger.error(f"Error converting {tool_doc_path}: {e}")
                self.failed_conversions.append(str(tool_doc_path))
    
    def _convert_initialization_tasks(self):
        """Convert system initialization tasks to knowledge entities."""
        logger.info("Converting initialization tasks...")
        
        # Create domain knowledge for system initialization
        domain_entity = self.converter.create_domain_entity("system_initialization")
        
        # Override with specific initialization content
        domain_entity.content.summary = "Knowledge domain for system initialization and bootstrap validation"
        domain_entity.content.core_concepts = [
            "Bootstrap validation phases",
            "Framework establishment sequence",
            "Capability validation procedures",
            "Self-improvement setup"
        ]
        domain_entity.content.procedures = [
            "Phase 1: Bootstrap validation (Tasks 1-3)",
            "Phase 2: Framework establishment (Tasks 4-8)",
            "Phase 3: Capability validation (Tasks 9-12)",
            "Phase 4: Self-improvement setup (Tasks 13-15)"
        ]
        domain_entity.content.examples = [
            "Knowledge base validation",
            "Context assembly testing",
            "Entity framework validation",
            "End-to-end system test"
        ]
        domain_entity.content.quality_criteria = [
            "All initialization phases complete successfully",
            "System frameworks operational",
            "Knowledge base comprehensive",
            "Self-improvement mechanisms active"
        ]
        domain_entity.content.common_pitfalls = [
            "Skipping validation steps",
            "Incomplete framework establishment",
            "Missing critical knowledge",
            "Inadequate error handling"
        ]
        
        self.storage.save_entity(domain_entity)
        self.relationship_builder.add_entity(domain_entity)
        self.converted_count += 1
        logger.info("Converted: domain_system_initialization")
        
        # Create individual task entities
        init_tasks = [
            ("Knowledge Base Validation", "1", [], ["knowledge_base_operational"]),
            ("Context Assembly Test", "2", ["knowledge_base_operational"], ["context_assembly_validated"]),
            ("Gap Detection Validation", "3", ["context_assembly_validated"], ["gap_detection_operational"]),
            ("Process Framework Test", "4", ["gap_detection_operational"], ["process_frameworks_validated"]),
            ("Agent Specialization Test", "5", ["process_frameworks_validated"], ["agents_specialized"]),
            ("Tool Integration Test", "6", ["agents_specialized"], ["tools_integrated"]),
            ("Event System Test", "7", ["tools_integrated"], ["events_tracked"]),
            ("Self-Improvement Test", "8", ["events_tracked"], ["self_improvement_active"])
        ]
        
        for task_name, task_id, deps, outcomes in init_tasks:
            entity = self.converter.create_initialization_task_entity(
                task_name, task_id, deps, outcomes
            )
            self.storage.save_entity(entity)
            self.relationship_builder.add_entity(entity)
            self.converted_count += 1
            logger.info(f"Converted: init_task_{task_id}")
    
    def _create_initial_relationships(self):
        """Create initial domain entities that other entities depend on."""
        logger.info("Creating initial knowledge relationships...")
        
        # Create basic domain entities
        domains = [
            "process_framework_establishment",
            "task_routing_orchestration", 
            "task_decomposition",
            "knowledge_management",
            "capability_expansion",
            "quality_assessment",
            "information_synthesis",
            "continuous_improvement"
        ]
        
        for domain in domains:
            if not self.storage.get_entity(f"domain_{domain}"):
                entity = self.converter.create_domain_entity(domain)
                self.storage.save_entity(entity)
                self.relationship_builder.add_entity(entity)
                self.converted_count += 1
                logger.info(f"Created domain: {domain}")


def bootstrap_knowledge_system(docs_dir: str = ".", knowledge_dir: str = "knowledge"):
    """Bootstrap the knowledge system from existing documentation.
    
    Args:
        docs_dir: Root directory containing documentation
        knowledge_dir: Directory to store knowledge entities
        
    Returns:
        Conversion statistics
    """
    # Initialize storage
    storage = KnowledgeStorage(knowledge_dir)
    
    # Convert documentation
    converter = DocumentationConverter(docs_dir, storage)
    stats = converter.convert_all_documentation()
    
    # Validate relationships
    warnings = converter.relationship_builder.validate_relationships()
    if warnings:
        logger.warning(f"Relationship validation warnings: {len(warnings)}")
        for warning in warnings[:10]:
            logger.warning(f"  - {warning}")
    
    # Save relationship graph
    graph_path = Path(knowledge_dir) / "relationship_graph.json"
    graph = converter.relationship_builder.get_entity_graph()
    with open(graph_path, 'w') as f:
        json.dump(graph, f, indent=2)
    
    logger.info(f"Knowledge bootstrap complete: {stats['converted']} entities created")
    logger.info(f"Relationship graph saved to: {graph_path}")
    
    return stats


if __name__ == "__main__":
    import sys
    
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    knowledge_dir = sys.argv[2] if len(sys.argv) > 2 else "knowledge"
    
    stats = bootstrap_knowledge_system(docs_dir, knowledge_dir)
    print(f"\nBootstrap complete: {stats['converted']} entities created")