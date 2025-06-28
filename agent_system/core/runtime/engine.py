"""Event-driven runtime engine for task execution."""

import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass
import logging

from ..runtime.state_machine import TaskState, TaskStateMachine
from ..runtime.dependency_graph import DependencyGraph
from ..runtime.event_handler import RuntimeEventHandler
from ..events.event_manager import EventManager
from ..events.event_types import EventType, EntityType
from ..entities.entity_manager import EntityManager
from ..entities.task import TaskEntity


logger = logging.getLogger(__name__)


@dataclass
class RuntimeSettings:
    """Runtime engine configuration settings."""
    max_consecutive_calls: int = 10        # Per task tree
    max_concurrent_agents: int = 5         # System-wide
    manual_stepping_enabled: bool = False  # Global manual mode
    auto_trigger_enabled: bool = True      # Auto-progression
    event_processing_interval: float = 0.1 # Event loop interval
    
    # Task-specific limits
    max_task_depth: int = 10              # Maximum task tree depth
    max_subtasks_per_task: int = 20       # Maximum subtasks per parent
    task_timeout: int = 3600              # Task timeout in seconds (1 hour)


@dataclass
class RuntimeEvent:
    """Event for the runtime engine to process."""
    event_type: str
    task_id: int
    data: Dict[str, Any]
    timestamp: float


class RuntimeEngine:
    """Event-driven runtime engine for task execution."""
    
    def __init__(
        self,
        event_manager: EventManager,
        entity_manager: EntityManager,
        settings: Optional[RuntimeSettings] = None
    ):
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.settings = settings or RuntimeSettings()
        
        # Core components
        self.state_machine = TaskStateMachine(event_manager)
        self.dependency_graph = DependencyGraph(event_manager)
        self.event_handler = RuntimeEventHandler(self)
        
        # Runtime state
        self.event_queue: asyncio.Queue[RuntimeEvent] = asyncio.Queue()
        self.active_agents: Dict[int, asyncio.Task] = {}
        self.task_states: Dict[int, TaskState] = {}
        self.task_settings: Dict[int, Dict[str, Any]] = {}
        self.tree_settings: Dict[int, Dict[str, Any]] = {}
        
        # Control flags
        self.running = False
        self._stop_event = asyncio.Event()
        self._main_loop_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the runtime engine."""
        if self.running:
            logger.warning("Runtime engine already running")
            return
        
        logger.info("Starting runtime engine...")
        self.running = True
        self._stop_event.clear()
        
        # Start the main event loop
        self._main_loop_task = asyncio.create_task(self._event_loop())
        
        # Log startup event
        await self.event_manager.log_event(
            EventType.RUNTIME_STARTED,
            EntityType.SYSTEM,
            0,
            settings=self.settings.__dict__
        )
    
    async def stop(self):
        """Stop the runtime engine gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping runtime engine...")
        self.running = False
        self._stop_event.set()
        
        # Cancel all active agent tasks
        for task_id, agent_task in self.active_agents.items():
            if not agent_task.done():
                agent_task.cancel()
        
        # Wait for main loop to finish
        if self._main_loop_task:
            await self._main_loop_task
        
        # Log shutdown event
        await self.event_manager.log_event(
            EventType.RUNTIME_STOPPED,
            EntityType.SYSTEM,
            0
        )
    
    async def _event_loop(self):
        """Main event processing loop."""
        logger.info("Runtime event loop started")
        
        while self.running:
            try:
                # Process events with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=self.settings.event_processing_interval
                )
                
                # Handle the event
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                # Check for tasks that need progression
                await self._check_task_progression()
                
            except Exception as e:
                logger.error(f"Error in event loop: {e}", exc_info=True)
                await self.event_manager.log_event(
                    EventType.RUNTIME_ERROR,
                    EntityType.SYSTEM,
                    0,
                    error=str(e)
                )
        
        logger.info("Runtime event loop stopped")
    
    async def _handle_event(self, event: RuntimeEvent):
        """Handle a runtime event."""
        try:
            await self.event_handler.handle_event(event)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}", exc_info=True)
            await self.event_manager.log_event(
                EventType.EVENT_PROCESSING_FAILED,
                EntityType.TASK,
                event.task_id,
                event_type=event.event_type,
                error=str(e)
            )
    
    async def _check_task_progression(self):
        """Check for tasks that can progress."""
        # Find tasks in READY_FOR_AGENT state
        for task_id, state in self.task_states.items():
            if state == TaskState.READY_FOR_AGENT:
                if task_id not in self.active_agents:
                    await self.trigger_agent_call(task_id)
    
    # Task management methods
    
    async def create_task(
        self,
        instruction: str,
        parent_task_id: Optional[int] = None,
        process: str = "neutral_task",
        **kwargs
    ) -> int:
        """Create a new task and start its execution."""
        # Create task entity
        task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"Task: {instruction[:50]}...",
            instruction=instruction,
            parent_task_id=parent_task_id,
            assigned_process=process,
            task_state=TaskState.CREATED,
            **kwargs
        )
        
        task_id = task.entity_id
        self.task_states[task_id] = TaskState.CREATED
        
        # Add to dependency graph
        await self.dependency_graph.add_task(task_id)
        
        # Queue task creation event
        await self.queue_event(RuntimeEvent(
            event_type="task_created",
            task_id=task_id,
            data={"process": process},
            timestamp=datetime.now().timestamp()
        ))
        
        return task_id
    
    async def update_task_state(
        self,
        task_id: int,
        new_state: TaskState,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update task state through the state machine."""
        current_state = self.task_states.get(task_id, TaskState.CREATED)
        
        # Validate transition
        success = await self.state_machine.transition(
            task_id,
            current_state,
            new_state,
            metadata
        )
        
        if success:
            self.task_states[task_id] = new_state
            
            # Update entity
            task_entity = await self.entity_manager.get_entity(EntityType.TASK, task_id)
            if task_entity:
                await task_entity.update_task_state(new_state)
                await self.entity_manager.update_entity(task_entity)
            
            # Queue state change event
            await self.queue_event(RuntimeEvent(
                event_type="task_state_changed",
                task_id=task_id,
                data={
                    "old_state": current_state.value,
                    "new_state": new_state.value,
                    "metadata": metadata
                },
                timestamp=datetime.now().timestamp()
            ))
        
        return success
    
    async def trigger_agent_call(self, task_id: int):
        """Trigger an LLM call for a task."""
        # Check if already running
        if task_id in self.active_agents:
            logger.warning(f"Agent already active for task {task_id}")
            return
        
        # Check runtime limits
        if not await self._can_make_agent_call(task_id):
            await self.update_task_state(task_id, TaskState.MANUAL_HOLD)
            return
        
        # Check manual stepping
        if await self._is_manual_stepping_enabled(task_id):
            await self.update_task_state(task_id, TaskState.MANUAL_HOLD)
            await self._notify_manual_hold(task_id)
            return
        
        # Update state and trigger call
        await self.update_task_state(task_id, TaskState.AGENT_RESPONDING)
        
        # Create agent execution task
        agent_task = asyncio.create_task(self._execute_agent_call(task_id))
        self.active_agents[task_id] = agent_task
    
    async def _execute_agent_call(self, task_id: int):
        """Execute the actual agent call."""
        try:
            # Import here to avoid circular imports
            from ..universal_agent_runtime import UniversalAgentRuntime
            
            # Create and initialize agent
            agent = UniversalAgentRuntime(task_id, self.event_manager)
            if not await agent.initialize():
                raise RuntimeError(f"Failed to initialize agent for task {task_id}")
            
            # Execute the agent
            result = await agent.execute()
            
            if result.success:
                # Check if task is complete
                if result.task_complete:
                    await self.update_task_state(task_id, TaskState.COMPLETED)
                else:
                    # Task continues - may have created subtasks
                    await self.update_task_state(task_id, TaskState.WAITING_ON_DEPENDENCIES)
            else:
                await self.update_task_state(task_id, TaskState.FAILED)
            
            # Queue agent response event
            await self.queue_event(RuntimeEvent(
                event_type="agent_response_received",
                task_id=task_id,
                data={
                    "success": result.success,
                    "result": result.result,
                    "task_complete": result.task_complete
                },
                timestamp=datetime.now().timestamp()
            ))
            
        except Exception as e:
            logger.error(f"Agent execution failed for task {task_id}: {e}")
            await self.update_task_state(task_id, TaskState.FAILED)
        finally:
            # Remove from active agents
            self.active_agents.pop(task_id, None)
    
    async def add_task_dependency(self, task_id: int, depends_on: int) -> bool:
        """Add a dependency between tasks."""
        success = await self.dependency_graph.add_dependency(task_id, depends_on)
        
        if success:
            # Check if task should wait
            if not await self.dependency_graph.all_dependencies_resolved(task_id):
                await self.update_task_state(task_id, TaskState.WAITING_ON_DEPENDENCIES)
        
        return success
    
    async def add_task_dependencies(self, task_id: int, dependencies: List[int]) -> bool:
        """Add multiple dependencies for a task."""
        success = await self.dependency_graph.add_dependencies(task_id, dependencies)
        
        if success and dependencies:
            # Check if task should wait
            if not await self.dependency_graph.all_dependencies_resolved(task_id):
                await self.update_task_state(task_id, TaskState.WAITING_ON_DEPENDENCIES)
        
        return success
    
    async def complete_task(self, task_id: int, result: Dict[str, Any]) -> List[int]:
        """Mark a task as completed and trigger dependent tasks."""
        # Update state
        await self.update_task_state(task_id, TaskState.COMPLETED)
        
        # Update entity
        task_entity = await self.entity_manager.get_entity(EntityType.TASK, task_id)
        if task_entity:
            await task_entity.complete_with_result(result)
            await self.entity_manager.update_entity(task_entity)
        
        # Mark completed in dependency graph
        ready_tasks = await self.dependency_graph.mark_completed(task_id)
        
        # Queue completion events for ready tasks
        for ready_task_id in ready_tasks:
            await self.queue_event(RuntimeEvent(
                event_type="dependency_resolved",
                task_id=ready_task_id,
                data={"resolved_dependency": task_id},
                timestamp=datetime.now().timestamp()
            ))
        
        return ready_tasks
    
    async def fail_task(self, task_id: int, error: str) -> List[int]:
        """Mark a task as failed and handle affected tasks."""
        # Update state
        await self.update_task_state(task_id, TaskState.FAILED)
        
        # Update entity
        task_entity = await self.entity_manager.get_entity(EntityType.TASK, task_id)
        if task_entity:
            await task_entity.fail_with_error(error)
            await self.entity_manager.update_entity(task_entity)
        
        # Mark failed in dependency graph
        blocked_tasks = await self.dependency_graph.mark_failed(task_id, error)
        
        # Queue failure events for blocked tasks
        for blocked_task_id in blocked_tasks:
            await self.queue_event(RuntimeEvent(
                event_type="dependency_failed",
                task_id=blocked_task_id,
                data={"failed_dependency": task_id, "reason": error},
                timestamp=datetime.now().timestamp()
            ))
        
        return blocked_tasks
    
    # Event queue management
    
    async def queue_event(self, event: RuntimeEvent):
        """Queue an event for processing."""
        await self.event_queue.put(event)
    
    # Runtime control methods
    
    async def _can_make_agent_call(self, task_id: int) -> bool:
        """Check if an agent call is allowed."""
        # Check concurrent agents limit
        if len(self.active_agents) >= self.settings.max_concurrent_agents:
            return False
        
        # Check task-specific limits
        task_settings = self.task_settings.get(task_id, {})
        if "max_agent_calls" in task_settings:
            # Would need to track calls per task
            pass
        
        return True
    
    async def _is_manual_stepping_enabled(self, task_id: int) -> bool:
        """Check if manual stepping is enabled for this task."""
        # Check task-specific setting
        if task_id in self.task_settings:
            if self.task_settings[task_id].get("manual_stepping"):
                return True
        
        # Check tree-specific setting
        task_entity = await self.entity_manager.get_entity(EntityType.TASK, task_id)
        if task_entity and task_entity.tree_id in self.tree_settings:
            if self.tree_settings[task_entity.tree_id].get("manual_stepping"):
                return True
        
        # Check global setting
        return self.settings.manual_stepping_enabled
    
    async def _notify_manual_hold(self, task_id: int):
        """Notify that a task is in manual hold."""
        await self.event_manager.log_event(
            EventType.TASK_MANUAL_HOLD,
            EntityType.TASK,
            task_id,
            reason="Manual stepping enabled"
        )
    
    # Manual control methods
    
    async def enable_manual_stepping(
        self,
        scope: str,
        target_id: Optional[int] = None
    ):
        """Enable manual stepping for task, tree, or system."""
        if scope == "system":
            self.settings.manual_stepping_enabled = True
        elif scope == "tree" and target_id:
            self.tree_settings.setdefault(target_id, {})["manual_stepping"] = True
        elif scope == "task" and target_id:
            self.task_settings.setdefault(target_id, {})["manual_stepping"] = True
    
    async def step_task(self, task_id: int):
        """Manually step a task forward."""
        current_state = self.task_states.get(task_id)
        
        if current_state == TaskState.MANUAL_HOLD:
            # Determine next state based on context
            task_entity = await self.entity_manager.get_entity(EntityType.TASK, task_id)
            if task_entity and task_entity.assigned_agent:
                await self.update_task_state(task_id, TaskState.READY_FOR_AGENT)
                await self.trigger_agent_call(task_id)
            else:
                logger.warning(f"Cannot step task {task_id} - no clear next state")
    
    async def get_manual_holds(self) -> List[int]:
        """Get all tasks currently in manual hold."""
        return [
            task_id for task_id, state in self.task_states.items()
            if state == TaskState.MANUAL_HOLD
        ]
    
    # Statistics and monitoring
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        state_counts = {}
        for state in TaskState:
            state_counts[state.value] = sum(
                1 for s in self.task_states.values() if s == state
            )
        
        return {
            "running": self.running,
            "active_agents": len(self.active_agents),
            "total_tasks": len(self.task_states),
            "state_distribution": state_counts,
            "event_queue_size": self.event_queue.qsize(),
            "settings": self.settings.__dict__
        }