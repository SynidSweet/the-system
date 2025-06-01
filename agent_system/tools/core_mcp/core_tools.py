from typing import Dict, Any, Optional
import json
from core.models import MCPToolResult, TaskStatus
from core.database_manager import database
from ..base_tool import CoreMCPTool


class BreakDownTaskTool(CoreMCPTool):
    """Spawn breakdown agent for current task"""
    
    def __init__(self):
        super().__init__(
            name="break_down_task",
            description="Break down the current task into smaller, manageable subtasks by spawning a task breakdown agent",
            parameters={
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of why the task needs to be broken down"
                    },
                    "complexity_assessment": {
                        "type": "string", 
                        "description": "Assessment of the task complexity"
                    }
                },
                "required": ["reasoning"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        reasoning = kwargs.get("reasoning")
        complexity_assessment = kwargs.get("complexity_assessment", "Complex task requiring breakdown")
        
        # This will be called from within an agent execution context
        # For now, return a placeholder result
        # TODO: Implement actual task breakdown spawning
        
        return MCPToolResult(
            success=True,
            result=f"Task breakdown requested: {reasoning}",
            metadata={
                "tool_name": "break_down_task",
                "reasoning": reasoning,
                "complexity_assessment": complexity_assessment,
                "action": "spawn_breakdown_agent"
            }
        )


class StartSubtaskTool(CoreMCPTool):
    """Create isolated subtask with specific agent"""
    
    def __init__(self):
        super().__init__(
            name="start_subtask",
            description="Create a new subtask in the same tree with a specific agent type",
            parameters={
                "type": "object",
                "properties": {
                    "task_instruction": {
                        "type": "string",
                        "description": "Clear instruction for the subtask"
                    },
                    "agent_type": {
                        "type": "string",
                        "description": "Name of the agent type to handle this subtask"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority level (0-10, higher is more important)",
                        "default": 0
                    },
                    "max_execution_time": {
                        "type": "integer", 
                        "description": "Maximum execution time in seconds",
                        "default": 300
                    }
                },
                "required": ["task_instruction", "agent_type"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        task_instruction = kwargs.get("task_instruction")
        agent_type = kwargs.get("agent_type")
        priority = kwargs.get("priority", 0)
        max_execution_time = kwargs.get("max_execution_time", 300)
        
        # TODO: Implement actual subtask creation
        # This requires access to the current task context
        
        return MCPToolResult(
            success=True,
            result=f"Subtask created for agent '{agent_type}': {task_instruction[:100]}...",
            metadata={
                "tool_name": "start_subtask",
                "agent_type": agent_type,
                "priority": priority,
                "max_execution_time": max_execution_time,
                "action": "create_subtask"
            }
        )


class RequestContextTool(CoreMCPTool):
    """Spawn context addition agent"""
    
    def __init__(self):
        super().__init__(
            name="request_context",
            description="Request additional context documents by spawning a context addition agent",
            parameters={
                "type": "object",
                "properties": {
                    "context_needed": {
                        "type": "string",
                        "description": "Description of what additional context is needed"
                    },
                    "context_type": {
                        "type": "string",
                        "description": "Type of context needed (e.g., 'technical_docs', 'process_guide', 'reference')",
                        "default": "general"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "How urgently the context is needed",
                        "default": "medium"
                    }
                },
                "required": ["context_needed"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        context_needed = kwargs.get("context_needed")
        context_type = kwargs.get("context_type", "general")
        urgency = kwargs.get("urgency", "medium")
        
        # TODO: Implement actual context addition agent spawning
        
        return MCPToolResult(
            success=True,
            result=f"Context request submitted: {context_needed}",
            metadata={
                "tool_name": "request_context",
                "context_needed": context_needed,
                "context_type": context_type,
                "urgency": urgency,
                "action": "spawn_context_agent"
            }
        )


class RequestToolsTool(CoreMCPTool):
    """Spawn tool discovery/creation agent"""
    
    def __init__(self):
        super().__init__(
            name="request_tools",
            description="Request additional tools by spawning a tool addition agent",
            parameters={
                "type": "object",
                "properties": {
                    "tools_needed": {
                        "type": "string",
                        "description": "Description of what tools are needed"
                    },
                    "tool_category": {
                        "type": "string",
                        "description": "Category of tools needed (e.g., 'file_ops', 'api_calls', 'data_processing')",
                        "default": "general"
                    },
                    "search_external": {
                        "type": "boolean",
                        "description": "Whether to search for external tools/libraries",
                        "default": true
                    }
                },
                "required": ["tools_needed"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        tools_needed = kwargs.get("tools_needed")
        tool_category = kwargs.get("tool_category", "general")
        search_external = kwargs.get("search_external", True)
        
        # TODO: Implement actual tool addition agent spawning
        
        return MCPToolResult(
            success=True,
            result=f"Tool request submitted: {tools_needed}",
            metadata={
                "tool_name": "request_tools",
                "tools_needed": tools_needed,
                "tool_category": tool_category,
                "search_external": search_external,
                "action": "spawn_tool_agent"
            }
        )


class EndTaskTool(CoreMCPTool):
    """Mark task complete (success/failure)"""
    
    def __init__(self):
        super().__init__(
            name="end_task",
            description="Mark the current task as complete and trigger evaluation/documentation",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "failure"],
                        "description": "Whether the task completed successfully"
                    },
                    "result": {
                        "type": "string",
                        "description": "Detailed result of the task execution"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Concise summary for the parent agent"
                    },
                    "lessons_learned": {
                        "type": "string",
                        "description": "Any important lessons or insights from this task"
                    }
                },
                "required": ["status", "result"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        status = kwargs.get("status")
        result = kwargs.get("result")
        summary = kwargs.get("summary", "")
        lessons_learned = kwargs.get("lessons_learned", "")
        
        # TODO: Implement actual task completion logic
        # This should:
        # 1. Update task status in database
        # 2. Trigger evaluator agent
        # 3. Trigger documentation agent
        # 4. Create summary for parent agent
        
        task_status = TaskStatus.COMPLETE if status == "success" else TaskStatus.FAILED
        
        return MCPToolResult(
            success=True,
            result=f"Task marked as {status}: {result[:100]}...",
            metadata={
                "tool_name": "end_task",
                "task_status": task_status.value,
                "summary": summary,
                "lessons_learned": lessons_learned,
                "action": "complete_task"
            }
        )


class FlagForReviewTool(CoreMCPTool):
    """Queue item for manual review"""
    
    def __init__(self):
        super().__init__(
            name="flag_for_review",
            description="Flag an issue or decision for manual human review",
            parameters={
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Description of the issue that needs review"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Severity level of the issue",
                        "default": "medium"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the issue (e.g., 'safety', 'decision', 'error', 'improvement')",
                        "default": "general"
                    },
                    "blocking": {
                        "type": "boolean",
                        "description": "Whether this issue blocks further progress",
                        "default": false
                    }
                },
                "required": ["issue"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        issue = kwargs.get("issue")
        severity = kwargs.get("severity", "medium")
        category = kwargs.get("category", "general")
        blocking = kwargs.get("blocking", False)
        
        # TODO: Implement actual review queue system
        # This should add the item to a review queue for human inspection
        
        return MCPToolResult(
            success=True,
            result=f"Issue flagged for review ({severity}): {issue[:100]}...",
            metadata={
                "tool_name": "flag_for_review",
                "severity": severity,
                "category": category,
                "blocking": blocking,
                "action": "add_to_review_queue"
            }
        )


class ThinkOutLoudTool(CoreMCPTool):
    """Log reasoning and planning thoughts"""
    
    def __init__(self):
        super().__init__(
            name="think_out_loud",
            description="Log reasoning, planning thoughts, and decision-making process",
            parameters={
                "type": "object",
                "properties": {
                    "thoughts": {
                        "type": "string",
                        "description": "The agent's reasoning, planning, or thought process"
                    },
                    "thought_type": {
                        "type": "string",
                        "enum": ["planning", "reasoning", "decision", "observation", "reflection"],
                        "description": "Type of thought being logged",
                        "default": "reasoning"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence level in this reasoning (0-1)",
                        "default": 0.5
                    }
                },
                "required": ["thoughts"]
            }
        )
    
    async def execute(self, **kwargs) -> MCPToolResult:
        thoughts = kwargs.get("thoughts")
        thought_type = kwargs.get("thought_type", "reasoning")
        confidence = kwargs.get("confidence", 0.5)
        
        # TODO: Implement actual thought logging
        # This should log the thoughts to the message history with special formatting
        
        return MCPToolResult(
            success=True,
            result=f"Logged {thought_type}: {thoughts[:100]}...",
            metadata={
                "tool_name": "think_out_loud",
                "thought_type": thought_type,
                "confidence": confidence,
                "action": "log_thoughts"
            }
        )


# Register all core tools
def register_core_tools(registry):
    """Register all core MCP tools with the registry"""
    core_tools = [
        BreakDownTaskTool(),
        StartSubtaskTool(),
        RequestContextTool(),
        RequestToolsTool(),
        EndTaskTool(),
        FlagForReviewTool(),
        ThinkOutLoudTool()
    ]
    
    for tool in core_tools:
        registry.register_tool(tool, "core")
    
    return core_tools