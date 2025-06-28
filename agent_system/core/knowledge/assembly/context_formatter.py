"""
Context Formatter for Knowledge System

Formats knowledge entities into comprehensive context text for task execution.
"""

from typing import List
import logging

from ..entity import KnowledgeEntity

logger = logging.getLogger(__name__)


class ContextFormatter:
    """Formats knowledge entities into context text."""
    
    def build_context_text(
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