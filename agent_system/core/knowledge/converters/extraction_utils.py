"""
Utility functions for extracting information from documentation.
"""

import re
from typing import Dict, List


class ExtractionUtils:
    """Utilities for extracting structured information from documentation."""
    
    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """Extract major sections from markdown documentation."""
        sections = {}
        
        # Common section patterns
        section_patterns = [
            r"## Purpose\s*\n(.*?)(?=\n##|\Z)",
            r"## Core Concepts?\s*\n(.*?)(?=\n##|\Z)",
            r"## Approach\s*\n(.*?)(?=\n##|\Z)", 
            r"## Success Metrics?\s*\n(.*?)(?=\n##|\Z)",
            r"## Common Pitfalls\s*\n(.*?)(?=\n##|\Z)",
            r"## Examples?\s*\n(.*?)(?=\n##|\Z)",
            r"## Implementation\s*\n(.*?)(?=\n##|\Z)",
            r"## Context Documents?\s*\n(.*?)(?=\n##|\Z)",
            r"## Available Tools?\s*\n(.*?)(?=\n##|\Z)",
            r"## Permission Model\s*\n(.*?)(?=\n##|\Z)",
            r"## Overview\s*\n(.*?)(?=\n##|\Z)",
            r"## Architecture\s*\n(.*?)(?=\n##|\Z)"
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                section_name = pattern.split()[1].lower()
                sections[section_name] = match.group(1).strip()
        
        return sections
    
    @staticmethod
    def extract_concepts_from_approach(approach_text: str) -> List[str]:
        """Extract core concepts from approach section."""
        concepts = []
        
        # Look for bullet points
        bullet_lines = re.findall(r"[*-]\s+(.+)", approach_text)
        for line in bullet_lines[:10]:
            # Clean up the concept
            concept = line.strip()
            if len(concept) > 10 and len(concept) < 100:
                concepts.append(concept)
        
        # Also look for numbered lists
        numbered_lines = re.findall(r"\d+\.\s+(.+)", approach_text) 
        for line in numbered_lines[:10]:
            concept = line.strip()
            if len(concept) > 10 and len(concept) < 100 and concept not in concepts:
                concepts.append(concept)
        
        return concepts[:10]
    
    @staticmethod
    def extract_procedures(content: str) -> List[str]:
        """Extract procedural steps from content."""
        procedures = []
        
        # Look for numbered procedures
        proc_pattern = r"(\d+\.\s+[A-Z][^.!?]+[.!?])"
        matches = re.findall(proc_pattern, content)
        
        for match in matches[:15]:
            procedure = match.strip()
            if len(procedure) > 20 and len(procedure) < 200:
                procedures.append(procedure)
        
        # Also look for imperative sentences
        imperative_pattern = r"(?:^|\n)([A-Z][^.!?]*(?:Create|Build|Implement|Define|Extract|Analyze|Test|Validate|Check|Update)[^.!?]+[.!?])"
        imp_matches = re.findall(imperative_pattern, content, re.MULTILINE)
        
        for match in imp_matches[:10]:
            if match not in procedures and len(match) > 20:
                procedures.append(match.strip())
        
        return procedures[:8]
    
    @staticmethod
    def extract_examples(content: str) -> List[str]:
        """Extract examples from content."""
        examples = []
        
        # Look for example sections
        example_pattern = r"(?:Example:|For example,|e\.g\.,)([^.!?]+[.!?])"
        matches = re.findall(example_pattern, content, re.IGNORECASE)
        
        for match in matches[:10]:
            example = match.strip()
            if len(example) > 15:
                examples.append(example)
        
        # Look for code blocks as examples
        code_blocks = re.findall(r"```[^`]+```", content)
        for block in code_blocks[:5]:
            if len(block) < 500:
                examples.append(block)
        
        return examples[:5]
    
    @staticmethod
    def extract_quality_criteria(success_text: str) -> List[str]:
        """Extract quality criteria from success metrics."""
        criteria = []
        
        # Look for measurable criteria
        metric_patterns = [
            r"[*-]\s+([^*\n]+(?:accuracy|rate|score|percentage|time|quality|coverage)[^*\n]+)",
            r"[*-]\s+([^*\n]+(?:must|should|needs to|requires)[^*\n]+)",
            r"(?:Success when:|Success criteria:)([^.!?]+[.!?])"
        ]
        
        for pattern in metric_patterns:
            matches = re.findall(pattern, success_text, re.IGNORECASE)
            for match in matches:
                criterion = match.strip()
                if len(criterion) > 10 and len(criterion) < 150:
                    criteria.append(criterion)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_criteria = []
        for c in criteria:
            if c not in seen:
                seen.add(c)
                unique_criteria.append(c)
        
        return unique_criteria[:6]
    
    @staticmethod
    def extract_pitfalls(content: str) -> List[str]:
        """Extract common pitfalls and anti-patterns."""
        pitfalls = []
        
        # Look for pitfall sections
        pitfall_section = re.search(
            r"(?:Common Pitfalls|Anti-patterns|Avoid|Don't|Never)[^#]*", 
            content, 
            re.IGNORECASE
        )
        
        if pitfall_section:
            pitfall_text = pitfall_section.group(0)
            
            # Extract bullet points
            bullets = re.findall(r"[*-]\s+([^*\n]+)", pitfall_text)
            for bullet in bullets[:10]:
                if len(bullet) > 10:
                    pitfalls.append(bullet.strip())
        
        # Look for negative patterns in general content
        negative_patterns = re.findall(
            r"(?:Never|Don't|Avoid|Should not|Must not)([^.!?]+[.!?])",
            content,
            re.IGNORECASE
        )
        
        for pattern in negative_patterns[:5]:
            pitfall = pattern.strip()
            if len(pitfall) > 10 and pitfall not in pitfalls:
                pitfalls.append(pitfall)
        
        return pitfalls[:4]
    
    @staticmethod
    def extract_required_knowledge(content: str) -> List[str]:
        """Extract required knowledge dependencies."""
        requirements = []
        
        # Look for requirement patterns
        req_patterns = [
            r"(?:Requires:|Prerequisites:|Depends on:)([^.!?\n]+)",
            r"(?:Must understand|Need to know|Should know)([^.!?\n]+)",
            r"(?:Knowledge of|Understanding of|Familiarity with)([^.!?\n]+)"
        ]
        
        for pattern in req_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                req = match.strip()
                if len(req) > 5 and len(req) < 100:
                    requirements.append(req)
        
        # Extract from context document references
        context_refs = re.findall(r"context_documents/(\w+)", content)
        for ref in context_refs:
            requirements.append(f"{ref}_knowledge")
        
        # Remove duplicates
        return list(set(requirements))[:8]
    
    @staticmethod
    def extract_system_concepts(content: str, sections: Dict[str, str]) -> List[str]:
        """Extract system-level concepts from architecture documentation."""
        concepts = []
        
        # Extract from overview section
        if "overview" in sections:
            overview_concepts = ExtractionUtils.extract_concepts_from_approach(sections["overview"])
            concepts.extend(overview_concepts)
        
        # Look for architecture patterns
        pattern_matches = re.findall(
            r"(?:pattern|principle|concept|design|architecture):\s*([^.!?\n]+)",
            content,
            re.IGNORECASE
        )
        
        for match in pattern_matches[:10]:
            concept = match.strip()
            if len(concept) > 10 and concept not in concepts:
                concepts.append(concept)
        
        # Extract key components
        component_section = re.search(r"## (?:Components?|Modules?|Systems?)\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if component_section:
            comp_text = component_section.group(1)
            bullets = re.findall(r"[*-]\s+\*?\*?([^*:\n]+)", comp_text)
            for bullet in bullets[:10]:
                if len(bullet) > 5 and bullet not in concepts:
                    concepts.append(bullet.strip())
        
        return concepts[:15]
    
    @staticmethod
    def extract_principles(content: str) -> List[Dict[str, str]]:
        """Extract principles with descriptions from system documentation."""
        principles = []
        
        # Look for principles section
        principles_section = re.search(
            r"## (?:Principles?|Core Principles?|Design Principles?)\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if principles_section:
            prin_text = principles_section.group(1)
            
            # Extract principles with descriptions
            # Pattern: **Principle Name**: Description
            prin_pattern = r"\*\*([^*]+)\*\*:\s*([^*\n]+)"
            matches = re.findall(prin_pattern, prin_text)
            
            for name, desc in matches[:10]:
                principles.append({
                    "name": name.strip(),
                    "description": desc.strip()
                })
            
            # Also try numbered format
            # Pattern: 1. Principle Name - Description
            num_pattern = r"\d+\.\s*([^-:\n]+)[-:]\s*([^.\n]+)"
            num_matches = re.findall(num_pattern, prin_text)
            
            for name, desc in num_matches[:10]:
                principle = {
                    "name": name.strip(),
                    "description": desc.strip()
                }
                if principle not in principles:
                    principles.append(principle)
        
        return principles[:8]
    
    @staticmethod
    def infer_domain_from_agent_name(agent_name: str) -> str:
        """Infer domain from agent name."""
        domain_mappings = {
            "process_discovery": "process_framework_establishment",
            "agent_selector": "task_routing_orchestration",
            "planning": "task_decomposition",
            "context_addition": "knowledge_management",
            "tool_addition": "capability_expansion",
            "task_evaluator": "quality_assessment",
            "documentation": "knowledge_capture",
            "summary": "information_synthesis",
            "review": "continuous_improvement"
        }
        
        # Direct mapping
        if agent_name in domain_mappings:
            return domain_mappings[agent_name]
        
        # Pattern matching
        if "test" in agent_name:
            return "testing_validation"
        elif "analysis" in agent_name or "analyze" in agent_name:
            return "analytical_processing"
        elif "build" in agent_name or "create" in agent_name:
            return "construction_generation"
        else:
            return "general_task_execution"
    
    @staticmethod
    def infer_process_frameworks(agent_name: str) -> List[str]:
        """Infer applicable process frameworks from agent name."""
        framework_mappings = {
            "process_discovery": ["domain_analysis", "framework_establishment", "systematic_structuring"],
            "agent_selector": ["task_classification", "agent_matching", "routing_optimization"],
            "planning": ["task_decomposition", "dependency_analysis", "milestone_planning"],
            "context_addition": ["knowledge_retrieval", "context_assembly", "gap_analysis"],
            "tool_addition": ["capability_assessment", "tool_integration", "permission_management"],
            "task_evaluator": ["quality_validation", "success_measurement", "output_verification"],
            "documentation": ["knowledge_extraction", "format_standardization", "metadata_enrichment"],
            "summary": ["information_distillation", "key_point_extraction", "synthesis_generation"],
            "review": ["pattern_recognition", "improvement_identification", "optimization_planning"]
        }
        
        return framework_mappings.get(agent_name, ["general_process_framework"])