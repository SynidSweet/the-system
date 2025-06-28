"""Integration module to connect the new runtime engine with existing systems."""

import asyncio
from typing import Optional, Dict, Any
import logging

from ..runtime.engine import RuntimeEngine, RuntimeSettings
from ..runtime.state_machine import TaskState
from ..processes.process_registry import ProcessRegistry, initialize_process_registry
from ..events.event_manager import EventManager
from ..entities.entity_manager import EntityManager
from ..events.event_types import EntityType


logger = logging.getLogger(__name__)


class RuntimeIntegration:
    """Manages integration between new runtime and existing systems."""
    
    def __init__(
        self,
        event_manager: EventManager,
        entity_manager: EntityManager,
        mode: str = "parallel"  # parallel, runtime_first, legacy_first
    ):
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.mode = mode
        
        # Initialize components
        self.runtime_engine: Optional[RuntimeEngine] = None
        self.process_registry: Optional[ProcessRegistry] = None
        
        # Track migration status
        self.tasks_using_runtime = 0
        self.total_tasks = 0
    
    async def initialize(self):
        """Initialize the runtime system."""
        logger.info(f"Initializing runtime integration in {self.mode} mode")
        
        # Initialize process registry
        self.process_registry = initialize_process_registry(
            self.entity_manager,
            self.event_manager
        )
        
        # Initialize runtime engine
        settings = RuntimeSettings(
            max_concurrent_agents=5,
            manual_stepping_enabled=False,
            auto_trigger_enabled=True
        )
        
        self.runtime_engine = RuntimeEngine(
            self.event_manager,
            self.entity_manager,
            settings
        )
        
        # Start runtime engine
        await self.runtime_engine.start()
        
        logger.info("Runtime integration initialized successfully")
    
    async def shutdown(self):
        """Shutdown the runtime system."""
        if self.runtime_engine:
            await self.runtime_engine.stop()
    
    async def create_task(
        self,
        instruction: str,
        parent_task_id: Optional[int] = None,
        **kwargs
    ) -> int:
        """Create a task using the new runtime engine."""
        self.total_tasks += 1
        self.tasks_using_runtime += 1
        
        if not self.runtime_engine:
            raise RuntimeError("Runtime engine not initialized")
        
        # Always use new runtime
        task_id = await self.runtime_engine.create_task(
            instruction=instruction,
            parent_task_id=parent_task_id,
            **kwargs
        )
        
        logger.info(f"Created task {task_id} using runtime engine")
        return task_id
    
    # Backward compatibility alias
    async def create_task_with_runtime(self, *args, **kwargs) -> int:
        """Deprecated - use create_task instead."""
        return await self.create_task(*args, **kwargs)
    
    def _should_use_runtime(self) -> bool:
        """Always use runtime - legacy mode is deprecated."""
        return True
    
    async def handle_tool_call(
        self,
        task_id: int,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a tool call, potentially triggering a process or MCP tool."""
        # Check if this is an MCP tool call (format: "server.operation")
        if "." in tool_name:
            server_name, operation = tool_name.split(".", 1)
            
            # Get tool system manager if available
            from ...tools.mcp_servers.startup import get_tool_system_manager
            tool_system = get_tool_system_manager()
            
            if tool_system:
                try:
                    # Get agent type from task
                    from .task import TaskEntity
                    task = await self.entity_manager.get_entity(EntityType.TASK, task_id)
                    agent_type = task.metadata.get("agent_type", "unknown") if task else "unknown"
                    
                    # Call MCP tool
                    result = await tool_system.call_tool(
                        tool_name=server_name,
                        operation=operation,
                        parameters=tool_args,
                        agent_type=agent_type,
                        task_id=task_id
                    )
                    
                    return {
                        "status": "mcp_tool_executed",
                        "server": server_name,
                        "operation": operation,
                        "result": result
                    }
                except Exception as e:
                    logger.error(f"MCP tool call failed: {e}")
                    return {
                        "status": "error",
                        "error": str(e)
                    }
        
        # Map tool names to process names
        tool_process_map = {
            "break_down_task": "break_down_task_process",
            "start_subtask": "create_subtask_process",
            "create_subtask": "create_subtask_process",
            "end_task": "end_task_process",
            "request_context": "need_more_context_process",
            "need_more_context": "need_more_context_process",
            "need_more_tools": "need_more_tools_process",
            # Future processes can be added here
            # "flag_for_review": "flag_for_review_process"
        }
        
        process_name = tool_process_map.get(tool_name)
        
        if process_name and self.process_registry:
            # Execute process
            logger.info(f"Executing process {process_name} for tool {tool_name}")
            
            # Prepare process parameters
            process_params = {
                "parent_task_id": task_id,
                **tool_args
            }
            
            # Special parameter mapping for different tools
            if tool_name == "break_down_task":
                process_params["breakdown_request"] = tool_args.get("approach", "")
            elif tool_name in ["start_subtask", "create_subtask"]:
                process_params["subtask_instruction"] = tool_args.get("instruction", "")
            elif tool_name == "end_task":
                process_params["task_id"] = task_id
                process_params["result"] = tool_args.get("result", {})
            elif tool_name in ["request_context", "need_more_context"]:
                process_params["requesting_task_id"] = task_id
                process_params["context_request"] = tool_args.get("request", "")
            elif tool_name == "need_more_tools":
                process_params["requesting_task_id"] = task_id
                process_params["tool_request"] = tool_args.get("tool_request", "")
                process_params["justification"] = tool_args.get("justification", "")
            # Future tool parameter mappings can be added here
            # elif tool_name == "flag_for_review":
            #     process_params["flagging_task_id"] = task_id
            #     process_params["flag_reason"] = tool_args.get("reason", "")
            #     process_params["severity"] = tool_args.get("severity", "normal")
            
            # Execute the process
            result = await self.process_registry.execute_process(
                process_name,
                **process_params
            )
            
            return {
                "status": "process_executed",
                "process": process_name,
                "result": result
            }
        else:
            # Regular tool execution
            return {
                "status": "tool_executed",
                "tool": tool_name,
                "result": f"Tool {tool_name} executed (legacy)"
            }
    
    async def get_runtime_statistics(self) -> Dict[str, Any]:
        """Get statistics about runtime usage."""
        runtime_stats = {}
        if self.runtime_engine:
            runtime_stats = self.runtime_engine.get_statistics()
        
        process_stats = {}
        if self.process_registry:
            process_stats = {
                "registered_processes": len(self.process_registry.list_processes()),
                "processes": self.process_registry.list_processes()
            }
        
        adoption_rate = 0.0
        if self.total_tasks > 0:
            adoption_rate = self.tasks_using_runtime / self.total_tasks
        
        return {
            "runtime_active": self.runtime_engine is not None,
            "mode": self.mode,
            "tasks_using_runtime": self.tasks_using_runtime,
            "total_tasks": self.total_tasks,
            "adoption_rate": adoption_rate,
            "runtime_engine": runtime_stats,
            "process_registry": process_stats
        }
    
    async def migrate_task_to_runtime(self, task_id: int) -> bool:
        """Migrate an existing task to use the runtime engine."""
        if not self.runtime_engine:
            return False
        
        try:
            # Get task from entity manager
            from .task import TaskEntity
            task = await self.entity_manager.get_entity(EntityType.TASK, task_id)
            
            if not task or not isinstance(task, TaskEntity):
                return False
            
            # Add to runtime engine's tracking
            self.runtime_engine.task_states[task_id] = task.task_state
            
            # Add to dependency graph if has dependencies
            if task.dependencies:
                await self.runtime_engine.dependency_graph.add_task(task_id)
                for dep_id in task.dependencies:
                    await self.runtime_engine.dependency_graph.add_dependency(task_id, dep_id)
            
            logger.info(f"Migrated task {task_id} to runtime engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate task {task_id}: {e}")
            return False


# Global runtime integration instance
_runtime_integration: Optional[RuntimeIntegration] = None


async def initialize_runtime_integration(
    event_manager: EventManager,
    entity_manager: EntityManager,
    mode: str = "parallel"
) -> RuntimeIntegration:
    """Initialize the global runtime integration."""
    global _runtime_integration
    
    if _runtime_integration is None:
        _runtime_integration = RuntimeIntegration(
            event_manager,
            entity_manager,
            mode
        )
        await _runtime_integration.initialize()
    
    return _runtime_integration


def get_runtime_integration() -> Optional[RuntimeIntegration]:
    """Get the current runtime integration instance."""
    return _runtime_integration


# Fix missing import
from ..events.event_types import EntityType