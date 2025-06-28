"""
Relationship builder for creating connections between knowledge entities.
"""

import logging
from typing import List, Dict, Set
from ..entity import KnowledgeEntity

logger = logging.getLogger(__name__)


class RelationshipBuilder:
    """Builds relationships between knowledge entities."""
    
    def __init__(self):
        """Initialize relationship builder."""
        self.entities_by_id: Dict[str, KnowledgeEntity] = {}
        self.entities_by_type: Dict[str, List[KnowledgeEntity]] = {}
        self.entities_by_domain: Dict[str, List[KnowledgeEntity]] = {}
    
    def add_entity(self, entity: KnowledgeEntity):
        """Add entity to internal tracking for relationship building."""
        self.entities_by_id[entity.id] = entity
        
        # Track by type
        if entity.type not in self.entities_by_type:
            self.entities_by_type[entity.type] = []
        self.entities_by_type[entity.type].append(entity)
        
        # Track by domain
        if entity.domain not in self.entities_by_domain:
            self.entities_by_domain[entity.domain] = []
        self.entities_by_domain[entity.domain].append(entity)
    
    def build_all_relationships(self) -> int:
        """Build relationships between all tracked entities.
        
        Returns:
            Number of relationships created
        """
        logger.info("Building entity relationships...")
        relationship_count = 0
        
        # Build agent to process relationships
        relationship_count += self._build_agent_process_relationships()
        
        # Build process to tool relationships
        relationship_count += self._build_process_tool_relationships()
        
        # Build domain relationships
        relationship_count += self._build_domain_relationships()
        
        # Build system architecture relationships
        relationship_count += self._build_system_relationships()
        
        # Build initialization task relationships
        relationship_count += self._build_initialization_relationships()
        
        logger.info(f"Created {relationship_count} entity relationships")
        return relationship_count
    
    def _build_agent_process_relationships(self) -> int:
        """Build relationships between agents and processes."""
        count = 0
        
        agents = self.entities_by_type.get("agent", [])
        processes = self.entities_by_type.get("process", [])
        
        for agent in agents:
            agent_name = agent.id.replace("agent_knowledge_", "")
            
            for process in processes:
                process_name = process.id.replace("process_knowledge_", "")
                
                # Match agents to their primary processes
                if self._should_link_agent_process(agent_name, process_name):
                    # Agent enables process
                    if process.id not in agent.relationships.enables:
                        agent.relationships.enables.append(process.id)
                        count += 1
                    
                    # Process requires agent
                    if agent.id not in process.relationships.requires:
                        process.relationships.requires.append(agent.id)
                        count += 1
                    
                    # Mark as related
                    if process.id not in agent.relationships.related:
                        agent.relationships.related.append(process.id)
                    if agent.id not in process.relationships.related:
                        process.relationships.related.append(agent.id)
        
        return count
    
    def _build_process_tool_relationships(self) -> int:
        """Build relationships between processes and tools."""
        count = 0
        
        processes = self.entities_by_type.get("process", [])
        tools = self.entities_by_type.get("tool", [])
        
        for process in processes:
            process_name = process.id.replace("process_knowledge_", "")
            
            for tool in tools:
                tool_name = tool.id.replace("tool_knowledge_", "").split("_")[0]
                
                # Match processes to relevant tools
                if self._should_link_process_tool(process_name, tool_name):
                    # Process requires tool
                    if tool.id not in process.relationships.requires:
                        process.relationships.requires.append(tool.id)
                        count += 1
                    
                    # Tool enables process capabilities
                    if process.id not in tool.relationships.enables:
                        tool.relationships.enables.append(process.id)
                        count += 1
        
        return count
    
    def _build_domain_relationships(self) -> int:
        """Build relationships within domains."""
        count = 0
        
        for domain, entities in self.entities_by_domain.items():
            # Skip if only one entity in domain
            if len(entities) <= 1:
                continue
            
            # Find the domain entity if it exists
            domain_entity = None
            for entity in entities:
                if entity.type == "domain":
                    domain_entity = entity
                    break
            
            # Link all entities in domain
            for entity in entities:
                # Skip self-relationships
                if domain_entity and entity.id != domain_entity.id:
                    # Domain entity enables all domain entities
                    if entity.id not in domain_entity.relationships.enables:
                        domain_entity.relationships.enables.append(entity.id)
                        count += 1
                    
                    # All domain entities require domain knowledge
                    if domain_entity.id not in entity.relationships.requires:
                        entity.relationships.requires.append(domain_entity.id)
                        count += 1
                
                # Link related entities in same domain
                for other in entities:
                    if entity.id != other.id and other.id not in entity.relationships.related:
                        # Only link if they share process frameworks
                        if any(pf in other.process_frameworks for pf in entity.process_frameworks):
                            entity.relationships.related.append(other.id)
                            count += 1
        
        return count
    
    def _build_system_relationships(self) -> int:
        """Build relationships between system architecture components."""
        count = 0
        
        system_entities = self.entities_by_type.get("system", [])
        
        # Define architectural dependencies
        arch_dependencies = {
            "system_entity_architecture": ["system_process_architecture"],
            "system_process_architecture": ["system_runtime_architecture"],
            "system_event_architecture": ["system_entity_architecture"],
            "system_runtime_architecture": ["system_entity_architecture", "system_process_architecture"]
        }
        
        for entity in system_entities:
            deps = arch_dependencies.get(entity.id, [])
            
            for dep_id in deps:
                if dep_id in self.entities_by_id:
                    # This entity requires the dependency
                    if dep_id not in entity.relationships.requires:
                        entity.relationships.requires.append(dep_id)
                        count += 1
                    
                    # The dependency enables this entity
                    dep_entity = self.entities_by_id[dep_id]
                    if entity.id not in dep_entity.relationships.enables:
                        dep_entity.relationships.enables.append(entity.id)
                        count += 1
        
        return count
    
    def _build_initialization_relationships(self) -> int:
        """Build relationships for initialization tasks."""
        count = 0
        
        init_tasks = [e for e in self.entities_by_type.get("pattern", []) 
                      if e.id.startswith("init_task_")]
        
        # Sort by sequence order
        init_tasks.sort(key=lambda x: x.metadata.get("sequence_order", 0))
        
        # Link sequential tasks
        for i in range(len(init_tasks) - 1):
            current = init_tasks[i]
            next_task = init_tasks[i + 1]
            
            # Current enables next
            if next_task.id not in current.relationships.enables:
                current.relationships.enables.append(next_task.id)
                count += 1
            
            # Next requires current
            if current.id not in next_task.relationships.requires:
                next_task.relationships.requires.append(current.id)
                count += 1
        
        return count
    
    def _should_link_agent_process(self, agent_name: str, process_name: str) -> bool:
        """Determine if agent and process should be linked."""
        # Direct name matching
        if agent_name in process_name or process_name in agent_name:
            return True
        
        # Semantic matching
        agent_process_mapping = {
            "process_discovery": ["domain_analysis", "framework_establishment"],
            "agent_selector": ["task_routing", "agent_selection"],
            "planning": ["task_decomposition", "planning"],
            "context_addition": ["knowledge", "context"],
            "tool_addition": ["tool", "capability"],
            "task_evaluator": ["evaluation", "validation"],
            "documentation": ["documentation", "knowledge_capture"],
            "summary": ["summary", "synthesis"],
            "review": ["review", "improvement"]
        }
        
        agent_processes = agent_process_mapping.get(agent_name, [])
        return any(ap in process_name for ap in agent_processes)
    
    def _should_link_process_tool(self, process_name: str, tool_name: str) -> bool:
        """Determine if process and tool should be linked."""
        # Process-tool mapping
        process_tool_mapping = {
            "task_decomposition": ["break_down_task", "start_subtask"],
            "knowledge": ["request_context", "query_database"],
            "tool": ["request_tools", "list_optional_tools"],
            "evaluation": ["end_task", "flag_for_review"],
            "agent_selection": ["list_agents", "query_database"],
            "documentation": ["query_database", "send_message_to_user"]
        }
        
        # Check if process uses tool
        for process_key, tools in process_tool_mapping.items():
            if process_key in process_name:
                return tool_name in tools
        
        # Default core tools used by all processes
        core_tools = ["query_database", "end_task"]
        return tool_name in core_tools
    
    def get_entity_graph(self) -> Dict[str, Dict[str, List[str]]]:
        """Get a graph representation of all entity relationships.
        
        Returns:
            Dict mapping entity IDs to their relationships
        """
        graph = {}
        
        for entity_id, entity in self.entities_by_id.items():
            graph[entity_id] = {
                "enables": entity.relationships.enables,
                "requires": entity.relationships.requires,
                "related": entity.relationships.related,
                "type": entity.type,
                "domain": entity.domain,
                "name": entity.name
            }
        
        return graph
    
    def validate_relationships(self) -> List[str]:
        """Validate relationship consistency.
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        for entity_id, entity in self.entities_by_id.items():
            # Check for circular dependencies
            if entity_id in entity.relationships.requires:
                warnings.append(f"Circular dependency: {entity_id} requires itself")
            
            # Check for missing entities in relationships
            for rel_id in entity.relationships.enables + entity.relationships.requires + entity.relationships.related:
                if rel_id not in self.entities_by_id:
                    warnings.append(f"Missing entity in relationship: {entity_id} references {rel_id}")
            
            # Check for orphaned entities (no relationships)
            total_rels = (len(entity.relationships.enables) + 
                         len(entity.relationships.requires) + 
                         len(entity.relationships.related))
            if total_rels == 0 and entity.type != "domain":
                warnings.append(f"Orphaned entity with no relationships: {entity_id}")
        
        return warnings