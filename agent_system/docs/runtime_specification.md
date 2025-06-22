# Process-First Runtime and Trigger System Specification

## Core Process-First Runtime Philosophy

The system operates as a **systematic framework-driven dependency resolver** where:
- **Systematic framework establishment automatically precedes** all task execution
- **Process discovery creates comprehensive structure** before any task breakdown
- **Framework-compliant subtasks become dependencies** within systematic boundaries
- **Completion events cascade** through systematic framework-defined dependency graphs
- **LLM conversations continue** automatically within established systematic frameworks
- **Manual controls** provide systematic framework debugging and safety mechanisms

## Systematic Task State Machine

### Process-First Task States
```python
class SystematicTaskState(Enum):
    CREATED = "created"                              # Just created, needs systematic framework analysis
    FRAMEWORK_ANALYSIS = "framework_analysis"       # Systematic domain analysis in progress
    FRAMEWORK_ESTABLISHMENT = "framework_establishment"  # Missing systematic frameworks being created
    FRAMEWORK_VALIDATED = "framework_validated"     # Systematic framework completeness confirmed
    SYSTEMATIC_PROCESS_ASSIGNED = "systematic_process_assigned"  # Framework-compliant process assigned
    READY_FOR_SYSTEMATIC_AGENT = "ready_for_systematic_agent"    # Agent assigned within framework boundaries
    WAITING_ON_SYSTEMATIC_DEPENDENCIES = "waiting_on_systematic_dependencies"  # Blocked on framework-compliant subtasks
    SYSTEMATIC_AGENT_RESPONDING = "systematic_agent_responding"  # LLM call within systematic framework
    SYSTEMATIC_TOOL_PROCESSING = "systematic_tool_processing"    # Framework-compliant tool calls being processed
    COMPLETED = "completed"                          # Task finished with systematic framework compliance
    FAILED = "failed"                               # Task failed with systematic framework context
    MANUAL_HOLD = "manual_hold"                     # Manually paused for systematic debugging
```

### Process-First State Transitions
```python
# Automatic systematic transitions triggered by framework events:
CREATED → FRAMEWORK_ANALYSIS                    # Systematic domain analysis initiated
FRAMEWORK_ANALYSIS → FRAMEWORK_ESTABLISHMENT    # Missing systematic frameworks identified
FRAMEWORK_ESTABLISHMENT → FRAMEWORK_VALIDATED   # Systematic frameworks established completely
FRAMEWORK_VALIDATED → SYSTEMATIC_PROCESS_ASSIGNED  # Framework-compliant process assigned
SYSTEMATIC_PROCESS_ASSIGNED → READY_FOR_SYSTEMATIC_AGENT  # Framework-aware agent assignment completed
READY_FOR_SYSTEMATIC_AGENT → SYSTEMATIC_AGENT_RESPONDING  # Runtime triggers systematic LLM call
SYSTEMATIC_AGENT_RESPONDING → SYSTEMATIC_TOOL_PROCESSING  # Agent makes framework-compliant tool calls
SYSTEMATIC_AGENT_RESPONDING → COMPLETED         # Agent calls systematic end_task() tool
SYSTEMATIC_TOOL_PROCESSING → WAITING_ON_SYSTEMATIC_DEPENDENCIES  # Tool calls create framework-compliant subtasks
WAITING_ON_SYSTEMATIC_DEPENDENCIES → READY_FOR_SYSTEMATIC_AGENT  # All systematic dependencies completed
```

## Process-First Runtime Engine Architecture

### Core Systematic Runtime Loop
```python
class SystematicRuntimeEngine:
    def __init__(self):
        self.systematic_task_queue = PriorityQueue()
        self.systematic_dependency_graph = SystematicDependencyGraph()
        self.systematic_framework_registry = SystematicFrameworkRegistry()
        self.settings = SystematicRuntimeSettings()
        self.active_systematic_agents = {}
        
    async def start(self):
        """Main systematic runtime loop - framework-driven, no polling"""
        while True:
            # Wait for systematic framework events
            event = await self.systematic_event_queue.get()
            await self.handle_systematic_event(event)
    
    async def handle_systematic_event(self, event: SystematicRuntimeEvent):
        """Handle different types of systematic framework events"""
        if event.type == "systematic_task_state_changed":
            await self.handle_systematic_task_state_change(event.task_id, event.new_state)
        elif event.type == "systematic_framework_established":
            await self.handle_systematic_framework_establishment(event.framework_id)
        elif event.type == "systematic_task_completed":
            await self.handle_systematic_task_completion(event.task_id)
        elif event.type == "systematic_dependency_resolved":
            await self.handle_systematic_dependency_resolution(event.task_id)
        elif event.type == "systematic_agent_response_received":
            await self.handle_systematic_agent_response(event.task_id, event.response)
    
    async def handle_systematic_task_state_change(self, task_id: int, new_state: SystematicTaskState):
        """React to systematic task state changes"""
        if new_state == SystematicTaskState.CREATED:
            await self.initiate_systematic_framework_analysis(task_id)
        elif new_state == SystematicTaskState.FRAMEWORK_VALIDATED:
            await self.assign_systematic_process(task_id)
        elif new_state == SystematicTaskState.READY_FOR_SYSTEMATIC_AGENT:
            await self.trigger_systematic_agent_call(task_id)
        elif new_state == SystematicTaskState.SYSTEMATIC_TOOL_PROCESSING:
            await self.process_systematic_tool_calls(task_id)
```

### Systematic Framework Analysis Management
```python
class SystematicFrameworkAnalysisManager:
    async def initiate_systematic_framework_analysis(self, task_id: int):
        """Initiate comprehensive systematic framework analysis for every task"""
        task = await self.sys.get_task(task_id)
        
        # ALWAYS establish systematic framework first
        await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_ANALYSIS)
        
        # Execute systematic process discovery
        framework_analysis_result = await self.sys.execute_process(
            "process_discovery_process",
            task_id=task_id,
            task_instruction=task.instruction
        )
        
        if framework_analysis_result.missing_frameworks:
            # Establish missing systematic frameworks
            await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_ESTABLISHMENT)
            await self.establish_missing_systematic_frameworks(task_id, framework_analysis_result.missing_frameworks)
        else:
            # Framework complete - proceed to validation
            await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_VALIDATED)
    
    async def establish_missing_systematic_frameworks(self, task_id: int, missing_frameworks: List[FrameworkRequirement]):
        """Establish all missing systematic frameworks before any execution"""
        establishment_tasks = []
        
        for framework_requirement in missing_frameworks:
            establishment_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Establish systematic framework: {framework_requirement.name}",
                agent_type="process_discovery",
                context=["process_creation_guide", "systematic_framework_patterns"],
                process="systematic_framework_establishment_process",
                parameters={
                    "framework_requirement": framework_requirement,
                    "domain_analysis": framework_requirement.domain_context,
                    "isolation_requirements": framework_requirement.isolated_success_requirements
                }
            )
            establishment_tasks.append(establishment_task_id)
        
        # Wait for ALL systematic frameworks to be established
        await self.sys.wait_for_tasks(establishment_tasks)
        
        # Validate complete systematic framework
        validation_result = await self.validate_systematic_framework_completeness(task_id)
        
        if validation_result.framework_complete:
            await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_VALIDATED)
        else:
            # Additional framework establishment needed
            await self.establish_missing_systematic_frameworks(task_id, validation_result.additional_requirements)
```

### Systematic Agent Call Management
```python
class SystematicAgentCallManager:
    async def trigger_systematic_agent_call(self, task_id: int):
        """Trigger LLM call for systematic framework-ready task"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        # Check systematic runtime limits
        if not await self.can_make_systematic_agent_call(task, systematic_framework):
            await self.sys.update_task_state(task_id, SystematicTaskState.MANUAL_HOLD)
            await self.sys.log_event("systematic_agent_call_limit_reached", task_id)
            return
        
        # Check systematic framework compliance
        framework_compliance = await self.validate_systematic_framework_compliance(task, systematic_framework)
        if not framework_compliance.compliant:
            await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_ESTABLISHMENT)
            await self.enhance_systematic_framework_compliance(task_id, framework_compliance.compliance_gaps)
            return
        
        # Check manual stepping mode for systematic debugging
        if await self.is_systematic_manual_stepping_enabled(task):
            await self.sys.update_task_state(task_id, SystematicTaskState.MANUAL_HOLD)
            await self.sys.notify_user(f"Systematic task {task_id} ready for manual framework step")
            return
        
        # Make the systematic LLM call
        await self.sys.update_task_state(task_id, SystematicTaskState.SYSTEMATIC_AGENT_RESPONDING)
        
        # Build systematic conversation context
        systematic_conversation = await self.build_systematic_conversation_context(task, systematic_framework)
        
        # Call systematic agent
        systematic_agent_response = await self.sys.call_systematic_agent(
            agent_type=task.assigned_agent,
            conversation=systematic_conversation,
            systematic_framework=systematic_framework,
            context=task.additional_context,
            tools=task.available_tools
        )
        
        # Trigger systematic response handling
        await self.systematic_event_queue.put(SystematicRuntimeEvent(
            type="systematic_agent_response_received",
            task_id=task_id,
            response=systematic_agent_response,
            framework_id=systematic_framework.id
        ))
    
    async def can_make_systematic_agent_call(self, task: Task, framework: SystematicFramework) -> bool:
        """Check if systematic agent call is allowed based on framework limits"""
        # Check systematic consecutive calls limit
        consecutive_calls = await self.count_systematic_consecutive_calls(task.tree_id)
        if consecutive_calls >= self.settings.max_systematic_consecutive_calls:
            return False
        
        # Check systematic concurrent agents limit
        if len(self.active_systematic_agents) >= self.settings.max_concurrent_systematic_agents:
            return False
        
        # Check systematic framework-specific limits
        framework_limits = framework.get_execution_limits()
        if framework_limits and not self.within_framework_limits(task, framework_limits):
            return False
        
        return True
```

## Systematic Tool Call Processing

### Framework-Compliant Tool Call → Systematic Subtask Creation
```python
class SystematicToolCallProcessor:
    async def process_systematic_tool_calls(self, task_id: int):
        """Process systematic framework-compliant tool calls from agent response"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        agent_response = await self.sys.get_latest_agent_response(task_id)
        
        if not agent_response.tool_calls:
            # No tool calls, systematic task continues
            await self.sys.update_task_state(task_id, SystematicTaskState.READY_FOR_SYSTEMATIC_AGENT)
            return
        
        systematic_subtask_ids = []
        
        for tool_call in agent_response.tool_calls:
            # Validate systematic framework compliance
            framework_compliance = await self.validate_tool_call_framework_compliance(
                tool_call, systematic_framework
            )
            
            if not framework_compliance.compliant:
                await self.add_system_message(task_id, 
                    f"Tool call {tool_call.name} denied: {framework_compliance.compliance_issues}")
                continue
            
            if tool_call.name in self.systematic_deterministic_tools:
                # Handle deterministic tools within systematic framework
                result = await self.execute_systematic_deterministic_tool(tool_call, systematic_framework)
                await self.add_system_message(task_id, f"Systematic tool {tool_call.name} completed: {result}")
            
            elif tool_call.name in self.systematic_process_triggering_tools:
                # Create systematic subtask for framework-compliant process-based tools
                systematic_subtask_id = await self.create_systematic_tool_subtask(task_id, tool_call, systematic_framework)
                systematic_subtask_ids.append(systematic_subtask_id)
            
            elif tool_call.name in self.systematic_framework_tools:
                # Handle systematic framework management tools
                await self.execute_systematic_framework_tool(task_id, tool_call, systematic_framework)
                return  # Framework tools may change task state directly
        
        if systematic_subtask_ids:
            # Add systematic dependencies and wait
            await self.sys.add_systematic_task_dependencies(task_id, systematic_subtask_ids)
            await self.sys.update_task_state(task_id, SystematicTaskState.WAITING_ON_SYSTEMATIC_DEPENDENCIES)
        else:
            # All systematic tools handled, continue
            await self.sys.update_task_state(task_id, SystematicTaskState.READY_FOR_SYSTEMATIC_AGENT)
    
    async def create_systematic_tool_subtask(self, parent_task_id: int, tool_call: ToolCall, 
                                           systematic_framework: SystematicFramework) -> int:
        """Create systematic framework-compliant subtask for tool execution"""
        if tool_call.name == "break_down_task":
            return await self.sys.create_systematic_subtask(
                parent_id=parent_task_id,
                instruction=f"Systematic breakdown: {tool_call.arguments['approach']}",
                systematic_framework_id=systematic_framework.id,
                process="systematic_break_down_task_process",
                parameters={
                    **tool_call.arguments,
                    "systematic_framework": systematic_framework,
                    "framework_compliance_requirements": systematic_framework.breakdown_compliance_requirements
                }
            )
        
        elif tool_call.name == "need_more_context":
            return await self.sys.create_systematic_subtask(
                parent_id=parent_task_id,
                instruction=f"Systematic context provision: {tool_call.arguments['context_request']}",
                systematic_framework_id=systematic_framework.id,
                process="systematic_need_more_context_process",
                parameters={
                    **tool_call.arguments,
                    "systematic_framework": systematic_framework,
                    "framework_context_requirements": systematic_framework.context_requirements
                }
            )
        
        elif tool_call.name == "need_process_establishment":
            return await self.sys.create_systematic_subtask(
                parent_id=parent_task_id,
                instruction=f"Establish systematic framework: {tool_call.arguments['process_description']}",
                agent_type="process_discovery",
                process="process_discovery_process",
                parameters={
                    **tool_call.arguments,
                    "current_systematic_framework": systematic_framework,
                    "framework_enhancement_requirements": tool_call.arguments.get('framework_requirements', {})
                }
            )
        
        # ... other systematic tool-specific subtask creation
```

## Systematic Dependency Resolution System

### Systematic Framework Dependency Graph Management
```python
class SystematicDependencyGraph:
    async def handle_systematic_task_completion(self, completed_task_id: int):
        """Handle systematic task completion and cascade to framework-compliant dependents"""
        completed_task = await self.sys.get_task(completed_task_id)
        systematic_framework = await self.sys.get_systematic_framework(completed_task.systematic_framework_id)
        
        # Get all systematic tasks waiting on this one
        dependent_tasks = await self.get_systematic_dependent_tasks(completed_task_id)
        
        for dependent_task_id in dependent_tasks:
            # Check if all systematic dependencies are now resolved
            if await self.all_systematic_dependencies_resolved(dependent_task_id):
                await self.trigger_systematic_task_continuation(dependent_task_id)
    
    async def trigger_systematic_task_continuation(self, task_id: int):
        """Trigger systematic task to continue after framework-compliant dependencies resolved"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        # Add systematic message with framework-compliant subtask results
        systematic_subtask_summaries = await self.collect_systematic_subtask_summaries(task_id, systematic_framework)
        systematic_message = self.format_systematic_dependency_completion_message(
            systematic_subtask_summaries, systematic_framework
        )
        await self.add_system_message(task_id, systematic_message)
        
        # Validate systematic framework compliance before continuation
        framework_compliance = await self.validate_systematic_framework_compliance_after_dependencies(
            task_id, systematic_framework
        )
        
        if framework_compliance.compliant:
            # Update state to trigger next systematic agent call
            await self.sys.update_task_state(task_id, SystematicTaskState.READY_FOR_SYSTEMATIC_AGENT)
        else:
            # Framework compliance issues - enhance framework
            await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_ESTABLISHMENT)
            await self.enhance_systematic_framework_for_compliance(task_id, framework_compliance.compliance_gaps)
    
    def format_systematic_dependency_completion_message(self, summaries: List[SystematicSubtaskSummary], 
                                                       framework: SystematicFramework) -> str:
        """Format systematic completion message for agent conversation"""
        if len(summaries) == 1:
            return f"Systematic subtask completed within {framework.domain_type} framework: {summaries[0].summary}"
        else:
            formatted = f"Multiple systematic subtasks completed within {framework.domain_type} framework:\n"
            for i, summary in enumerate(summaries, 1):
                formatted += f"{i}. {summary.summary} (Framework compliance: {summary.framework_compliance})\n"
            return formatted
```

## Systematic Conversation Management

### Systematic Framework Message Flow System
```python
class SystematicConversationManager:
    async def build_systematic_conversation_context(self, task: Task, framework: SystematicFramework) -> List[SystematicMessage]:
        """Build systematic framework-aware conversation context for agent call"""
        messages = []
        
        # Start with systematic framework context
        framework_context_message = SystematicMessage(
            role="system",
            content=f"Operating within systematic framework: {framework.domain_type}. "
                   f"Framework requirements: {framework.get_framework_requirements()}. "
                   f"Isolation capabilities: {framework.get_isolation_capabilities()}."
        )
        messages.append(framework_context_message)
        
        # Add task instruction within framework context
        messages.append(SystematicMessage(
            role="user",
            content=f"Task: {task.instruction}\n\n"
                   f"Systematic Framework Context: {framework.get_task_context(task.instruction)}\n"
                   f"Isolation Requirements: {framework.get_isolation_requirements_for_task(task.instruction)}"
        ))
        
        # Add systematic conversation history
        systematic_conversation_history = await self.sys.get_systematic_task_conversation(task.id)
        messages.extend(systematic_conversation_history)
        
        return messages
    
    async def add_systematic_message(self, task_id: int, content: str):
        """Add systematic framework-aware message to task conversation"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        systematic_message = SystematicMessage(
            role="system",
            content=f"[{systematic_framework.domain_type} Framework] {content}",
            framework_id=systematic_framework.id,
            timestamp=time.time()
        )
        
        await self.sys.add_systematic_conversation_message(task_id, systematic_message)
    
    async def add_systematic_agent_response(self, task_id: int, response: SystematicAgentResponse):
        """Add systematic framework-compliant agent response to conversation"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        # Validate framework compliance of response
        compliance_validation = await self.validate_response_framework_compliance(response, systematic_framework)
        
        systematic_message = SystematicMessage(
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls,
            framework_id=systematic_framework.id,
            framework_compliance=compliance_validation.compliant,
            timestamp=time.time()
        )
        
        await self.sys.add_systematic_conversation_message(task_id, systematic_message)
```

## Systematic Runtime Settings and Controls

### Systematic Framework Configuration System
```python
class SystematicRuntimeSettings:
    def __init__(self):
        # Global systematic settings
        self.max_systematic_consecutive_calls: int = 15      # Per systematic task tree
        self.max_concurrent_systematic_agents: int = 7       # System-wide systematic limit
        self.systematic_manual_stepping_enabled: bool = False  # Global systematic manual mode
        self.systematic_auto_trigger_enabled: bool = True      # Systematic auto-progression
        self.systematic_framework_validation_required: bool = True  # Always validate frameworks
        
        # Systematic task-specific overrides
        self.systematic_task_settings: Dict[int, SystematicTaskSettings] = {}
        
        # Systematic framework-specific overrides
        self.systematic_framework_settings: Dict[int, SystematicFrameworkSettings] = {}
    
    async def is_systematic_manual_stepping_enabled(self, task: Task) -> bool:
        """Check if systematic manual stepping is enabled for this task"""
        # Systematic task-specific override
        if task.id in self.systematic_task_settings:
            return self.systematic_task_settings[task.id].systematic_manual_stepping
        
        # Systematic framework-specific override
        if task.systematic_framework_id in self.systematic_framework_settings:
            return self.systematic_framework_settings[task.systematic_framework_id].systematic_manual_stepping
        
        # Global systematic setting
        return self.systematic_manual_stepping_enabled

class SystematicTaskSettings:
    systematic_manual_stepping: bool = False
    max_systematic_agent_calls: Optional[int] = None
    systematic_auto_trigger: bool = True
    systematic_framework_compliance_required: bool = True
    
class SystematicFrameworkSettings:
    systematic_manual_stepping: bool = False
    max_systematic_framework_depth: Optional[int] = None
    max_concurrent_systematic_subtasks: Optional[int] = None
    systematic_framework_validation_level: str = "strict"  # "strict", "moderate", "permissive"
```

### Systematic Manual Control Interface
```python
class SystematicManualControlInterface:
    async def enable_systematic_manual_stepping(self, scope: str, target_id: int = None):
        """Enable systematic manual stepping for task, framework, or system"""
        if scope == "system":
            self.settings.systematic_manual_stepping_enabled = True
        elif scope == "framework" and target_id:
            self.settings.systematic_framework_settings[target_id].systematic_manual_stepping = True
        elif scope == "task" and target_id:
            self.settings.systematic_task_settings[target_id].systematic_manual_stepping = True
    
    async def step_systematic_task(self, task_id: int):
        """Manually step a systematic task forward (for framework debugging)"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        if task.state == SystematicTaskState.MANUAL_HOLD:
            # Validate systematic framework before stepping
            framework_validation = await self.validate_systematic_framework_for_step(task, systematic_framework)
            
            if framework_validation.can_proceed:
                await self.sys.update_task_state(task_id, SystematicTaskState.READY_FOR_SYSTEMATIC_AGENT)
                await self.trigger_systematic_agent_call(task_id)
            else:
                await self.sys.notify_user(f"Systematic framework validation failed: {framework_validation.issues}")
    
    async def get_systematic_manual_holds(self) -> List[SystematicTask]:
        """Get all systematic tasks currently in manual hold"""
        systematic_holds = await self.sys.get_tasks_by_state(SystematicTaskState.MANUAL_HOLD)
        
        # Add systematic framework context to each hold
        for hold in systematic_holds:
            hold.systematic_framework = await self.sys.get_systematic_framework(hold.systematic_framework_id)
        
        return systematic_holds
```

## Systematic Event-Driven Triggers

### Systematic Framework Event Types and Handlers
```python
class SystematicRuntimeEvent:
    type: str
    task_id: int
    framework_id: Optional[int]
    data: Dict[str, Any]
    timestamp: float

# Systematic event flow examples:
# 1. Task created → Systematic framework analysis → Framework establishment → Agent readiness → LLM call
# 2. Systematic agent response → Framework-compliant tool processing → Systematic subtask creation → Framework dependency waiting
# 3. Systematic subtask completion → Framework dependency resolution → Parent systematic continuation → LLM call
# 4. Systematic end task tool → Framework compliance validation → Task completion → Dependent systematic task triggering

class SystematicEventHandlers:
    async def on_systematic_task_created(self, task_id: int):
        """Systematic task created - initiate framework analysis"""
        await self.systematic_framework_analyzer.initiate_systematic_framework_analysis(task_id)
    
    async def on_systematic_framework_established(self, framework_id: int, task_id: int):
        """Systematic framework established - proceed to validation"""
        await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_VALIDATED)
    
    async def on_systematic_agent_response(self, task_id: int, response: SystematicAgentResponse):
        """Systematic agent responded - process framework-compliant tools or continue"""
        await self.add_systematic_agent_response(task_id, response)
        
        if response.tool_calls:
            await self.sys.update_task_state(task_id, SystematicTaskState.SYSTEMATIC_TOOL_PROCESSING)
        else:
            # No tools, ready for next systematic iteration
            await self.sys.update_task_state(task_id, SystematicTaskState.READY_FOR_SYSTEMATIC_AGENT)
    
    async def on_systematic_subtask_completed(self, subtask_id: int):
        """Systematic subtask completed - check systematic parent dependencies"""
        parent_id = await self.sys.get_parent_task(subtask_id)
        if parent_id and await self.systematic_dependency_graph.all_systematic_dependencies_resolved(parent_id):
            await self.systematic_dependency_graph.trigger_systematic_task_continuation(parent_id)
```

## Systematic Safety and Performance Features

### Systematic Framework Circuit Breakers
```python
class SystematicSafetyManager:
    async def check_systematic_runaway_protection(self, task_id: int) -> bool:
        """Prevent systematic runaway agent loops through framework validation"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        consecutive_calls = await self.count_systematic_consecutive_calls(task_id)
        framework_call_limit = systematic_framework.get_call_limit()
        
        if consecutive_calls > min(self.settings.max_systematic_consecutive_calls, framework_call_limit):
            await self.sys.update_task_state(task_id, SystematicTaskState.MANUAL_HOLD)
            await self.sys.notify_user(f"Systematic task {task_id} hit framework call limit")
            return False
        return True
    
    async def check_systematic_framework_compliance(self, task_id: int) -> bool:
        """Monitor systematic framework compliance during execution"""
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        compliance_check = await self.validate_ongoing_systematic_framework_compliance(task, systematic_framework)
        
        if not compliance_check.compliant:
            await self.sys.update_task_state(task_id, SystematicTaskState.FRAMEWORK_ESTABLISHMENT)
            await self.enhance_systematic_framework_compliance(task_id, compliance_check.compliance_gaps)
            return False
        return True
```

This systematic process-first runtime design ensures tasks flow automatically through comprehensive framework establishment before any execution while providing complete control mechanisms for systematic debugging and safety. The key innovation is that **everything becomes systematic framework-driven** - no ad-hoc execution, just pure systematic progression based on comprehensive framework establishment and framework-compliant dependency resolution.