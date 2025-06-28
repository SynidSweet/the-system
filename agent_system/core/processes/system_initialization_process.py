"""
System Initialization Process

Orchestrates the complete system initialization sequence including knowledge bootstrap
and framework establishment. This process ensures the system is properly initialized
before autonomous operation.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..base_process import BaseProcess
from ..system_interface import SystemInterface
from ..entities import TaskEntity, TaskState

# Type aliases for backward compatibility
Task = TaskEntity
TaskStatus = TaskState
from ..knowledge.bootstrap import bootstrap_knowledge_system
from ..initialization_tasks import get_initialization_tasks, get_tasks_by_phase, get_phase_descriptions

logger = logging.getLogger(__name__)


class SystemInitializationProcess(BaseProcess):
    """
    Process for system initialization including knowledge bootstrap and framework establishment.
    
    This process:
    1. Bootstraps the knowledge system from documentation
    2. Executes initialization tasks in phases
    3. Validates system readiness
    4. Enables autonomous operation
    """
    
    def __init__(self, system: SystemInterface):
        super().__init__(system, "system_initialization_process")
        self.initialization_tasks = get_initialization_tasks()
        self.phase_descriptions = get_phase_descriptions()
        self.current_phase = 1
        self.completed_tasks = []
    
    async def execute(self, task_id: int, task: Task) -> Dict[str, Any]:
        """Execute the system initialization process."""
        try:
            await self.sys.log(task_id, "system", "Starting system initialization process")
            
            # Phase 0: Knowledge Bootstrap (Special handling)
            await self.sys.log(task_id, "system", "Phase 0: Bootstrapping knowledge system")
            bootstrap_success = await self._bootstrap_knowledge_system(task_id)
            
            if not bootstrap_success:
                return {
                    "status": "failed",
                    "error": "Knowledge bootstrap failed",
                    "phase": 0
                }
            
            # Execute initialization phases
            for phase in range(1, 5):
                await self.sys.log(task_id, "system", f"Phase {phase}: {self.phase_descriptions[phase]}")
                
                phase_success = await self._execute_phase(task_id, phase)
                
                if not phase_success:
                    return {
                        "status": "failed",
                        "error": f"Phase {phase} failed",
                        "phase": phase,
                        "completed_tasks": self.completed_tasks
                    }
            
            # Final validation
            await self.sys.log(task_id, "system", "Performing final system validation")
            validation_result = await self._validate_system_readiness(task_id)
            
            if validation_result["ready"]:
                await self.sys.log(task_id, "system", "System initialization complete! Ready for autonomous operation.")
                
                return {
                    "status": "completed",
                    "message": "System successfully initialized",
                    "completed_tasks": self.completed_tasks,
                    "validation": validation_result
                }
            else:
                return {
                    "status": "failed",
                    "error": "System validation failed",
                    "validation": validation_result,
                    "completed_tasks": self.completed_tasks
                }
                
        except Exception as e:
            logger.error(f"System initialization error: {e}")
            await self.sys.log(task_id, "error", f"System initialization failed: {str(e)}")
            
            return {
                "status": "failed",
                "error": str(e),
                "phase": self.current_phase,
                "completed_tasks": self.completed_tasks
            }
    
    async def _bootstrap_knowledge_system(self, task_id: int) -> bool:
        """Bootstrap the knowledge system from documentation."""
        try:
            await self.sys.log(task_id, "system", "Converting documentation to knowledge entities...")
            
            # Check if knowledge already exists
            knowledge_dir = Path("knowledge")
            if knowledge_dir.exists() and any(knowledge_dir.iterdir()):
                await self.sys.log(task_id, "system", "Knowledge base already exists, skipping bootstrap")
                return True
            
            # Run the bootstrap conversion
            results = bootstrap_knowledge_system(
                docs_dir=".",
                knowledge_dir="knowledge"
            )
            
            await self.sys.log(
                task_id, 
                "system", 
                f"Knowledge bootstrap complete: {results['converted']} entities created"
            )
            
            if results['failed'] > 0:
                await self.sys.log(
                    task_id,
                    "warning",
                    f"Some conversions failed: {results['failed']} files"
                )
            
            # Log to event system
            await self.sys.log_event(
                "knowledge_bootstrap_complete",
                "system",
                0,
                {
                    "entities_created": results['converted'],
                    "failed_conversions": results['failed']
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Knowledge bootstrap error: {e}")
            await self.sys.log(task_id, "error", f"Knowledge bootstrap failed: {str(e)}")
            return False
    
    async def _execute_phase(self, task_id: int, phase: int) -> bool:
        """Execute all tasks in a specific phase."""
        phase_tasks = get_tasks_by_phase(phase)
        
        await self.sys.log(
            task_id,
            "system",
            f"Executing {len(phase_tasks)} tasks in phase {phase}"
        )
        
        for init_task in phase_tasks:
            # Check dependencies
            if not await self._check_dependencies(task_id, init_task.dependencies):
                await self.sys.log(
                    task_id,
                    "error",
                    f"Dependencies not met for task {init_task.task_id}"
                )
                return False
            
            # Create subtask for this initialization task
            subtask_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=init_task.instruction,
                assigned_agent=init_task.agent_type,
                additional_context=init_task.context,
                process=init_task.process,
                metadata={
                    "init_task_id": init_task.task_id,
                    "init_task_name": init_task.name,
                    "phase": phase,
                    "deliverables": init_task.deliverables,
                    "success_criteria": init_task.success_criteria
                }
            )
            
            await self.sys.log(
                task_id,
                "system",
                f"Created subtask {subtask_id} for {init_task.name}"
            )
            
            # Wait for subtask completion
            subtask_result = await self._wait_for_subtask(subtask_id)
            
            if subtask_result["status"] != "completed":
                await self.sys.log(
                    task_id,
                    "error",
                    f"Initialization task {init_task.task_id} failed"
                )
                return False
            
            # Mark task as completed
            self.completed_tasks.append(init_task.task_id)
            
            # Log completion
            await self.sys.log_event(
                "initialization_task_complete",
                "task",
                subtask_id,
                {
                    "init_task_id": init_task.task_id,
                    "phase": phase,
                    "name": init_task.name
                }
            )
        
        await self.sys.log(
            task_id,
            "system",
            f"Phase {phase} completed successfully"
        )
        
        return True
    
    async def _check_dependencies(self, task_id: int, dependencies: List[str]) -> bool:
        """Check if all dependencies are satisfied."""
        for dep in dependencies:
            if dep not in self.completed_tasks:
                await self.sys.log(
                    task_id,
                    "system",
                    f"Dependency {dep} not satisfied"
                )
                return False
        return True
    
    async def _wait_for_subtask(self, subtask_id: int, timeout: int = 3600) -> Dict[str, Any]:
        """Wait for a subtask to complete with timeout."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check task status
            subtask = await self.sys.get_task(subtask_id)
            
            if subtask.status in ["completed", "failed"]:
                return {
                    "status": subtask.status,
                    "result": subtask.result
                }
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                await self.sys.log(
                    subtask_id,
                    "error",
                    f"Subtask {subtask_id} timed out"
                )
                return {
                    "status": "failed",
                    "error": "timeout"
                }
            
            # Wait before checking again
            await asyncio.sleep(5)
    
    async def _validate_system_readiness(self, task_id: int) -> Dict[str, Any]:
        """Validate that the system is ready for autonomous operation."""
        validation_results = {
            "ready": True,
            "checks": {}
        }
        
        # Check 1: Knowledge base exists
        knowledge_dir = Path("knowledge")
        has_knowledge = knowledge_dir.exists() and any(knowledge_dir.iterdir())
        validation_results["checks"]["knowledge_base"] = has_knowledge
        if not has_knowledge:
            validation_results["ready"] = False
        
        # Check 2: All core agents exist
        agents = await self.sys.list_agents()
        has_all_agents = len(agents) >= 9
        validation_results["checks"]["core_agents"] = {
            "expected": 9,
            "actual": len(agents),
            "valid": has_all_agents
        }
        if not has_all_agents:
            validation_results["ready"] = False
        
        # Check 3: All initialization tasks completed
        all_tasks_complete = len(self.completed_tasks) == len(self.initialization_tasks)
        validation_results["checks"]["initialization_tasks"] = {
            "expected": len(self.initialization_tasks),
            "completed": len(self.completed_tasks),
            "valid": all_tasks_complete
        }
        if not all_tasks_complete:
            validation_results["ready"] = False
        
        # Check 4: Core processes exist
        processes = await self.sys.query_database(
            "SELECT name FROM processes WHERE status = 'active'"
        )
        has_processes = len(processes) > 0
        validation_results["checks"]["processes"] = has_processes
        if not has_processes:
            validation_results["ready"] = False
        
        # Check 5: System can execute tasks
        test_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction="Test system readiness with simple calculation: 2 + 2",
            assigned_agent="agent_selector"
        )
        
        test_result = await self._wait_for_subtask(test_task_id, timeout=60)
        can_execute = test_result["status"] == "completed"
        validation_results["checks"]["task_execution"] = can_execute
        if not can_execute:
            validation_results["ready"] = False
        
        await self.sys.log(
            task_id,
            "system",
            f"System validation complete: {'READY' if validation_results['ready'] else 'NOT READY'}"
        )
        
        return validation_results