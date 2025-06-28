"""
Analysis Utilities for Knowledge System

Utilities for analyzing execution patterns, failures, and extracting knowledge.
"""

from typing import Dict, List, Any
import re
import logging

logger = logging.getLogger(__name__)


class AnalysisUtils:
    """Utilities for analyzing execution patterns and failures."""
    
    @staticmethod
    def analyze_failure_patterns(failure_result: str) -> List[str]:
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
    
    @staticmethod
    def extract_execution_patterns(
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
    
    @staticmethod
    def infer_domain_from_task(task_instruction: str, domain_keywords: Dict[str, List[str]]) -> str:
        """Infer domain from task instruction using keyword matching."""
        task_lower = task_instruction.lower()
        domain_scores = {}
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            # Return domain with highest score
            return max(domain_scores, key=domain_scores.get)
        
        return "general"
    
    @staticmethod
    def load_domain_keywords() -> Dict[str, List[str]]:
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