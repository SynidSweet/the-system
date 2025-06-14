import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from .models import Task, TaskStatus, TaskSubmission, TaskResponse, Agent
from .database_manager import database
from .universal_agent import UniversalAgent
from config.settings import settings


class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 5
    CRITICAL = 10


class TaskManager:
    """
    Central task management system that handles:
    - Task queue with priority handling
    - Concurrency limits
    - Task tree isolation
    - Agent spawning and coordination
    """
    
    def __init__(self):
        self.running_agents: Dict[int, UniversalAgent] = {}
        self.task_queue: List[int] = []  # Task IDs ordered by priority
        self.max_concurrent_agents = settings.max_concurrent_agents
        self.is_running = False
        self.queue_processor_task: Optional[asyncio.Task] = None
        self.websocket_manager = None  # Set by API on startup
        
        # Step mode configuration
        self.step_mode_enabled = False
        self.step_mode_threads: List[int] = []  # Specific threads in step mode
        self.paused_agents: Dict[int, asyncio.Event] = {}
        
    async def start(self):
        """Start the task manager"""
        if self.is_running:
            return
        
        self.is_running = True
        self.queue_processor_task = asyncio.create_task(self._process_queue())
        print(f"Task Manager started with max {self.max_concurrent_agents} concurrent agents")
    
    async def stop(self):
        """Stop the task manager"""
        self.is_running = False
        
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Wait for running agents to complete or force stop after timeout
        if self.running_agents:
            print(f"Waiting for {len(self.running_agents)} running agents to complete...")
            
            # Wait up to 30 seconds for graceful shutdown
            timeout = 30
            start_time = time.time()
            
            while self.running_agents and (time.time() - start_time) < timeout:
                await asyncio.sleep(1)
            
            if self.running_agents:
                print(f"Force stopping {len(self.running_agents)} agents after timeout")
                # TODO: Implement force stop mechanism
    
    async def continue_step(self, task_id: int):
        """Continue execution of a paused agent"""
        if task_id in self.paused_agents:
            self.paused_agents[task_id].set()
            del self.paused_agents[task_id]
    
    async def skip_step(self, task_id: int):
        """Skip current step (mark as continue with skip flag)"""
        # Implementation would set a skip flag on the agent
        await self.continue_step(task_id)
    
    async def abort_task(self, task_id: int):
        """Abort a running task"""
        if task_id in self.running_agents:
            agent = self.running_agents[task_id]
            # Cancel the agent's execution
            await database.tasks.update_status(task_id, TaskStatus.CANCELLED)
            del self.running_agents[task_id]
    
    def is_step_mode_active(self, tree_id: int) -> bool:
        """Check if step mode is active for a tree"""
        return self.step_mode_enabled or tree_id in self.step_mode_threads
    
    async def broadcast_message(self, message):
        """Broadcast a WebSocket message if manager is available"""
        if self.websocket_manager:
            await self.websocket_manager.broadcast_message(message)
        
        print("Task Manager stopped")
    
    async def submit_task(self, submission: TaskSubmission) -> TaskResponse:
        """Submit a new task for execution"""
        
        # Get next tree ID
        tree_id = await database.tasks.get_next_tree_id()
        
        # Determine agent type
        agent_type = submission.agent_type or "agent_selector"
        agent = await database.agents.get_by_name(agent_type)
        
        if not agent:
            raise ValueError(f"Agent type '{agent_type}' not found")
        
        # Create task
        task = Task(
            tree_id=tree_id,
            agent_id=agent.id,
            instruction=submission.instruction,
            priority=submission.priority,
            max_execution_time=submission.max_execution_time
        )
        
        task_id = await database.tasks.create(task)
        
        # Add to queue
        await self._add_to_queue(task_id)
        
        # If this is a subtask, add it to the queue immediately
        # The parent agent will continue running and can spawn more subtasks
        
        return TaskResponse(
            task_id=task_id,
            tree_id=tree_id,
            status=TaskStatus.QUEUED,
            created_at=datetime.utcnow()
        )
    
    async def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed status of a task"""
        task = await database.tasks.get_by_id(task_id)
        if not task:
            return None
        
        # Get task tree info
        tree_tasks = await database.tasks.get_by_tree_id(task.tree_id)
        
        # Get recent messages
        messages = await database.messages.get_by_task_id(task_id)
        recent_messages = messages[-5:] if messages else []
        
        return {
            "task": task.model_dump(),
            "tree_info": {
                "tree_id": task.tree_id,
                "total_tasks": len(tree_tasks),
                "completed_tasks": len([t for t in tree_tasks if t.status == TaskStatus.COMPLETE]),
                "failed_tasks": len([t for t in tree_tasks if t.status == TaskStatus.FAILED]),
                "active_tasks": len([t for t in tree_tasks if t.status in [TaskStatus.RUNNING, TaskStatus.QUEUED]])
            },
            "recent_messages": [msg.model_dump() for msg in recent_messages],
            "is_running": task_id in self.running_agents
        }
    
    async def get_task_tree(self, tree_id: int) -> List[Dict[str, Any]]:
        """Get all tasks in a tree with hierarchical structure"""
        tasks = await database.tasks.get_by_tree_id(tree_id)
        
        # Build hierarchical structure
        task_dict = {task.id: task.model_dump() for task in tasks}
        
        # Add children to each task
        for task in tasks:
            task_dict[task.id]["children"] = []
        
        for task in tasks:
            if task.parent_task_id and task.parent_task_id in task_dict:
                task_dict[task.parent_task_id]["children"].append(task_dict[task.id])
        
        # Return root tasks (no parent)
        return [task_dict[task.id] for task in tasks if not task.parent_task_id]
    
    async def get_active_trees(self) -> List[Dict[str, Any]]:
        """Get all active task trees"""
        active_tasks = await database.tasks.get_active_tasks()
        
        # Group by tree_id
        trees = {}
        for task in active_tasks:
            if task.tree_id not in trees:
                trees[task.tree_id] = {
                    "tree_id": task.tree_id,
                    "tasks": [],
                    "started_at": task.created_at,
                    "status": "active"
                }
            trees[task.tree_id]["tasks"].append(task.model_dump())
        
        return list(trees.values())
    
    async def get_all_trees(self) -> List[Dict[str, Any]]:
        """Get all task trees including completed ones"""
        # Get all root tasks (tasks with no parent)
        all_tasks = await database.tasks.get_all_root_tasks()
        
        # For each root task, get the full tree
        trees = []
        for root_task in all_tasks:
            # Get all tasks in this tree
            tree_tasks = await database.tasks.get_by_tree_id(root_task.tree_id)
            
            # Build tree structure
            tree = {
                "tree_id": root_task.tree_id,
                "tasks": [task.model_dump() for task in tree_tasks],
                "started_at": root_task.created_at.isoformat() if root_task.created_at else None,
                "status": root_task.status.value if hasattr(root_task.status, 'value') else root_task.status
            }
            trees.append(tree)
        
        return trees
    
    async def _add_to_queue(self, task_id: int):
        """Add task to queue in priority order"""
        task = await database.tasks.get_by_id(task_id)
        if not task:
            return
        
        # Update task status
        await database.tasks.update_status(task_id, TaskStatus.QUEUED)
        
        # Insert in priority order (higher priority first)
        inserted = False
        for i, queued_task_id in enumerate(self.task_queue):
            queued_task = await database.tasks.get_by_id(queued_task_id)
            if queued_task and task.priority > queued_task.priority:
                self.task_queue.insert(i, task_id)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task_id)
        
        print(f"Task {task_id} added to queue (priority: {task.priority}, queue size: {len(self.task_queue)})")
    
    async def _check_for_new_subtasks(self):
        """Check for newly created subtasks that need to be queued"""
        # Get all tasks with status CREATED
        from config.database import db_manager
        
        query = "SELECT id FROM tasks WHERE status = ?"
        new_tasks = await db_manager.execute_query(query, (TaskStatus.CREATED.value,))
        
        for task_row in new_tasks:
            task_id = task_row['id']
            # Check if not already in queue or running
            if task_id not in self.task_queue and task_id not in self.running_agents:
                await self._add_to_queue(task_id)
    
    async def _process_queue(self):
        """Main queue processing loop"""
        print("Queue processor started")
        
        while self.is_running:
            try:
                # Check for new subtasks that need to be queued
                await self._check_for_new_subtasks()
                
                # Clean up completed agents
                await self._cleanup_completed_agents()
                
                # Process pending tasks if we have capacity
                if len(self.running_agents) < self.max_concurrent_agents and self.task_queue:
                    await self._start_next_task()
                
                # Brief sleep to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error in queue processor: {e}")
                await asyncio.sleep(1)  # Wait longer on error
        
        print("Queue processor stopped")
    
    async def _cleanup_completed_agents(self):
        """Remove completed agents from running list"""
        completed_agents = []
        
        for task_id, agent in list(self.running_agents.items()):
            # Check if agent has execution task and if it's done
            if hasattr(agent, '_execution_task') and agent._execution_task.done():
                try:
                    result = await agent._execution_task
                    await self._handle_agent_completion(task_id, result)
                except Exception as e:
                    await self._handle_agent_error(task_id, e)
                
                completed_agents.append(task_id)
        
        # Remove from running agents
        for task_id in completed_agents:
            del self.running_agents[task_id]
    
    async def _start_next_task(self):
        """Start the next task from the queue"""
        if not self.task_queue:
            return
        
        task_id = self.task_queue.pop(0)
        
        # Verify task is still valid
        task = await database.tasks.get_by_id(task_id)
        if not task or task.status != TaskStatus.QUEUED:
            return  # Skip invalid or already processed tasks
        
        # Create and start agent
        try:
            agent = UniversalAgent(task_id)
            
            # Pass task manager reference for step mode and broadcasting
            agent.task_manager = self
            
            if await agent.initialize():
                # Store agent instance for management
                self.running_agents[task_id] = agent
                
                # Start agent execution
                agent_task = asyncio.create_task(agent.execute())
                agent._execution_task = agent_task  # Store task reference
                
                print(f"Started agent for task {task_id} (running: {len(self.running_agents)})")
            else:
                await self._handle_agent_error(task_id, Exception("Agent initialization failed"))
                
        except Exception as e:
            await self._handle_agent_error(task_id, e)
    
    async def _handle_agent_completion(self, task_id: int, result):
        """Handle successful agent completion"""
        print(f"Agent for task {task_id} completed successfully")
        
        # Check if this task spawned subtasks
        if result.spawned_tasks:
            for subtask_id in result.spawned_tasks:
                await self._add_to_queue(subtask_id)
        
        # TODO: Trigger post-completion agents (evaluator, documentation)
    
    async def _handle_agent_error(self, task_id: int, error: Exception):
        """Handle agent execution error"""
        print(f"Agent for task {task_id} failed: {error}")
        
        # Update task status
        await database.tasks.update_status(
            task_id,
            TaskStatus.FAILED,
            error_message=str(error)
        )
        
        # TODO: Implement error recovery strategies
    
    async def pause_tree(self, tree_id: int):
        """Pause all tasks in a tree"""
        # TODO: Implement tree pausing
        pass
    
    async def resume_tree(self, tree_id: int):
        """Resume all tasks in a tree"""
        # TODO: Implement tree resuming
        pass
    
    async def cancel_tree(self, tree_id: int):
        """Cancel all tasks in a tree"""
        tree_tasks = await database.tasks.get_by_tree_id(tree_id)
        
        for task in tree_tasks:
            if task.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]:
                await database.tasks.update_status(
                    task.id,
                    TaskStatus.FAILED,
                    error_message="Cancelled by user"
                )
                
                # Remove from queue if queued
                if task.id in self.task_queue:
                    self.task_queue.remove(task.id)
                
                # TODO: Stop running agent if running
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics"""
        return {
            "running_agents": len(self.running_agents),
            "queued_tasks": len(self.task_queue),
            "max_concurrent_agents": self.max_concurrent_agents,
            "is_running": self.is_running
        }


# Global task manager instance
task_manager = TaskManager()