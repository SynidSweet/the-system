# Entity-Based Runtime and Trigger System Specification

## Core Runtime Philosophy

The system operates as an **event-driven dependency resolver** where:
- **Tasks automatically progress** when ready (no polling, pure event-driven)
- **Tool calls create subtasks** that become dependencies
- **Completion events cascade** through dependency graphs
- **LLM conversations continue** automatically with system-injected messages
- **Manual controls** provide debugging and safety mechanisms

## Task State Machine

### Task States
```python
class TaskState(Enum):
    CREATED = "created"                    # Just created, needs process assignment
    PROCESS_ASSIGNED = "process_assigned"  # Process assigned, ready for process execution
    READY_FOR_AGENT = "ready_for_agent"    # Agent assigned, ready for LLM call
    WAITING_ON_DEPENDENCIES = "waiting"    # Blocked on subtask completion
    AGENT_RESPONDING = "responding"        # LLM call in progress
    TOOL_PROCESSING = "tool_processing"    # Tool calls being processed
    COMPLETED = "completed"                # Task finished successfully
    FAILED = "failed"                      # Task failed
    MANUAL_HOLD = "manual_hold"           # Manually paused for debugging
```

### State Transitions
```python
# Automatic transitions triggered by events:
CREATED → PROCESS_ASSIGNED           # Process engine assigns process
PROCESS_ASSIGNED → READY_FOR_AGENT   # Process execution completes setup
READY_FOR_AGENT → AGENT_RESPONDING   # Runtime triggers LLM call
AGENT_RESPONDING → TOOL_PROCESSING   # Agent makes tool calls
AGENT_RESPONDING → COMPLETED         # Agent calls end_task() tool
TOOL_PROCESSING → WAITING            # Tool calls create subtask dependencies
WAITING → READY_FOR_AGENT           # All dependencies completed
```

## Runtime Engine Architecture

### Core Runtime Loop
```python
class RuntimeEngine:
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.dependency_graph = DependencyGraph()
        self.settings = RuntimeSettings()
        self.active_agents = {}  # track concurrent agent calls
        
    async def start(self):
        """Main runtime loop - event-driven, no polling"""
        while True:
            # Wait for events (task state changes, completions, etc.)
            event = await self.event_queue.get()
            await self.handle_event(event)
    
    async def handle_event(self, event: RuntimeEvent):
        """Handle different types of runtime events"""
        if event.type == "task_state_changed":
            await self.handle_task_state_change(event.task_id, event.new_state)
        elif event.type == "task_completed":
            await self.handle_task_completion(event.task_id)
        elif event.type == "dependency_resolved":
            await self.handle_dependency_resolution(event.task_id)
        elif event.type == "agent_response_received":
            await self.handle_agent_response(event.task_id, event.response)
    
    async def handle_task_state_change(self, task_id: int, new_state: TaskState):
        """React to task state changes"""
        if new_state == TaskState.READY_FOR_AGENT:
            await self.trigger_agent_call(task_id)
        elif new_state == TaskState.TOOL_PROCESSING:
            await self.process_tool_calls(task_id)
        # ... other state handlers
```

### Agent Call Management
```python
class AgentCallManager:
    async def trigger_agent_call(self, task_id: int):
        """Trigger LLM call for ready task"""
        task = await self.sys.get_task(task_id)
        
        # Check runtime limits
        if not await self.can_make_agent_call(task):
            await self.sys.update_task_state(task_id, TaskState.MANUAL_HOLD)
            await self.sys.log_event("agent_call_limit_reached", task_id)
            return
        
        # Check manual stepping mode
        if await self.is_manual_stepping_enabled(task):
            await self.sys.update_task_state(task_id, TaskState.MANUAL_HOLD)
            await self.sys.notify_user(f"Task {task_id} ready for manual step")
            return
        
        # Make the LLM call
        await self.sys.update_task_state(task_id, TaskState.AGENT_RESPONDING)
        
        # Build conversation context
        conversation = await self.build_conversation_context(task)
        
        # Call agent asynchronously
        agent_response = await self.sys.call_agent(
            agent_type=task.assigned_agent,
            conversation=conversation,
            context=task.additional_context,
            tools=task.available_tools
        )
        
        # Trigger response handling
        await self.event_queue.put(RuntimeEvent(
            type="agent_response_received",
            task_id=task_id,
            response=agent_response
        ))
    
    async def can_make_agent_call(self, task: Task) -> bool:
        """Check if agent call is allowed based on limits"""
        # Check consecutive calls limit
        consecutive_calls = await self.count_consecutive_calls(task.tree_id)
        if consecutive_calls >= self.settings.max_consecutive_calls:
            return False
        
        # Check concurrent agents limit
        if len(self.active_agents) >= self.settings.max_concurrent_agents:
            return False
            
        # Check task-specific limits
        if task.metadata.get("max_agent_calls"):
            task_calls = await self.count_task_agent_calls(task.id)
            if task_calls >= task.metadata["max_agent_calls"]:
                return False
        
        return True
```

## Tool Call Processing

### Tool Call → Subtask Creation
```python
class ToolCallProcessor:
    async def process_tool_calls(self, task_id: int):
        """Process tool calls from agent response"""
        task = await self.sys.get_task(task_id)
        agent_response = await self.sys.get_latest_agent_response(task_id)
        
        if not agent_response.tool_calls:
            # No tool calls, task continues
            await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
            return
        
        subtask_ids = []
        
        for tool_call in agent_response.tool_calls:
            if tool_call.name in self.deterministic_tools:
                # Handle deterministic tools immediately
                result = await self.execute_deterministic_tool(tool_call)
                await self.add_system_message(task_id, f"Tool {tool_call.name} completed: {result}")
            
            elif tool_call.name in self.process_triggering_tools:
                # Create subtask for process-based tools
                subtask_id = await self.create_tool_subtask(task_id, tool_call)
                subtask_ids.append(subtask_id)
            
            elif tool_call.name in self.system_tools:
                # Handle system tools (like end_task)
                await self.execute_system_tool(task_id, tool_call)
                return  # System tools often change task state directly
        
        if subtask_ids:
            # Add dependencies and wait
            await self.sys.add_task_dependencies(task_id, subtask_ids)
            await self.sys.update_task_state(task_id, TaskState.WAITING_ON_DEPENDENCIES)
        else:
            # All tools handled, continue
            await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def create_tool_subtask(self, parent_task_id: int, tool_call: ToolCall) -> int:
        """Create subtask for tool execution"""
        if tool_call.name == "break_down_task":
            return await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=f"Break down task: {tool_call.arguments['approach']}",
                process="break_down_task_process",
                parameters=tool_call.arguments
            )
        
        elif tool_call.name == "need_more_context":
            return await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=f"Provide context: {tool_call.arguments['context_request']}",
                process="need_more_context_process",
                parameters=tool_call.arguments
            )
        
        # ... other tool-specific subtask creation
```

## Dependency Resolution System

### Dependency Graph Management
```python
class DependencyGraph:
    async def handle_task_completion(self, completed_task_id: int):
        """Handle task completion and cascade to dependents"""
        # Get all tasks waiting on this one
        dependent_tasks = await self.get_dependent_tasks(completed_task_id)
        
        for dependent_task_id in dependent_tasks:
            # Check if all dependencies are now resolved
            if await self.all_dependencies_resolved(dependent_task_id):
                await self.trigger_task_continuation(dependent_task_id)
    
    async def trigger_task_continuation(self, task_id: int):
        """Trigger task to continue after dependencies resolved"""
        task = await self.sys.get_task(task_id)
        
        # Add system message with subtask results
        subtask_summaries = await self.collect_subtask_summaries(task_id)
        system_message = self.format_dependency_completion_message(subtask_summaries)
        await self.add_system_message(task_id, system_message)
        
        # Update state to trigger next agent call
        await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    def format_dependency_completion_message(self, summaries: List[SubtaskSummary]) -> str:
        """Format completion message for agent conversation"""
        if len(summaries) == 1:
            return f"Subtask completed: {summaries[0].summary}"
        else:
            formatted = "Multiple subtasks completed:\n"
            for i, summary in enumerate(summaries, 1):
                formatted += f"{i}. {summary.summary}\n"
            return formatted
```

## Conversation Management

### Message Flow System
```python
class ConversationManager:
    async def build_conversation_context(self, task: Task) -> List[Message]:
        """Build full conversation context for agent call"""
        messages = []
        
        # Start with task instruction
        messages.append(Message(
            role="user",
            content=task.instruction
        ))
        
        # Add conversation history
        conversation_history = await self.sys.get_task_conversation(task.id)
        messages.extend(conversation_history)
        
        return messages
    
    async def add_system_message(self, task_id: int, content: str):
        """Add system message to task conversation"""
        await self.sys.add_conversation_message(task_id, Message(
            role="system",
            content=content,
            timestamp=time.time()
        ))
    
    async def add_agent_response(self, task_id: int, response: AgentResponse):
        """Add agent response to conversation"""
        await self.sys.add_conversation_message(task_id, Message(
            role="assistant", 
            content=response.content,
            tool_calls=response.tool_calls,
            timestamp=time.time()
        ))
```

## Runtime Settings and Controls

### Configuration System
```python
class RuntimeSettings:
    def __init__(self):
        # Global settings
        self.max_consecutive_calls: int = 10        # Per task tree
        self.max_concurrent_agents: int = 5         # System-wide
        self.manual_stepping_enabled: bool = False  # Global manual mode
        self.auto_trigger_enabled: bool = True      # Auto-progression
        
        # Task-specific overrides
        self.task_settings: Dict[int, TaskSettings] = {}
        
        # Tree-specific overrides  
        self.tree_settings: Dict[int, TreeSettings] = {}
    
    async def is_manual_stepping_enabled(self, task: Task) -> bool:
        """Check if manual stepping is enabled for this task"""
        # Task-specific override
        if task.id in self.task_settings:
            return self.task_settings[task.id].manual_stepping
        
        # Tree-specific override
        if task.tree_id in self.tree_settings:
            return self.tree_settings[task.tree_id].manual_stepping
        
        # Global setting
        return self.manual_stepping_enabled

class TaskSettings:
    manual_stepping: bool = False
    max_agent_calls: Optional[int] = None
    auto_trigger: bool = True
    
class TreeSettings:
    manual_stepping: bool = False
    max_tree_depth: Optional[int] = None
    max_concurrent_subtasks: Optional[int] = None
```

### Manual Control Interface
```python
class ManualControlInterface:
    async def enable_manual_stepping(self, scope: str, target_id: int = None):
        """Enable manual stepping for task, tree, or system"""
        if scope == "system":
            self.settings.manual_stepping_enabled = True
        elif scope == "tree" and target_id:
            self.settings.tree_settings[target_id].manual_stepping = True
        elif scope == "task" and target_id:
            self.settings.task_settings[target_id].manual_stepping = True
    
    async def step_task(self, task_id: int):
        """Manually step a task forward (for debugging)"""
        task = await self.sys.get_task(task_id)
        
        if task.state == TaskState.MANUAL_HOLD:
            await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
            await self.trigger_agent_call(task_id)
    
    async def get_manual_holds(self) -> List[Task]:
        """Get all tasks currently in manual hold"""
        return await self.sys.get_tasks_by_state(TaskState.MANUAL_HOLD)
```

## Event-Driven Triggers

### Event Types and Handlers
```python
class RuntimeEvent:
    type: str
    task_id: int
    data: Dict[str, Any]
    timestamp: float

# Event flow examples:
# 1. Task created → Process assignment → Agent readiness → LLM call
# 2. Agent response → Tool processing → Subtask creation → Dependency waiting
# 3. Subtask completion → Dependency resolution → Parent continuation → LLM call
# 4. End task tool → Task completion → Dependent task triggering

class EventHandlers:
    async def on_task_created(self, task_id: int):
        """Task created - assign process"""
        await self.process_engine.assign_process(task_id)
    
    async def on_process_completed(self, task_id: int):
        """Process assignment done - ready for agent"""
        await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_agent_response(self, task_id: int, response: AgentResponse):
        """Agent responded - process tools or continue"""
        await self.add_agent_response(task_id, response)
        
        if response.tool_calls:
            await self.sys.update_task_state(task_id, TaskState.TOOL_PROCESSING)
        else:
            # No tools, ready for next iteration
            await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
    
    async def on_subtask_completed(self, subtask_id: int):
        """Subtask completed - check parent dependencies"""
        parent_id = await self.sys.get_parent_task(subtask_id)
        if parent_id and await self.dependency_graph.all_dependencies_resolved(parent_id):
            await self.dependency_graph.trigger_task_continuation(parent_id)
```

## Safety and Performance Features

### Circuit Breakers
```python
class SafetyManager:
    async def check_runaway_protection(self, task_id: int) -> bool:
        """Prevent runaway agent loops"""
        consecutive_calls = await self.count_consecutive_calls(task_id)
        if consecutive_calls > self.settings.max_consecutive_calls:
            await self.sys.update_task_state(task_id, TaskState.MANUAL_HOLD)
            await self.sys.notify_user(f"Task {task_id} hit consecutive call limit")
            return False
        return True
    
    async def check_system_load(self) -> bool:
        """Monitor system resource usage"""
        if self.get_active_agent_count() > self.settings.max_concurrent_agents:
            return False
        return True
```

This runtime design ensures tasks flow automatically through their lifecycle while providing comprehensive control mechanisms for debugging and safety. The key innovation is that **everything becomes event-driven** - no polling, just pure reactive progression based on state changes and dependency resolution.