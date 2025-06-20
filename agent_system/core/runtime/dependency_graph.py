"""Dependency graph management for task execution."""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
import asyncio
from datetime import datetime

from agent_system.core.events.event_types import EventType, EntityType
from agent_system.core.events.event_manager import EventManager


class DependencyNode:
    """Represents a task in the dependency graph."""
    
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.dependencies: Set[int] = set()  # Tasks this task depends on
        self.dependents: Set[int] = set()    # Tasks that depend on this task
        self.completed = False
        self.failed = False
        self.completion_time: Optional[datetime] = None
        self.failure_reason: Optional[str] = None


class DependencyGraph:
    """Manages task dependencies and resolution."""
    
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.event_manager = event_manager
        self.nodes: Dict[int, DependencyNode] = {}
        self._lock = asyncio.Lock()
    
    async def add_task(self, task_id: int) -> DependencyNode:
        """Add a task to the dependency graph."""
        async with self._lock:
            if task_id not in self.nodes:
                self.nodes[task_id] = DependencyNode(task_id)
                
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.DEPENDENCY_ADDED,
                        EntityType.TASK,
                        task_id,
                        action="task_added_to_graph"
                    )
            
            return self.nodes[task_id]
    
    async def add_dependency(self, task_id: int, depends_on: int) -> bool:
        """Add a dependency relationship between tasks."""
        async with self._lock:
            # Ensure both tasks exist
            if task_id not in self.nodes:
                await self.add_task(task_id)
            if depends_on not in self.nodes:
                await self.add_task(depends_on)
            
            # Check for circular dependencies
            if await self._would_create_cycle(task_id, depends_on):
                if self.event_manager:
                    await self.event_manager.log_event(
                        EventType.DEPENDENCY_FAILED,
                        EntityType.TASK,
                        task_id,
                        reason="Would create circular dependency",
                        depends_on=depends_on
                    )
                return False
            
            # Add the dependency
            self.nodes[task_id].dependencies.add(depends_on)
            self.nodes[depends_on].dependents.add(task_id)
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EventType.DEPENDENCY_ADDED,
                    EntityType.TASK,
                    task_id,
                    depends_on=depends_on
                )
            
            return True
    
    async def add_dependencies(self, task_id: int, dependencies: List[int]) -> bool:
        """Add multiple dependencies for a task."""
        success = True
        for dep_id in dependencies:
            if not await self.add_dependency(task_id, dep_id):
                success = False
        return success
    
    async def mark_completed(self, task_id: int) -> List[int]:
        """Mark a task as completed and return tasks that can now proceed."""
        async with self._lock:
            if task_id not in self.nodes:
                return []
            
            node = self.nodes[task_id]
            node.completed = True
            node.completion_time = datetime.now()
            
            # Find tasks that can now proceed
            ready_tasks = []
            for dependent_id in node.dependents:
                if await self._all_dependencies_resolved(dependent_id):
                    ready_tasks.append(dependent_id)
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EventType.DEPENDENCY_RESOLVED,
                    EntityType.TASK,
                    task_id,
                    ready_tasks=ready_tasks
                )
            
            return ready_tasks
    
    async def mark_failed(self, task_id: int, reason: str) -> List[int]:
        """Mark a task as failed and return affected dependent tasks."""
        async with self._lock:
            if task_id not in self.nodes:
                return []
            
            node = self.nodes[task_id]
            node.failed = True
            node.failure_reason = reason
            
            # Get all dependent tasks that are now blocked
            blocked_tasks = list(node.dependents)
            
            if self.event_manager:
                await self.event_manager.log_event(
                    EventType.DEPENDENCY_FAILED,
                    EntityType.TASK,
                    task_id,
                    reason=reason,
                    blocked_tasks=blocked_tasks
                )
            
            return blocked_tasks
    
    async def all_dependencies_resolved(self, task_id: int) -> bool:
        """Check if all dependencies for a task are resolved."""
        async with self._lock:
            return await self._all_dependencies_resolved(task_id)
    
    async def _all_dependencies_resolved(self, task_id: int) -> bool:
        """Internal method to check if all dependencies are resolved."""
        if task_id not in self.nodes:
            return True
        
        node = self.nodes[task_id]
        for dep_id in node.dependencies:
            if dep_id in self.nodes:
                dep_node = self.nodes[dep_id]
                if not dep_node.completed or dep_node.failed:
                    return False
        
        return True
    
    async def get_dependency_status(self, task_id: int) -> Dict:
        """Get detailed dependency status for a task."""
        async with self._lock:
            if task_id not in self.nodes:
                return {
                    "task_id": task_id,
                    "exists": False,
                    "dependencies": [],
                    "dependents": []
                }
            
            node = self.nodes[task_id]
            
            # Build dependency status
            dependencies = []
            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    dep_node = self.nodes[dep_id]
                    dependencies.append({
                        "task_id": dep_id,
                        "completed": dep_node.completed,
                        "failed": dep_node.failed,
                        "failure_reason": dep_node.failure_reason
                    })
            
            # Build dependent status
            dependents = []
            for dep_id in node.dependents:
                if dep_id in self.nodes:
                    dep_node = self.nodes[dep_id]
                    dependents.append({
                        "task_id": dep_id,
                        "completed": dep_node.completed,
                        "failed": dep_node.failed
                    })
            
            return {
                "task_id": task_id,
                "exists": True,
                "completed": node.completed,
                "failed": node.failed,
                "failure_reason": node.failure_reason,
                "completion_time": node.completion_time.isoformat() if node.completion_time else None,
                "dependencies": dependencies,
                "dependents": dependents,
                "all_dependencies_resolved": await self._all_dependencies_resolved(task_id)
            }
    
    async def get_blocked_tasks(self) -> List[int]:
        """Get all tasks that are blocked on dependencies."""
        async with self._lock:
            blocked = []
            for task_id, node in self.nodes.items():
                if not node.completed and not node.failed:
                    if not await self._all_dependencies_resolved(task_id):
                        blocked.append(task_id)
            return blocked
    
    async def get_ready_tasks(self) -> List[int]:
        """Get all tasks that have all dependencies resolved and are not completed."""
        async with self._lock:
            ready = []
            for task_id, node in self.nodes.items():
                if not node.completed and not node.failed:
                    if await self._all_dependencies_resolved(task_id):
                        ready.append(task_id)
            return ready
    
    async def _would_create_cycle(self, task_id: int, new_dependency: int) -> bool:
        """Check if adding a dependency would create a cycle."""
        # Use DFS to check if new_dependency can reach task_id
        visited = set()
        stack = [new_dependency]
        
        while stack:
            current = stack.pop()
            if current == task_id:
                return True
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current in self.nodes:
                stack.extend(self.nodes[current].dependencies)
        
        return False
    
    async def get_execution_order(self) -> List[List[int]]:
        """Get tasks grouped by execution level (topological sort)."""
        async with self._lock:
            # Create a copy of the graph
            in_degree = {}
            for task_id, node in self.nodes.items():
                in_degree[task_id] = len(node.dependencies)
            
            # Find all tasks with no dependencies
            queue = deque([
                task_id for task_id, degree in in_degree.items()
                if degree == 0
            ])
            
            levels = []
            current_level = []
            next_level_queue = deque()
            
            while queue or next_level_queue:
                if not queue:
                    if current_level:
                        levels.append(current_level)
                        current_level = []
                    queue = next_level_queue
                    next_level_queue = deque()
                
                if not queue:
                    break
                
                task_id = queue.popleft()
                current_level.append(task_id)
                
                # Reduce in-degree for dependents
                if task_id in self.nodes:
                    for dependent_id in self.nodes[task_id].dependents:
                        in_degree[dependent_id] -= 1
                        if in_degree[dependent_id] == 0:
                            next_level_queue.append(dependent_id)
            
            if current_level:
                levels.append(current_level)
            
            return levels
    
    def visualize(self) -> str:
        """Generate a text visualization of the dependency graph."""
        lines = ["Dependency Graph:"]
        lines.append("-" * 50)
        
        for task_id, node in sorted(self.nodes.items()):
            status = "✓" if node.completed else "✗" if node.failed else "○"
            lines.append(f"{status} Task {task_id}")
            
            if node.dependencies:
                deps = ", ".join(str(d) for d in sorted(node.dependencies))
                lines.append(f"  └─ Depends on: {deps}")
            
            if node.dependents:
                deps = ", ".join(str(d) for d in sorted(node.dependents))
                lines.append(f"  └─ Required by: {deps}")
            
            if node.failure_reason:
                lines.append(f"  └─ Failed: {node.failure_reason}")
        
        return "\n".join(lines)