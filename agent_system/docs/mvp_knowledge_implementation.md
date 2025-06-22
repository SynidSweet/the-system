# MVP Knowledge System Implementation Guide

## Implementation Overview

This guide provides step-by-step instructions for implementing the MVP knowledge system, including code structure, database integration, and the bootstrap process for converting existing documentation.

## Project Structure

### New Directories and Files to Create
```
project_root/
├── knowledge/                          # Knowledge storage directory
│   ├── domains/                        # Domain knowledge entities
│   ├── processes/                      # Process framework knowledge
│   ├── agents/                         # Agent specialization knowledge
│   ├── tools/                          # Tool capability knowledge
│   ├── patterns/                       # Successful execution patterns
│   ├── system/                         # System architecture knowledge
│   └── templates/                      # Context assembly templates
├── src/knowledge/                      # Knowledge system implementation
│   ├── __init__.py
│   ├── entity.py                       # Knowledge entity classes
│   ├── engine.py                       # Context assembly engine
│   ├── storage.py                      # File-based storage manager
│   ├── validator.py                    # Context validation system
│   └── bootstrap.py                    # Documentation conversion system
├── scripts/
│   ├── bootstrap_knowledge.py          # Convert documentation script
│   ├── initialize_system.py            # Run initialization tasks
│   └── validate_knowledge.py           # Knowledge validation script
└── tests/knowledge/                    # Knowledge system tests
    ├── test_entity.py
    ├── test_engine.py
    └── test_bootstrap.py
```

## Core Implementation Components

### 1. Knowledge Entity Classes (`src/knowledge/entity.py`)

```python
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

@dataclass
class KnowledgeContent:
    summary: str
    core_concepts: List[str]
    procedures: List[str]
    examples: List[str]
    quality_criteria: List[str]
    common_pitfalls: List[str]

@dataclass
class KnowledgeRelationships:
    enables: List[str] = None
    requires: List[str] = None
    related: List[str] = None
    enhances: List[str] = None
    specializes: List[str] = None
    generalizes: List[str] = None
    
    def __post_init__(self):
        # Initialize empty lists if None
        for field in ['enables', 'requires', 'related', 'enhances', 'specializes', 'generalizes']:
            if getattr(self, field) is None:
                setattr(self, field, [])

@dataclass
class ContextTemplates:
    task_context: str
    agent_context: str
    process_context: Optional[str] = None
    validation_context: Optional[str] = None
    learning_context: Optional[str] = None

@dataclass
class IsolationRequirements:
    minimum_context: List[str]
    validation_criteria: List[str]

@dataclass
class KnowledgeMetadata:
    created_at: str
    last_updated: str
    usage_count: int = 0
    effectiveness_score: float = 0.0
    source: str = "manual_creation"
    tags: List[str] = None
    priority: str = "medium"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class KnowledgeEntity:
    def __init__(self, id: str, type: str, name: str, version: str, domain: str,
                 process_frameworks: List[str], content: KnowledgeContent,
                 relationships: KnowledgeRelationships, context_templates: ContextTemplates,
                 isolation_requirements: IsolationRequirements, metadata: KnowledgeMetadata):
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
        """Convert to dictionary for JSON serialization"""
        return {
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntity':
        """Create from dictionary loaded from JSON"""
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
        """Update usage tracking"""
        self.metadata.usage_count += 1
        self.metadata.last_updated = datetime.now().isoformat()
    
    def update_effectiveness(self, score: float):
        """Update effectiveness score (0.0-1.0)"""
        # Moving average: new_score = 0.8 * old_score + 0.2 * new_measurement
        self.metadata.effectiveness_score = 0.8 * self.metadata.effectiveness_score + 0.2 * score
        self.metadata.last_updated = datetime.now().isoformat()
```

### 2. Storage Manager (`src/knowledge/storage.py`)

```python
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Iterator
from .entity import KnowledgeEntity

class KnowledgeStorage:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create knowledge directory structure if it doesn't exist"""
        subdirs = ["domains", "processes", "agents", "tools", "patterns", "system", "templates"]
        for subdir in subdirs:
            (self.knowledge_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def save_entity(self, entity: KnowledgeEntity) -> bool:
        """Save knowledge entity to appropriate subdirectory"""
        try:
            subdir = self._get_subdir_for_type(entity.type)
            file_path = self.knowledge_dir / subdir / f"{entity.id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entity.to_dict(), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving entity {entity.id}: {e}")
            return False
    
    def load_entity(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """Load knowledge entity by ID"""
        # Search all subdirectories for the entity
        for subdir in ["domains", "processes", "agents", "tools", "patterns", "system"]:
            file_path = self.knowledge_dir / subdir / f"{entity_id}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return KnowledgeEntity.from_dict(data)
                except Exception as e:
                    print(f"Error loading entity {entity_id}: {e}")
                    return None
        return None
    
    def list_entities_by_type(self, entity_type: str) -> List[str]:
        """List all entity IDs of a specific type"""
        subdir = self._get_subdir_for_type(entity_type)
        type_dir = self.knowledge_dir / subdir
        
        if not type_dir.exists():
            return []
        
        return [f.stem for f in type_dir.glob("*.json")]
    
    def list_all_entities(self) -> Iterator[KnowledgeEntity]:
        """Iterate through all knowledge entities"""
        for subdir in ["domains", "processes", "agents", "tools", "patterns", "system"]:
            type_dir = self.knowledge_dir / subdir
            if type_dir.exists():
                for file_path in type_dir.glob("*.json"):
                    entity = self.load_entity(file_path.stem)
                    if entity:
                        yield entity
    
    def search_entities(self, query: str, entity_type: Optional[str] = None) -> List[KnowledgeEntity]:
        """Search entities by content"""
        results = []
        
        for entity in self.list_all_entities():
            if entity_type and entity.type != entity_type:
                continue
                
            # Search in name, summary, and concepts
            searchable_text = " ".join([
                entity.name.lower(),
                entity.content.summary.lower(),
                " ".join(entity.content.core_concepts).lower()
            ])
            
            if query.lower() in searchable_text:
                results.append(entity)
        
        return results
    
    def get_entities_by_domain(self, domain: str) -> List[KnowledgeEntity]:
        """Get all entities for a specific domain"""
        return [entity for entity in self.list_all_entities() if entity.domain == domain]
    
    def get_entities_by_process_framework(self, framework: str) -> List[KnowledgeEntity]:
        """Get all entities that apply to a specific process framework"""
        return [entity for entity in self.list_all_entities() 
                if framework in entity.process_frameworks]
    
    def _get_subdir_for_type(self, entity_type: str) -> str:
        """Map entity type to storage subdirectory"""
        type_mapping = {
            "domain": "domains",
            "process": "processes", 
            "agent": "agents",
            "tool": "tools",
            "pattern": "patterns",
            "system": "system"
        }
        return type_mapping.get(entity_type, "system")
```

### 3. Context Assembly Engine (`src/knowledge/engine.py`)

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .storage import KnowledgeStorage
from .entity import KnowledgeEntity

@dataclass
class ContextPackage:
    task_id: int
    agent_type: str
    domain: str
    context_documents: List[str]
    context_text: str
    completeness_score: float
    missing_requirements: List[str]
    knowledge_sources: List[str]

@dataclass
class ValidationResult:
    is_complete: bool
    completeness_score: float
    missing_requirements: List[str]
    isolation_capable: bool
    recommendations: List[str]

class ContextAssemblyEngine:
    def __init__(self, storage: KnowledgeStorage):
        self.storage = storage
    
    def assemble_context_for_task(self, task_instruction: str, agent_type: str, 
                                 domain: Optional[str] = None) -> ContextPackage:
        """Assemble complete context package for a task"""
        
        # Determine domain if not provided
        if not domain:
            domain = self._infer_domain_from_task(task_instruction)
        
        # Get relevant knowledge entities
        relevant_entities = self._get_relevant_entities(task_instruction, agent_type, domain)
        
        # Build context text
        context_text = self._build_context_text(relevant_entities, task_instruction, agent_type)
        
        # Validate completeness
        validation = self.validate_context_completeness(relevant_entities, task_instruction, agent_type)
        
        # Create context documents list
        context_documents = [entity.id for entity in relevant_entities]
        
        return ContextPackage(
            task_id=0,  # Will be set by caller
            agent_type=agent_type,
            domain=domain,
            context_documents=context_documents,
            context_text=context_text,
            completeness_score=validation.completeness_score,
            missing_requirements=validation.missing_requirements,
            knowledge_sources=[entity.id for entity in relevant_entities]
        )
    
    def validate_context_completeness(self, entities: List[KnowledgeEntity], 
                                    task_instruction: str, agent_type: str) -> ValidationResult:
        """Validate if context is complete for isolated task success"""
        
        # Get agent-specific knowledge requirements
        agent_entity = self.storage.load_entity(f"agent_{agent_type}")
        if not agent_entity:
            return ValidationResult(
                is_complete=False,
                completeness_score=0.0,
                missing_requirements=[f"Agent knowledge for {agent_type} not found"],
                isolation_capable=False,
                recommendations=["Create agent knowledge entity"]
            )
        
        # Check isolation requirements
        required_context = agent_entity.isolation_requirements.minimum_context
        available_context = [entity.id for entity in entities]
        
        missing_requirements = []
        for requirement in required_context:
            if not any(requirement in entity.id or requirement in entity.domain 
                      for entity in entities):
                missing_requirements.append(requirement)
        
        # Calculate completeness score
        completeness_score = 1.0 - (len(missing_requirements) / max(len(required_context), 1))
        
        # Check if task can succeed in isolation
        isolation_capable = completeness_score >= 0.8 and len(missing_requirements) == 0
        
        recommendations = []
        if missing_requirements:
            recommendations.append(f"Add context for: {', '.join(missing_requirements)}")
        if completeness_score < 0.8:
            recommendations.append("Context may be insufficient for isolated task success")
        
        return ValidationResult(
            is_complete=len(missing_requirements) == 0,
            completeness_score=completeness_score,
            missing_requirements=missing_requirements,
            isolation_capable=isolation_capable,
            recommendations=recommendations
        )
    
    def identify_knowledge_gaps(self, task_instruction: str, agent_type: str) -> List[str]:
        """Identify missing knowledge that prevents task success"""
        context_package = self.assemble_context_for_task(task_instruction, agent_type)
        return context_package.missing_requirements
    
    def _infer_domain_from_task(self, task_instruction: str) -> str:
        """Infer domain from task instruction using keyword matching"""
        domain_keywords = {
            "software_development": ["code", "develop", "implement", "programming", "software"],
            "system_architecture": ["system", "architecture", "design", "framework"],
            "task_management": ["task", "project", "plan", "organize", "coordinate"],
            "quality_assurance": ["test", "validate", "quality", "review", "evaluate"],
            "knowledge_management": ["document", "knowledge", "context", "information"]
        }
        
        task_lower = task_instruction.lower()
        domain_scores = {}
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                domain_scores[domain] = score
        
        return max(domain_scores, key=domain_scores.get) if domain_scores else "general"
    
    def _get_relevant_entities(self, task_instruction: str, agent_type: str, 
                              domain: str) -> List[KnowledgeEntity]:
        """Get knowledge entities relevant to the task"""
        relevant_entities = []
        
        # Always include agent-specific knowledge
        agent_entity = self.storage.load_entity(f"agent_{agent_type}")
        if agent_entity:
            relevant_entities.append(agent_entity)
        
        # Include domain knowledge
        domain_entities = self.storage.get_entities_by_domain(domain)
        relevant_entities.extend(domain_entities)
        
        # Include system knowledge
        system_entities = self.storage.list_entities_by_type("system")
        for entity_id in system_entities:
            entity = self.storage.load_entity(entity_id)
            if entity:
                relevant_entities.append(entity)
        
        # Search for task-relevant knowledge
        search_results = self.storage.search_entities(task_instruction)
        for entity in search_results:
            if entity not in relevant_entities:
                relevant_entities.append(entity)
        
        return relevant_entities
    
    def _build_context_text(self, entities: List[KnowledgeEntity], 
                           task_instruction: str, agent_type: str) -> str:
        """Build comprehensive context text from knowledge entities"""
        context_parts = []
        
        # Start with agent-specific context
        agent_entity = next((e for e in entities if e.type == "agent"), None)
        if agent_entity:
            context_parts.append(f"# Agent Context: {agent_entity.name}")
            context_parts.append(agent_entity.content.summary)
            context_parts.append("## Core Concepts:")
            context_parts.extend([f"- {concept}" for concept in agent_entity.content.core_concepts])
            context_parts.append("")
        
        # Add domain knowledge
        domain_entities = [e for e in entities if e.type == "domain"]
        for entity in domain_entities:
            context_parts.append(f"# Domain Knowledge: {entity.name}")
            context_parts.append(entity.content.summary)
            context_parts.append("## Key Procedures:")
            context_parts.extend([f"- {proc}" for proc in entity.content.procedures[:5]])  # Top 5
            context_parts.append("")
        
        # Add process knowledge
        process_entities = [e for e in entities if e.type == "process"]
        for entity in process_entities:
            context_parts.append(f"# Process Framework: {entity.name}")
            context_parts.append(entity.content.summary)
            context_parts.append("")
        
        # Add relevant patterns
        pattern_entities = [e for e in entities if e.type == "pattern"]
        for entity in pattern_entities:
            context_parts.append(f"# Success Pattern: {entity.name}")
            context_parts.append(entity.content.summary)
            context_parts.append("")
        
        return "\n".join(context_parts)
```

### 4. Bootstrap Conversion System (`src/knowledge/bootstrap.py`)

```python
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .entity import (KnowledgeEntity, KnowledgeContent, KnowledgeRelationships, 
                    ContextTemplates, IsolationRequirements, KnowledgeMetadata)
from .storage import KnowledgeStorage

class DocumentationConverter:
    def __init__(self, docs_dir: str, storage: KnowledgeStorage):
        self.docs_dir = Path(docs_dir)
        self.storage = storage
        self.timestamp = datetime.now().isoformat()
    
    def convert_all_documentation(self):
        """Convert all documentation to knowledge entities"""
        print("Converting documentation to knowledge entities...")
        
        # Convert agent guides
        self._convert_agent_guides()
        
        # Convert architecture documents
        self._convert_architecture_docs()
        
        # Convert system principles
        self._convert_system_principles()
        
        # Convert tool documentation
        self._convert_tool_documentation()
        
        # Create initial relationships
        self._create_initial_relationships()
        
        print("Documentation conversion complete!")
    
    def _convert_agent_guides(self):
        """Convert agent guide files to agent knowledge entities"""
        agent_guides = list(self.docs_dir.glob("*_agent_guide.md"))
        
        for guide_path in agent_guides:
            try:
                content = guide_path.read_text(encoding='utf-8')
                agent_name = guide_path.stem.replace("_guide", "")
                
                entity = self._create_agent_knowledge_entity(agent_name, content)
                if entity:
                    self.storage.save_entity(entity)
                    print(f"Converted: {agent_name}")
                
            except Exception as e:
                print(f"Error converting {guide_path}: {e}")
    
    def _create_agent_knowledge_entity(self, agent_name: str, content: str) -> Optional[KnowledgeEntity]:
        """Create agent knowledge entity from guide content"""
        
        # Extract sections using regex
        purpose_match = re.search(r'## Core Purpose\n(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        approach_match = re.search(r'## Fundamental Approach\n(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        success_match = re.search(r'## Success Metrics\n(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        
        if not purpose_match:
            print(f"Could not extract purpose for {agent_name}")
            return None
        
        # Extract core concepts from approach section
        core_concepts = []
        if approach_match:
            approach_text = approach_match.group(1)
            # Extract bullet points and ### sections
            concepts = re.findall(r'(?:^- (.+)|^### (.+))', approach_text, re.MULTILINE)
            core_concepts = [c[0] or c[1] for c in concepts if c[0] or c[1]]
        
        # Extract procedures (look for numbered steps or phases)
        procedures = []
        procedure_matches = re.findall(r'(?:Phase \d+|Step \d+): (.+)', content)
        procedures.extend(procedure_matches)
        
        # Extract examples (look for example sections)
        examples = []
        example_matches = re.findall(r'Example[:\s]*(.+)', content)
        examples.extend(example_matches[:5])  # Limit to 5
        
        # Extract quality criteria from success metrics
        quality_criteria = []
        if success_match:
            success_text = success_match.group(1)
            criteria = re.findall(r'(?:^- (.+)|when (.+))', success_text, re.MULTILINE)
            quality_criteria = [c[0] or c[1] for c in criteria if c[0] or c[1]]
        
        # Domain inference
        domain = self._infer_domain_from_agent_name(agent_name)
        
        # Create entity
        entity = KnowledgeEntity(
            id=f"agent_{agent_name}",
            type="agent",
            name=f"{agent_name.replace('_', ' ').title()} Specialization",
            version="1.0.0",
            domain=domain,
            process_frameworks=self._infer_process_frameworks(agent_name),
            content=KnowledgeContent(
                summary=purpose_match.group(1).strip()[:200] + "...",
                core_concepts=core_concepts[:10],  # Limit to 10
                procedures=procedures[:8],  # Limit to 8
                examples=examples,
                quality_criteria=quality_criteria[:6],  # Limit to 6
                common_pitfalls=[]  # Will be populated later through learning
            ),
            relationships=KnowledgeRelationships(
                enables=[],  # Will be populated in relationship creation
                requires=[],
                related=[]
            ),
            context_templates=ContextTemplates(
                task_context=f"As {agent_name}: {purpose_match.group(1).strip()[:100]}...",
                agent_context=f"{agent_name} specializes in {domain} using systematic approaches."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=[f"{agent_name}_guide", f"{domain}_reference"],
                validation_criteria=["Can execute tasks independently", "Has required domain knowledge"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="agent_guide_conversion",
                tags=[agent_name, domain, "agent_specialization"]
            )
        )
        
        return entity
    
    def _convert_architecture_docs(self):
        """Convert architecture documents to system knowledge"""
        arch_docs = [
            ("updated_entity_architecture.md", "system_entity_architecture"),
            ("updated_process_architecture.md", "system_process_architecture"), 
            ("event_system_guide.md", "system_event_architecture"),
            ("updated_runtime_specification.md", "system_runtime_architecture")
        ]
        
        for doc_name, entity_id in arch_docs:
            doc_path = self.docs_dir / doc_name
            if doc_path.exists():
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    entity = self._create_system_knowledge_entity(entity_id, doc_name, content)
                    if entity:
                        self.storage.save_entity(entity)
                        print(f"Converted: {entity_id}")
                except Exception as e:
                    print(f"Error converting {doc_path}: {e}")
    
    def _create_system_knowledge_entity(self, entity_id: str, doc_name: str, content: str) -> Optional[KnowledgeEntity]:
        """Create system knowledge entity from architecture document"""
        
        # Extract overview/purpose
        overview_match = re.search(r'## (?:Overview|Core Concept|Purpose)\n(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        
        # Extract key principles or concepts
        principles_match = re.search(r'## (?:Principles|Key|Core|Fundamental)(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        
        if not overview_match:
            print(f"Could not extract overview for {entity_id}")
            return None
        
        # Extract core concepts
        core_concepts = []
        if principles_match:
            principles_text = principles_match.group(1)
            concepts = re.findall(r'(?:^- (.+)|^\* (.+)|^### (.+))', principles_text, re.MULTILINE)
            core_concepts = [c[0] or c[1] or c[2] for c in concepts if any(c)]
        
        entity = KnowledgeEntity(
            id=entity_id,
            type="system", 
            name=doc_name.replace("_", " ").replace(".md", "").title(),
            version="1.0.0",
            domain="system_architecture",
            process_frameworks=["system_operation"],
            content=KnowledgeContent(
                summary=overview_match.group(1).strip()[:300] + "...",
                core_concepts=core_concepts[:10],
                procedures=[],  # Extracted later if needed
                examples=[],
                quality_criteria=[],
                common_pitfalls=[]
            ),
            relationships=KnowledgeRelationships(),
            context_templates=ContextTemplates(
                task_context=f"System architecture context: {overview_match.group(1).strip()[:100]}...",
                agent_context="System operation requires understanding of architectural principles and constraints."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["system_architecture_overview"],
                validation_criteria=["Understands system structure", "Can work within architectural constraints"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="architecture_doc_conversion",
                tags=["system", "architecture", "core"]
            )
        )
        
        return entity
    
    def _convert_system_principles(self):
        """Convert project principles to foundational system knowledge"""
        principles_path = self.docs_dir / "updated_project_principles.md"
        if principles_path.exists():
            content = principles_path.read_text(encoding='utf-8')
            
            # Extract core principles
            principles_section = re.search(r'## Fundamental Principles(.+?)(?=\n##|\Z)', content, re.DOTALL)
            
            if principles_section:
                principles_text = principles_section.group(1)
                principles = re.findall(r'### (.+?)\n(.+?)(?=\n###|\n##|\Z)', principles_text, re.DOTALL)
                
                core_concepts = []
                procedures = []
                
                for title, description in principles:
                    core_concepts.append(title.strip())
                    # Extract key points from description
                    points = re.findall(r'(?:^- (.+)|^\* (.+))', description, re.MULTILINE)
                    procedures.extend([p[0] or p[1] for p in points if any(p)])
                
                entity = KnowledgeEntity(
                    id="system_core_principles",
                    type="system",
                    name="Core System Principles",
                    version="1.0.0",
                    domain="system_architecture",
                    process_frameworks=["system_operation", "self_improvement"],
                    content=KnowledgeContent(
                        summary="Fundamental principles that guide all system operations and evolution",
                        core_concepts=core_concepts,
                        procedures=procedures[:10],
                        examples=[],
                        quality_criteria=["System follows all core principles", "Principles guide decision making"],
                        common_pitfalls=["Ignoring principles for convenience", "Ad-hoc solutions without systematic approach"]
                    ),
                    relationships=KnowledgeRelationships(
                        enables=["all_system_operations"],
                        requires=[],
                        related=["system_entity_architecture", "system_process_architecture"]
                    ),
                    context_templates=ContextTemplates(
                        task_context="All operations must follow core system principles: process-first approach, entity-based architecture, systematic learning.",
                        agent_context="System operation requires adherence to fundamental principles in all decisions and actions."
                    ),
                    isolation_requirements=IsolationRequirements(
                        minimum_context=["core_principles_complete"],
                        validation_criteria=["Understands and applies core principles", "Makes principle-guided decisions"]
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
                print("Converted: system_core_principles")
    
    def _convert_tool_documentation(self):
        """Convert tool documentation to tool knowledge entities"""
        tool_docs = [
            ("mvp_tooling_guide.md", "tooling_system"),
            ("internal_tools_documentation.md", "internal_tools")
        ]
        
        for doc_name, base_id in tool_docs:
            doc_path = self.docs_dir / doc_name
            if doc_path.exists():
                content = doc_path.read_text(encoding='utf-8')
                
                # Create general tool system knowledge
                entity = self._create_tool_system_knowledge(base_id, content)
                if entity:
                    self.storage.save_entity(entity)
                    print(f"Converted: {base_id}")
    
    def _create_tool_system_knowledge(self, entity_id: str, content: str) -> Optional[KnowledgeEntity]:
        """Create tool system knowledge from documentation"""
        
        overview_match = re.search(r'## (?:Overview|Architecture)\n(.+?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        
        if not overview_match:
            return None
        
        # Extract tool categories
        tool_sections = re.findall(r'### (.+?)\n(.+?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        
        procedures = []
        examples = []
        
        for section_title, section_content in tool_sections[:5]:  # Limit to 5 sections
            procedures.append(section_title.strip())
            # Extract examples from section
            section_examples = re.findall(r'```[^`]+```', section_content)
            examples.extend(section_examples[:2])  # Limit examples per section
        
        entity = KnowledgeEntity(
            id=f"tool_{entity_id}",
            type="tool",
            name=f"{entity_id.replace('_', ' ').title()} System",
            version="1.0.0",
            domain="system_operation",
            process_frameworks=["tool_management", "capability_provision"],
            content=KnowledgeContent(
                summary=overview_match.group(1).strip()[:300] + "...",
                core_concepts=["Tool-based capability provision", "Permission-based access", "Usage tracking"],
                procedures=procedures,
                examples=examples[:5],
                quality_criteria=["Tools work reliably", "Permissions enforced correctly", "Usage tracked accurately"],
                common_pitfalls=["Permission bypass", "Tool misuse", "Performance issues"]
            ),
            relationships=KnowledgeRelationships(),
            context_templates=ContextTemplates(
                task_context="When using tools: Ensure proper permissions, follow usage guidelines, track tool effectiveness.",
                agent_context="Tool usage requires understanding of capabilities, permissions, and proper usage patterns."
            ),
            isolation_requirements=IsolationRequirements(
                minimum_context=["tool_capabilities_reference", "permission_requirements"],
                validation_criteria=["Can use tools correctly", "Understands permission requirements"]
            ),
            metadata=KnowledgeMetadata(
                created_at=self.timestamp,
                last_updated=self.timestamp,
                source="tool_documentation_conversion",
                tags=["tools", "capabilities", "system"]
            )
        )
        
        return entity
    
    def _create_initial_relationships(self):
        """Create initial relationships between knowledge entities"""
        # This would analyze all entities and create logical relationships
        # For MVP, we'll create basic relationships based on naming patterns
        print("Creating initial knowledge relationships...")
        
        # Implementation would go here - analyze entity content and create relationships
        # For now, relationships will be built up over time through usage
    
    def _infer_domain_from_agent_name(self, agent_name: str) -> str:
        """Infer domain from agent name"""
        domain_mapping = {
            "agent_selector": "task_routing",
            "planning_agent": "task_decomposition", 
            "context_addition": "knowledge_management",
            "tool_addition": "capability_management",
            "task_evaluator": "quality_assurance",
            "summary_agent": "communication",
            "documentation_agent": "knowledge_management",
            "review_agent": "system_improvement",
            "feedback_agent": "coordination",
            "request_validation": "resource_management",
            "investigator_agent": "analysis",
            "optimizer_agent": "performance_optimization",
            "recovery_agent": "system_resilience"
        }
        return domain_mapping.get(agent_name, "general")
    
    def _infer_process_frameworks(self, agent_name: str) -> List[str]:
        """Infer relevant process frameworks for agent"""
        framework_mapping = {
            "agent_selector": ["task_routing", "agent_assignment"],
            "planning_agent": ["task_breakdown", "workflow_design"],
            "context_addition": ["knowledge_provision", "context_assembly"],
            "tool_addition": ["capability_discovery", "tool_assignment"],
            "task_evaluator": ["quality_evaluation", "performance_assessment"],
            "summary_agent": ["information_synthesis", "communication"],
            "documentation_agent": ["knowledge_capture", "documentation_creation"],
            "review_agent": ["system_analysis", "improvement_planning"],
            "feedback_agent": ["coordination", "communication"],
            "request_validation": ["resource_validation", "efficiency_optimization"],
            "investigator_agent": ["analysis", "research"],
            "optimizer_agent": ["performance_optimization", "system_improvement"],
            "recovery_agent": ["error_recovery", "system_resilience"]
        }
        return framework_mapping.get(agent_name, ["general"])

def bootstrap_knowledge_system():
    """Main function to bootstrap the knowledge system"""
    storage = KnowledgeStorage()
    converter = DocumentationConverter(".", storage)  # Assuming docs are in current directory
    
    converter.convert_all_documentation()
    
    print("\nKnowledge bootstrap complete!")
    print(f"Created knowledge entities in: {storage.knowledge_dir}")
    
    # Validate the conversion
    total_entities = len(list(storage.list_all_entities()))
    print(f"Total knowledge entities created: {total_entities}")

if __name__ == "__main__":
    bootstrap_knowledge_system()
```

### 5. Implementation Script (`scripts/bootstrap_knowledge.py`)

```python
#!/usr/bin/env python3
"""
Bootstrap Knowledge System

Converts existing documentation into structured knowledge entities
and sets up the MVP knowledge system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge.bootstrap import bootstrap_knowledge_system
from knowledge.storage import KnowledgeStorage
from knowledge.engine import ContextAssemblyEngine

def main():
    print("Starting knowledge system bootstrap...")
    
    # Run the bootstrap conversion
    bootstrap_knowledge_system()
    
    # Test the knowledge system
    print("\nTesting knowledge system...")
    storage = KnowledgeStorage()
    engine = ContextAssemblyEngine(storage)
    
    # Test context assembly
    test_context = engine.assemble_context_for_task(
        "Plan a software development project",
        "planning_agent"
    )
    
    print(f"Test context completeness: {test_context.completeness_score:.2f}")
    print(f"Context sources: {len(test_context.knowledge_sources)}")
    
    if test_context.missing_requirements:
        print(f"Missing: {test_context.missing_requirements}")
    
    print("\nKnowledge system bootstrap complete!")

if __name__ == "__main__":
    main()
```

### 6. Database Integration

Add to your existing database schema:

```sql
-- Add knowledge tracking to tasks table
ALTER TABLE tasks ADD COLUMN context_package_id VARCHAR(255);
ALTER TABLE tasks ADD COLUMN knowledge_gaps TEXT;
ALTER TABLE tasks ADD COLUMN context_completeness_score FLOAT DEFAULT 0.0;

-- Knowledge usage tracking
CREATE TABLE knowledge_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_entity_id VARCHAR(255) NOT NULL,
    task_id INTEGER NOT NULL,
    agent_type VARCHAR(255),
    usage_type VARCHAR(255), -- 'context_assembly', 'validation', 'gap_detection'
    effectiveness_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Knowledge gap tracking
CREATE TABLE knowledge_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    gap_type VARCHAR(255), -- 'domain', 'process', 'tool', 'context'
    gap_description TEXT,
    priority VARCHAR(255) DEFAULT 'medium',
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

## Deployment Instructions

1. **Run the bootstrap script**:
   ```bash
   python scripts/bootstrap_knowledge.py
   ```

2. **Verify knowledge creation**:
   ```bash
   ls -la knowledge/*/
   ```

3. **Test context assembly**:
   ```bash
   python scripts/validate_knowledge.py
   ```

4. **Integrate with entity framework**:
   - Update task creation to use context assembly
   - Add knowledge gap detection to failed tasks
   - Integrate knowledge evolution with successful executions

This implementation provides a solid foundation for the MVP knowledge system that can grow into the full architecture as the system evolves.