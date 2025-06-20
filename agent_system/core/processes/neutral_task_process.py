"""The Neutral Task Process - Default process for tasks without assigned processes."""

from typing import Dict, Any, Optional
import logging

from agent_system.core.processes.base import BaseProcess, ProcessResult
from agent_system.core.runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class NeutralTaskProcess(BaseProcess):
    """Default process applied to tasks that don't have a specific process assigned.
    
    This process handles:
    1. Agent selection - determines optimal agent for the task
    2. Context assignment - identifies needed context documents
    3. Tool assignment - determines required tools
    4. Task preparation - prepares task for agent execution
    """
    
    async def execute(self, task_id: int, **kwargs) -> ProcessResult:
        """Execute the neutral task process."""
        try:
            task = await self.sys.get_task(task_id)
            if not task:
                return ProcessResult(
                    status="failure",
                    data={},
                    error=f"Task {task_id} not found"
                )
            
            logger.info(f"Starting NeutralTaskProcess for task {task_id}: {task.instruction}")
            
            # Skip if task already has agent assigned (pre-assigned scenario)
            if not task.assigned_agent:
                # 1. Agent Selection - create subtask for this
                agent_result = await self._select_agent(task_id, task)
                if agent_result.status != "success":
                    return agent_result
                
                selected_agent = agent_result.data.get("agent_type")
                await self.sys.update_task(task_id, assigned_agent=selected_agent)
                logger.info(f"Selected agent '{selected_agent}' for task {task_id}")
            
            # 2. Context Assignment - create subtask if needed
            if await self._needs_context_analysis(task):
                context_result = await self._assign_context(task_id, task)
                if context_result.status == "success" and context_result.data.get("context_added"):
                    logger.info(f"Added context documents to task {task_id}")
            
            # 3. Tool Assignment - similar pattern
            if await self._needs_tool_analysis(task):
                tool_result = await self._assign_tools(task_id, task)
                if tool_result.status == "success" and tool_result.data.get("tools_added"):
                    logger.info(f"Added tools to task {task_id}")
            
            # 4. Mark ready for agent - Runtime will handle LLM calls
            await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
            
            return ProcessResult(
                status="success",
                data={
                    "task_prepared": True,
                    "agent_assigned": task.assigned_agent or "pre-assigned",
                    "context_count": len(task.additional_context),
                    "tool_count": len(task.additional_tools)
                }
            )
            
        except Exception as e:
            return await self.handle_error(e, task_id=task_id)
    
    async def _select_agent(self, task_id: int, task) -> ProcessResult:
        """Select optimal agent for the task."""
        # Create subtask for agent selection
        selector_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Select optimal agent for: {task.instruction}",
            assigned_agent="agent_selector",
            additional_context=["agent_capabilities_reference", "agent_selector_guide"],
            process="agent_selection_process"
        )
        
        # Wait for agent selection
        results = await self.sys.wait_for_tasks([selector_task_id])
        if not results or results[0].status != "success":
            return ProcessResult(
                status="failure",
                data={},
                error="Agent selection failed"
            )
        
        selected_agent = results[0].data.get("selected_agent", "task_breakdown")
        
        return ProcessResult(
            status="success",
            data={"agent_type": selected_agent}
        )
    
    async def _needs_context_analysis(self, task) -> bool:
        """Determine if task needs context analysis."""
        # Simple heuristics for now
        if task.additional_context:
            return False  # Already has context
        
        # Check if task mentions specific domains or technologies
        keywords = ["api", "database", "frontend", "backend", "algorithm", "design"]
        instruction_lower = task.instruction.lower()
        
        return any(keyword in instruction_lower for keyword in keywords)
    
    async def _assign_context(self, task_id: int, task) -> ProcessResult:
        """Assign context documents to the task."""
        # Create context analysis subtask
        context_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Determine context needs for agent {task.assigned_agent} on: {task.instruction}",
            assigned_agent="context_addition",
            additional_context=["context_addition_guide"],
            process="context_analysis_process"
        )
        
        # Wait for context analysis
        results = await self.sys.wait_for_tasks([context_task_id])
        if not results or results[0].status != "success":
            return ProcessResult(
                status="success",  # Not critical failure
                data={"context_added": False}
            )
        
        context_docs = results[0].data.get("context_documents", [])
        if context_docs:
            await self.sys.add_context_to_task(task_id, context_docs)
            
        return ProcessResult(
            status="success",
            data={
                "context_added": bool(context_docs),
                "documents": context_docs
            }
        )
    
    async def _needs_tool_analysis(self, task) -> bool:
        """Determine if task needs tool analysis."""
        # Simple heuristics
        if task.additional_tools:
            return False  # Already has tools
        
        # Check if task mentions actions that might need tools
        action_keywords = ["create", "generate", "analyze", "search", "fetch", "query", "execute"]
        instruction_lower = task.instruction.lower()
        
        return any(keyword in instruction_lower for keyword in action_keywords)
    
    async def _assign_tools(self, task_id: int, task) -> ProcessResult:
        """Assign tools to the task."""
        # Create tool analysis subtask
        tool_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Determine tool needs for agent {task.assigned_agent} on: {task.instruction}",
            assigned_agent="tool_addition",
            additional_context=["tool_addition_guide"],
            process="tool_analysis_process"
        )
        
        # Wait for tool analysis
        results = await self.sys.wait_for_tasks([tool_task_id])
        if not results or results[0].status != "success":
            return ProcessResult(
                status="success",  # Not critical failure
                data={"tools_added": False}
            )
        
        tools = results[0].data.get("tools", [])
        if tools:
            await self.sys.add_tools_to_task(task_id, tools)
            
        return ProcessResult(
            status="success",
            data={
                "tools_added": bool(tools),
                "tools": tools
            }
        )
    
    async def validate_parameters(self, task_id: int = None, **kwargs) -> bool:
        """Validate process parameters."""
        if task_id is None:
            logger.error("NeutralTaskProcess requires task_id parameter")
            return False
        return True