"""
Model configuration for the agent system.

This module defines the available AI models and their characteristics,
helping the system choose the appropriate model for different tasks.
"""

from typing import Dict, Any
from enum import Enum


class ModelCapability(Enum):
    """Model capability levels"""
    LITE = "lite"         # Fast, cost-efficient, basic tasks
    BALANCED = "balanced" # Good balance of speed and capability
    ADVANCED = "advanced" # Highest capability, complex reasoning


# Gemini 2.5 model configurations
GEMINI_25_MODELS = {
    "gemini-2.5-flash-lite": {
        "name": "Gemini 2.5 Flash-Lite",
        "capability": ModelCapability.LITE,
        "description": "Fastest and most cost-efficient model for high-volume tasks",
        "best_for": [
            "Classification tasks",
            "Simple summarization", 
            "Translation",
            "Quick validations",
            "High-throughput operations"
        ],
        "context_window": 1_000_000,
        "supports_thinking": True,  # But off by default
        "relative_cost": 1,
        "relative_speed": 10
    },
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash", 
        "capability": ModelCapability.BALANCED,
        "description": "Balanced performance for most tasks",
        "best_for": [
            "General agent tasks",
            "Code generation",
            "Analysis and planning",
            "Multi-step reasoning",
            "Tool usage"
        ],
        "context_window": 1_000_000,
        "supports_thinking": True,
        "relative_cost": 3,
        "relative_speed": 5
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "capability": ModelCapability.ADVANCED,
        "description": "Highest capability for complex tasks",
        "best_for": [
            "Complex reasoning",
            "Architectural decisions",
            "Deep code analysis",
            "Critical validations",
            "Research and investigation"
        ],
        "context_window": 2_000_000,
        "supports_thinking": True,
        "relative_cost": 10,
        "relative_speed": 2
    }
}


class ModelSelector:
    """Helper class for selecting appropriate models based on task requirements"""
    
    @staticmethod
    def get_model_for_task(task_type: str, priority: str = "cost") -> str:
        """
        Select the appropriate model based on task type and priority.
        
        Args:
            task_type: Type of task (e.g., "validation", "architecture", "simple")
            priority: Optimization priority ("cost", "speed", "quality")
            
        Returns:
            Model name string
        """
        # Task type mappings
        task_model_map = {
            # Lite tasks
            "validation": "gemini-2.5-flash-lite",
            "classification": "gemini-2.5-flash-lite", 
            "summarization": "gemini-2.5-flash-lite",
            "simple": "gemini-2.5-flash-lite",
            
            # Balanced tasks
            "general": "gemini-2.5-flash",
            "coding": "gemini-2.5-flash",
            "planning": "gemini-2.5-flash",
            "tool_usage": "gemini-2.5-flash",
            
            # Advanced tasks
            "architecture": "gemini-2.5-pro",
            "complex_reasoning": "gemini-2.5-pro",
            "critical_validation": "gemini-2.5-pro",
            "research": "gemini-2.5-pro"
        }
        
        # Get base recommendation
        model = task_model_map.get(task_type, "gemini-2.5-flash")
        
        # Adjust based on priority
        if priority == "cost" and model == "gemini-2.5-pro":
            # Downgrade to flash for cost savings unless critical
            if task_type not in ["architecture", "critical_validation"]:
                model = "gemini-2.5-flash"
        elif priority == "quality" and model == "gemini-2.5-flash-lite":
            # Upgrade to flash for better quality
            model = "gemini-2.5-flash"
        
        return model
    
    @staticmethod
    def estimate_cost(model: str, tokens: int) -> float:
        """
        Estimate relative cost for a given model and token count.
        
        Args:
            model: Model name
            tokens: Estimated total tokens (input + output)
            
        Returns:
            Relative cost estimate
        """
        model_config = GEMINI_25_MODELS.get(model, {})
        relative_cost = model_config.get("relative_cost", 1)
        return relative_cost * (tokens / 1000)


# Default model configurations for different agent types
AGENT_MODEL_PREFERENCES = {
    "agent_selector": "gemini-2.5-flash-lite",  # Fast routing decisions
    "task_breakdown": "gemini-2.5-flash",       # Balanced for planning
    "context_addition": "gemini-2.5-flash",     # General purpose
    "tool_addition": "gemini-2.5-flash",        # General purpose
    "task_evaluator": "gemini-2.5-flash-lite",  # Quick validations
    "documentation_agent": "gemini-2.5-flash",  # Quality documentation
    "summary_agent": "gemini-2.5-flash-lite",   # Fast summarization
    "review_agent": "gemini-2.5-pro",           # Critical reviews
    "planning_agent": "gemini-2.5-flash",       # Strategic planning
    "investigator_agent": "gemini-2.5-pro",     # Deep investigation
    "optimizer_agent": "gemini-2.5-flash",      # Optimization analysis
    "feedback_agent": "gemini-2.5-flash",       # User interactions
    "recovery_agent": "gemini-2.5-flash"        # Error recovery
}