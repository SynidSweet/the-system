"""The Neutral Task Process - Process-First implementation for tasks."""

from typing import Dict, Any, Optional
import logging

from agent_system.core.processes.base_process import BaseProcess, ProcessResult
from agent_system.core.runtime.state_machine import TaskState


logger = logging.getLogger(__name__)


class NeutralTaskProcess(BaseProcess):
    """Process-first task process that ensures systematic framework establishment before execution.
    
    This process follows the process-first architecture:
    1. Process Discovery - ALWAYS establish systematic framework first
    2. Framework Validation - Ensure complete systematic structure exists
    3. Agent selection - determines optimal agent within framework
    4. Context assignment - framework-driven context provision
    5. Tool assignment - framework-appropriate tool selection
    6. Task preparation - prepares task for systematic execution
    """
    
    async def execute(self, task_id: int, **kwargs) -> ProcessResult:
        """Execute the process-first neutral task process."""
        try:
            task = await self.sys.get_task(task_id)
            if not task:
                return ProcessResult(
                    status="failure",
                    data={},
                    error=f"Task {task_id} not found"
                )
            
            logger.info(f"Starting Process-First NeutralTaskProcess for task {task_id}: {task.instruction}")
            
            # PHASE 1: PROCESS DISCOVERY AND ESTABLISHMENT (ALWAYS FIRST)
            # Check if task already has systematic framework established
            task_metadata = task.metadata or {}
            if not task_metadata.get("systematic_framework_id"):
                logger.info(f"No systematic framework found for task {task_id} - initiating process discovery")
                
                process_discovery_task_id = await self.sys.create_subtask(
                    parent_id=task_id,
                    instruction=f"Analyze and establish all necessary processes for: {task.instruction}",
                    assigned_agent="process_discovery",
                    additional_context=["process_discovery_guide", "process_framework_guide"],
                    process="process_discovery_process"
                )
                
                # Wait for process discovery to complete
                results = await self.sys.wait_for_tasks([process_discovery_task_id])
                if not results or results[0].status != "success":
                    return ProcessResult(
                        status="failure",
                        data={},
                        error="Process discovery and framework establishment failed"
                    )
                
                process_result = results[0].data
                
                # Update task with framework information
                await self.sys.update_task(
                    task_id,
                    metadata={
                        **task_metadata,
                        "systematic_framework_id": process_result.get("framework_id"),
                        "domain_type": process_result.get("domain_type"),
                        "isolation_capability": process_result.get("isolated_task_success_enabled", False)
                    }
                )
                
                # Add framework documentation to context
                framework_docs = process_result.get("framework_documentation", [])
                if framework_docs:
                    await self.sys.add_context_to_task(task_id, framework_docs)
                
                logger.info(f"Systematic framework established for task {task_id}: {process_result.get('domain_type')}")
            
            # PHASE 2: FRAMEWORK VALIDATION (ensure framework is complete)
            framework_id = task.metadata.get("systematic_framework_id") if task.metadata else None
            if framework_id:
                validation_result = await self._validate_framework_completeness(task_id, framework_id)
                if not validation_result.get("complete"):
                    logger.warning(f"Framework {framework_id} incomplete - enhancing")
                    # Could trigger framework enhancement here if needed
            
            # PHASE 3: FRAMEWORK-DRIVEN AGENT SELECTION
            if not task.assigned_agent:
                # Agent selection within systematic framework
                agent_result = await self._select_agent_with_framework(task_id, task, framework_id)
                if agent_result.status != "success":
                    return agent_result
                
                selected_agent = agent_result.data.get("agent_type")
                await self.sys.update_task(task_id, assigned_agent=selected_agent)
                logger.info(f"Selected agent '{selected_agent}' for task {task_id} within framework")
            
            # PHASE 4: FRAMEWORK-DRIVEN CONTEXT ASSIGNMENT
            if await self._needs_framework_context(task, framework_id):
                context_result = await self._assign_framework_context(task_id, task, framework_id)
                if context_result.status == "success" and context_result.data.get("context_added"):
                    logger.info(f"Added framework-driven context documents to task {task_id}")
            
            # PHASE 5: FRAMEWORK-APPROPRIATE TOOL ASSIGNMENT
            if await self._needs_framework_tools(task, framework_id):
                tool_result = await self._assign_framework_tools(task_id, task, framework_id)
                if tool_result.status == "success" and tool_result.data.get("tools_added"):
                    logger.info(f"Added framework-appropriate tools to task {task_id}")
            
            # PHASE 6: VALIDATE ISOLATED TASK SUCCESS CAPABILITY
            isolation_validation = await self._validate_isolation_capability(task_id, task, framework_id)
            if not isolation_validation.get("can_succeed_in_isolation"):
                logger.warning(f"Task {task_id} cannot succeed in isolation - enhancing context")
                # Could enhance isolation capability here
            
            # Mark ready for agent - Runtime will handle systematic LLM calls
            await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
            
            return ProcessResult(
                status="success",
                data={
                    "task_prepared": True,
                    "systematic_framework_established": True,
                    "framework_id": framework_id,
                    "domain_type": task_metadata.get("domain_type"),
                    "agent_assigned": task.assigned_agent or "pre-assigned",
                    "context_count": len(task.additional_context),
                    "tool_count": len(task.additional_tools),
                    "isolation_capability": isolation_validation.get("can_succeed_in_isolation", False)
                }
            )
            
        except Exception as e:
            return await self.handle_error(e, task_id=task_id)
    
    async def _validate_framework_completeness(self, task_id: int, framework_id: str) -> Dict[str, Any]:
        """Validate that the systematic framework is complete."""
        # In a full implementation, this would query the framework and validate completeness
        # For now, return assumed complete
        return {"complete": True, "framework_id": framework_id}
    
    async def _select_agent_with_framework(self, task_id: int, task, framework_id: str) -> ProcessResult:
        """Select optimal agent within systematic framework constraints."""
        # Create subtask for framework-aware agent selection
        selector_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Select optimal agent within framework {framework_id} for: {task.instruction}",
            assigned_agent="agent_selector",
            additional_context=["agent_capabilities_reference", "agent_selector_guide", "systematic_framework_guide"],
            process="agent_selection_process",
            metadata={
                "systematic_framework_id": framework_id,
                "framework_constraints": True
            }
        )
        
        # Wait for agent selection
        results = await self.sys.wait_for_tasks([selector_task_id])
        if not results or results[0].status != "success":
            return ProcessResult(
                status="failure",
                data={},
                error="Framework-driven agent selection failed"
            )
        
        selected_agent = results[0].data.get("selected_agent", "planning_agent")
        
        return ProcessResult(
            status="success",
            data={"agent_type": selected_agent}
        )
    
    async def _needs_framework_context(self, task, framework_id: str) -> bool:
        """Determine if task needs framework-driven context analysis."""
        # Framework-aware context needs
        if task.additional_context and len(task.additional_context) > 2:
            return False  # Already has sufficient context
        
        # Always analyze context needs within systematic framework
        return True
    
    async def _assign_framework_context(self, task_id: int, task, framework_id: str) -> ProcessResult:
        """Assign framework-appropriate context documents to the task."""
        # Create framework-aware context analysis subtask
        context_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Determine systematic context needs within framework {framework_id} for agent {task.assigned_agent} on: {task.instruction}",
            assigned_agent="context_addition",
            additional_context=["context_addition_guide", "systematic_framework_context_guide"],
            process="context_analysis_process",
            metadata={
                "systematic_framework_id": framework_id,
                "isolation_requirements": True
            }
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
                "documents": context_docs,
                "framework_compliant": True
            }
        )
    
    async def _needs_framework_tools(self, task, framework_id: str) -> bool:
        """Determine if task needs framework-appropriate tool analysis."""
        # Framework-aware tool needs
        if task.additional_tools and len(task.additional_tools) > 3:
            return False  # Already has sufficient tools
        
        # Always analyze tool needs within systematic framework
        return True
    
    async def _assign_framework_tools(self, task_id: int, task, framework_id: str) -> ProcessResult:
        """Assign framework-appropriate tools to the task."""
        # Create framework-aware tool analysis subtask
        tool_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Determine systematic tool needs within framework {framework_id} for agent {task.assigned_agent} on: {task.instruction}",
            assigned_agent="tool_addition",
            additional_context=["tool_addition_guide", "systematic_framework_tool_guide"],
            process="tool_analysis_process",
            metadata={
                "systematic_framework_id": framework_id,
                "framework_boundaries": True
            }
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
                "tools": tools,
                "framework_compliant": True
            }
        )
    
    async def _validate_isolation_capability(self, task_id: int, task, framework_id: str) -> Dict[str, Any]:
        """Validate that task can succeed in isolation within framework."""
        # Check if task has sufficient context and tools for isolated success
        has_framework = bool(framework_id)
        has_context = len(task.additional_context) > 0
        has_tools = len(task.additional_tools) > 0
        has_agent = bool(task.assigned_agent)
        
        can_succeed = has_framework and has_context and has_agent
        
        return {
            "can_succeed_in_isolation": can_succeed,
            "has_framework": has_framework,
            "has_context": has_context,
            "has_tools": has_tools,
            "has_agent": has_agent,
            "framework_id": framework_id
        }
    
    async def validate_parameters(self, task_id: int = None, **kwargs) -> bool:
        """Validate process parameters."""
        if task_id is None:
            logger.error("NeutralTaskProcess requires task_id parameter")
            return False
        return True