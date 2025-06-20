# Entity-Based Process Architecture Specification

## Process Implementation Strategy

### Hybrid Python + LLM Architecture
Processes are Python scripts that:
- Handle deterministic logic, state management, and system coordination
- Make strategic LLM calls only when reasoning/creativity is needed
- Call system functions for entity operations
- Include built-in error handling and rollback capabilities

### Process Categories

#### 1. Default Task Process
**The "Neutral Task" Process - Applied to tasks without specific processes**

```python
# neutral_task_process.py - The default process for tasks without assigned processes
class NeutralTaskProcess:
    """Default process applied to tasks that don't have a specific process assigned"""
    
    async def execute(self, task_id: int):
        task = await self.sys.get_task(task_id)
        
        # Skip if task already has agent assigned (pre-assigned scenario)
        if not task.assigned_agent:
            # 1. Agent Selection - create subtask for this
            selector_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Select optimal agent for: {task.instruction}",
                agent_type="agent_selector",
                context=["agent_capabilities_reference"],
                process="agent_selection_process"
            )
            
            # Wait for agent selection
            await self.sys.wait_for_tasks([selector_task_id])
            selected_agent = await self.sys.get_task_result(selector_task_id)
            await self.sys.update_task(task_id, assigned_agent=selected_agent.agent_type)
        
        # 2. Context Assignment - create subtask if needed
        if await self.needs_context_analysis(task):
            context_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Determine context needs for agent {task.assigned_agent} on: {task.instruction}",
                agent_type="context_addition",
                context=["context_addition_guide"],
                process="context_analysis_process"
            )
            
            await self.sys.wait_for_tasks([context_task_id])
            context_result = await self.sys.get_task_result(context_task_id)
            
            if context_result.additional_context_needed:
                await self.sys.add_context_to_task(task_id, context_result.context_documents)
        
        # 3. Tool Assignment - similar pattern
        if await self.needs_tool_analysis(task):
            tool_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Determine tool needs for agent {task.assigned_agent} on: {task.instruction}",
                agent_type="tool_addition",
                context=["tool_addition_guide"],
                process="tool_analysis_process"
            )
            
            await self.sys.wait_for_tasks([tool_task_id])
            tool_result = await self.sys.get_task_result(tool_task_id)
            
            if tool_result.additional_tools_needed:
                await self.sys.add_tools_to_task(task_id, tool_result.tools)
        
        # 4. Mark ready for agent - Runtime will handle LLM calls
        await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
        return {"status": "task_prepared_for_agent"}
```

#### 2. Core Tool Processes  
**Triggered by Agent Tool Calls During Task Execution**

```python
# break_down_task_process.py - Triggered when agent calls break_down_task() tool
class BreakDownTaskProcess:
    """Handles task breakdown - triggered by agent tool call, not direct LLM orchestration"""
    
    async def execute(self, parent_task_id: int, breakdown_request: str, **tool_args):
        parent_task = await self.sys.get_task(parent_task_id)
        
        # This process is triggered by an agent tool call, so we know the breakdown is requested
        # The actual breakdown work will be done by a planning agent in a subtask
        
        planning_task_id = await self.sys.create_subtask(
            parent_id=parent_task_id,
            instruction=f"Break down this task: {parent_task.instruction}. Approach: {breakdown_request}",
            agent_type="planning_agent",
            context=["planning_agent_guide", "task_breakdown_patterns"],
            parameters={
                "parent_task": parent_task.instruction,
                "breakdown_approach": breakdown_request,
                "parent_context": parent_task.additional_context
            }
        )
        
        # Wait for planning to complete
        await self.sys.wait_for_tasks([planning_task_id])
        breakdown_result = await self.sys.get_task_result(planning_task_id)
        
        # Create the actual subtasks based on planning result
        subtask_ids = []
        for subtask_spec in breakdown_result.subtasks:
            subtask_id = await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=subtask_spec.instruction,
                dependencies=subtask_spec.dependencies,
                priority=subtask_spec.priority,
                process=subtask_spec.suggested_process or "neutral_task"
            )
            subtask_ids.append(subtask_id)
        
        # Update parent task status - it's now broken down and waiting for subtasks
        await self.sys.update_task_state(parent_task_id, TaskState.WAITING_ON_DEPENDENCIES)
        await self.sys.add_task_dependencies(parent_task_id, subtask_ids)
        
        # Return result to the original agent via system message
        summary = f"Task broken down into {len(subtask_ids)} subtasks: {[s.instruction for s in breakdown_result.subtasks]}"
        return {"status": "breakdown_complete", "subtasks_created": subtask_ids, "summary": summary}

# end_task_process.py - Triggered when agent calls end_task() tool  
class EndTaskProcess:
    """Handles task completion - triggered by agent tool call"""
    
    async def execute(self, task_id: int, result: str, agent_assessment: str = ""):
        task = await self.sys.get_task(task_id)
        
        # Create evaluation subtask
        evaluation_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Evaluate completion quality of: {task.instruction}",
            agent_type="task_evaluator",
            context=["task_evaluator_guide"],
            parameters={
                "task_result": result,
                "agent_assessment": agent_assessment,
                "original_task": task.instruction
            }
        )
        
        # Create summary subtask (parallel with evaluation)
        summary_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Summarize outcomes from: {task.instruction}",
            agent_type="summary_agent",
            context=["summary_agent_guide"],
            parameters={
                "task_result": result,
                "task_context": task.instruction
            }
        )
        
        # Wait for both evaluation and summary
        await self.sys.wait_for_tasks([evaluation_task_id, summary_task_id])
        
        # Get results
        evaluation = await self.sys.get_task_result(evaluation_task_id)
        summary = await self.sys.get_task_result(summary_task_id)
        
        # Determine final task state based on evaluation
        if evaluation.quality_acceptable:
            await self.sys.update_task_state(task_id, TaskState.COMPLETED)
            await self.sys.set_task_result(task_id, {
                "result": result,
                "summary": summary.content,
                "evaluation": evaluation
            })
            
            # The runtime will automatically trigger dependent tasks
            
            # Create documentation subtask if recommended
            if evaluation.suggests_documentation:
                doc_task_id = await self.sys.create_subtask(
                    parent_id=task_id,
                    instruction=f"Document insights from: {task.instruction}",
                    agent_type="documentation_agent",
                    context=["documentation_agent_guide"]
                )
        else:
            # Task failed evaluation - could trigger recovery
            await self.sys.update_task_state(task_id, TaskState.FAILED)
            await self.sys.set_task_error(task_id, evaluation.failure_reason)
        
        return {"status": "task_completion_processed", "accepted": evaluation.quality_acceptable}

# create_subtask_process.py - Triggered when agent calls create_subtask() tool
class CreateSubtaskProcess:
    """Handles individual subtask creation requests from agents"""
    
    async def execute(self, parent_task_id: int, subtask_instruction: str, **kwargs):
        # Create the subtask - will go through neutral_task process unless specified
        subtask_id = await self.sys.create_subtask(
            parent_id=parent_task_id,
            instruction=subtask_instruction,
            process=kwargs.get("process", "neutral_task"),
            priority=kwargs.get("priority", "normal"),
            **kwargs
        )
        
        # Add as dependency to parent task
        await self.sys.add_task_dependencies(parent_task_id, [subtask_id])
        
        # Parent task now waits for this subtask
        await self.sys.update_task_state(parent_task_id, TaskState.WAITING_ON_DEPENDENCIES)
        
        return {"subtask_id": subtask_id, "status": "subtask_created"}
```

#### 3. Resource Request Processes
**Handle Dynamic Resource Addition - Triggered by Tool Calls**

```python
# need_more_context_process.py - Triggered when agent calls need_more_context() tool
class NeedMoreContextProcess:
    """Handles agent requests for additional context during task execution"""
    
    async def execute(self, requesting_task_id: int, context_request: str, justification: str = ""):
        requesting_task = await self.sys.get_task(requesting_task_id)
        
        # Create validation subtask first
        validation_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Validate context request: {context_request}. Justification: {justification}",
            agent_type="request_validation",
            context=["request_validation_guide"],
            parameters={
                "task": requesting_task.instruction,
                "current_context": requesting_task.additional_context,
                "request": context_request,
                "justification": justification
            }
        )
        
        await self.sys.wait_for_tasks([validation_task_id])
        validation_result = await self.sys.get_task_result(validation_task_id)
        
        if not validation_result.approved:
            # Add denial message to requesting task conversation
            await self.sys.add_system_message(
                requesting_task_id, 
                f"Context request denied: {validation_result.feedback}"
            )
            
            # Parent task can continue without additional context
            await self.sys.update_task_state(requesting_task_id, TaskState.READY_FOR_AGENT)
            return {"status": "request_denied", "feedback": validation_result.feedback}
        
        # Create context provision subtask
        context_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Provide context for: {context_request}",
            agent_type="context_addition",
            context=["context_addition_guide"],
            parameters={
                "context_request": context_request,
                "task_context": requesting_task.instruction
            }
        )
        
        # Create investigation subtask if validation says it's needed
        subtask_ids = [context_task_id]
        if validation_result.requires_investigation:
            investigation_task_id = await self.sys.create_subtask(
                parent_id=requesting_task_id,
                instruction=f"Investigate: {context_request}",
                agent_type="investigator_agent", 
                context=["investigator_agent_guide"]
            )
            subtask_ids.append(investigation_task_id)
        
        # Parent task waits for context provision
        await self.sys.add_task_dependencies(requesting_task_id, subtask_ids)
        await self.sys.update_task_state(requesting_task_id, TaskState.WAITING_ON_DEPENDENCIES)
        
        return {"status": "context_provision_initiated", "subtasks": subtask_ids}

# need_more_tools_process.py - Triggered when agent calls need_more_tools() tool
class NeedMoreToolsProcess:
    """Handles agent requests for additional tools during task execution"""
    
    async def execute(self, requesting_task_id: int, tool_request: str, justification: str = ""):
        requesting_task = await self.sys.get_task(requesting_task_id)
        
        # Create validation subtask
        validation_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Validate tool request: {tool_request}. Justification: {justification}",
            agent_type="request_validation",
            context=["request_validation_guide"],
            parameters={
                "task": requesting_task.instruction,
                "current_tools": requesting_task.additional_tools,
                "request": tool_request,
                "justification": justification
            }
        )
        
        await self.sys.wait_for_tasks([validation_task_id])
        validation_result = await self.sys.get_task_result(validation_task_id)
        
        if not validation_result.approved:
            await self.sys.add_system_message(
                requesting_task_id,
                f"Tool request denied: {validation_result.feedback}"
            )
            await self.sys.update_task_state(requesting_task_id, TaskState.READY_FOR_AGENT)
            return {"status": "request_denied", "feedback": validation_result.feedback}
        
        # Create tool provision subtask
        tool_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Provide or create tool for: {tool_request}",
            agent_type="tool_addition",
            context=["tool_addition_guide"],
            parameters={
                "tool_request": tool_request,
                "task_context": requesting_task.instruction
            }
        )
        
        await self.sys.add_task_dependencies(requesting_task_id, [tool_task_id])
        await self.sys.update_task_state(requesting_task_id, TaskState.WAITING_ON_DEPENDENCIES)
        
        return {"status": "tool_provision_initiated", "subtasks": [tool_task_id]}
```

#### 4. System Review and Investigation Processes
**Handle Quality Assurance and Deep Analysis - Triggered by Tool Calls**

```python
# flag_for_review_process.py
class FlagForReviewProcess:
    """Handles flagging items for human or system review"""
    
    async def execute(self, flagging_task_id: int, flag_reason: str, severity: str = "normal"):
        flagging_task = await self.sys.get_task(flagging_task_id)
        
        # 1. Create review subtask
        review_task_id = await self.sys.create_subtask(
            parent_id=flagging_task_id,
            instruction=f"Review flagged issue: {flag_reason}",
            agent_type="review_agent",
            context=["review_agent_guide"],
            parameters={
                "flag_reason": flag_reason,
                "severity": severity,
                "context": flagging_task.instruction
            }
        )
        
        # 2. Create investigation subtask if high severity
        if severity in ["high", "critical"]:
            investigation_task_id = await self.sys.create_subtask(
                parent_id=flagging_task_id,
                instruction=f"Investigate root cause of: {flag_reason}",
                agent_type="investigator_agent",
                context=["investigator_agent_guide"]
            )
            
            return {"status": "review_and_investigation_initiated", 
                   "subtasks": [review_task_id, investigation_task_id]}
        
        return {"status": "review_initiated", "subtasks": [review_task_id]}

# investigate_process.py
class InvestigateProcess:
    """Handles deep investigation requests"""
    
    async def execute(self, investigation_request: str, context_task_id: int = None):
        # 1. Create investigation subtask with broad tools
        investigation_task_id = await self.sys.create_subtask(
            parent_id=context_task_id,
            instruction=f"Conduct investigation: {investigation_request}",
            agent_type="investigator_agent",
            context=["investigator_agent_guide"],
            additional_tools=["web_search", "system_browser"]  # Give investigator broad capabilities
        )
        
        # 2. Create summary subtask to distill findings
        summary_task_id = await self.sys.create_subtask(
            parent_id=context_task_id,
            instruction=f"Summarize investigation findings for: {investigation_request}",
            agent_type="summary_agent",
            dependencies=[investigation_task_id]
        )
        
        return {"status": "investigation_initiated", 
               "subtasks": [investigation_task_id, summary_task_id]}
```

#### 5. System Maintenance Processes
**Triggered by Events/Counters**

```python
# optimization_review_process.py
class OptimizationReviewProcess:
    """Triggered by rolling event counters to optimize system entities"""
    
    async def execute(self, entity_type: str, entity_id: int, trigger_reason: str):
        # 1. Gather comprehensive performance data
        performance_data = await self.sys.get_entity_performance_data(entity_type, entity_id)
        usage_patterns = await self.sys.get_entity_usage_patterns(entity_type, entity_id)
        
        # 2. Create optimization analysis subtask
        analysis_task_id = await self.sys.create_subtask(
            parent_id=None,  # System-level task
            instruction=f"Analyze and optimize {entity_type} {entity_id} based on usage patterns",
            agent_type="optimizer_agent",
            context=["optimizer_agent_guide", f"{entity_type}_optimization_guide"],
            parameters={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "performance_data": performance_data,
                "usage_patterns": usage_patterns,
                "trigger_reason": trigger_reason
            }
        )
        
        # 3. Wait for analysis and implement approved optimizations
        await self.sys.wait_for_tasks([analysis_task_id])
        optimization_result = await self.sys.get_task_result(analysis_task_id)
        
        # 4. Apply optimizations (system function)
        for optimization in optimization_result.approved_optimizations:
            await self.sys.implement_optimization(entity_type, entity_id, optimization)
        
        # 5. Reset rolling counter and log optimization
        await self.sys.reset_review_counter(entity_type, entity_id)
        await self.sys.log_event("optimization_completed", entity_id, 
                                optimizations=optimization_result.approved_optimizations)
        
        return {"optimizations_applied": len(optimization_result.approved_optimizations)}

# compact_context_process.py  
class CompactContextProcess:
    """Handles context optimization and compression"""
    
    async def execute(self, task_id: int, context_documents: List[str]):
        task = await self.sys.get_task(task_id)
        
        # Create context optimization subtask
        optimization_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Optimize and compact context documents for better efficiency",
            agent_type="context_addition",
            context=["context_optimization_guide"],
            parameters={
                "documents": context_documents,
                "task_focus": task.instruction
            }
        )
        
        await self.sys.wait_for_tasks([optimization_task_id])
        result = await self.sys.get_task_result(optimization_task_id)
        
        # Update task with optimized context
        await self.sys.update_task(task_id, additional_context=result.optimized_documents)
        
        return {"status": "context_optimized", "documents_reduced": result.optimization_stats}
```

## Core System Functions Library

### Essential System Functions
```python
class SystemFunctions:
    # Task Lifecycle Management
    async def create_task(self, instruction: str, process: str = "neutral_task", **kwargs) -> int:
        """Create task and immediately apply specified process (default: neutral_task)"""
        
    async def create_subtask(self, parent_id: int, instruction: str, **kwargs) -> int:
        """Create subtask with parent relationship and dependency tracking"""
        
    async def get_task(self, task_id: int) -> Task:
        """Retrieve complete task entity with current status"""
        
    async def update_task(self, task_id: int, **updates) -> bool:
        """Update task entity fields and log change event"""
        
    async def mark_task_complete(self, task_id: int, result: str) -> bool:
        """Mark task complete and trigger dependent task processing"""
        
    async def mark_task_failed(self, task_id: int, error: str) -> bool:
        """Mark task failed and trigger recovery processes if configured"""
    
    # Process Orchestration  
    async def execute_process(self, process_name: str, **parameters) -> ProcessResult:
        """Execute named process with parameters"""
        
    async def call_agent(self, agent_type: str, instruction: str, 
                        context: List[str] = None, parameters: Dict = None) -> AgentResult:
        """Make strategic LLM call to specified agent type"""
        
    async def wait_for_tasks(self, task_ids: List[int], timeout: int = None) -> List[TaskResult]:
        """Wait for completion of specified tasks"""
    
    # Resource Management
    async def add_context_to_task(self, task_id: int, context_docs: List[str]) -> bool:
        """Add context documents to task entity"""
        
    async def add_tools_to_task(self, task_id: int, tools: List[str]) -> bool:
        """Add tools to task entity"""
        
    async def create_context_document(self, name: str, content: str, **metadata) -> str:
        """Create new context document entity"""
    
    # Dependency and Event Management
    async def trigger_dependent_tasks(self, completed_task_id: int) -> List[int]:
        """Check and trigger tasks that were waiting for this completion"""
        
    async def log_event(self, event_type: str, entity_id: int, **data) -> str:
        """Log system event for optimization analysis"""
        
    async def increment_counter(self, entity_type: str, entity_id: int, counter_type: str) -> bool:
        """Increment rolling review counter, returns True if threshold reached"""
    
    # Performance and Optimization
    async def get_entity_performance_data(self, entity_type: str, entity_id: int) -> PerformanceData:
        """Retrieve performance analytics for entity optimization"""
        
    async def implement_optimization(self, entity_type: str, entity_id: int, optimization: Optimization) -> bool:
        """Apply approved optimization to entity"""
```

## Key Design Principles

### 1. Process Assignment Strategy
```python
# When task is created:
def create_task(instruction: str, process: str = None, **kwargs):
    if process is None:
        process = "neutral_task"  # Default fallback process
    
    task_id = create_task_entity(instruction, **kwargs)
    execute_process(process, task_id=task_id)  # Immediate process application
    return task_id
```

### 2. Agent Tool Integration
Each agent has access to core tools that trigger processes:
- `break_down_task()` → triggers `BreakDownTaskProcess`
- `create_subtask()` → triggers `CreateSubtaskProcess`  
- `end_task()` → triggers `EndTaskProcess`
- `need_more_context()` → triggers `NeedMoreContextProcess`
- `need_more_tools()` → triggers `NeedMoreToolsProcess`
- `flag_for_review()` → triggers `FlagForReviewProcess`

### 3. Rolling Counter Integration
```python
# After every significant entity operation:
counter_triggered = await sys.increment_counter(entity_type, entity_id, "usage")
if counter_triggered:
    await sys.execute_process("optimization_review", 
                             entity_type=entity_type, 
                             entity_id=entity_id,
                             trigger_reason="usage_threshold")
```

### 4. Failure Recovery
```python
# Each process includes error handling:
try:
    result = await process_step()
except ProcessError as e:
    if self.has_recovery_strategy(e):
        await self.execute_recovery_strategy(e)
    else:
        await sys.create_subtask(
            instruction=f"Recover from process failure: {e}",
            agent_type="recovery_agent"
        )
```

## Process Design Principles

### 1. **Process-Runtime Separation**
- **Processes**: Handle task preparation, orchestration, and coordination
- **Runtime**: Manages LLM conversation flow and automatic task progression

### 2. **Subtask Creation Pattern**
Processes create subtasks for agent work rather than making direct LLM calls:

```python
# Standard pattern for process implementation
class AnyProcess:
    async def execute(self, **params):
        # 1. Create subtasks for agent work
        subtask_id = await self.sys.create_subtask(
            instruction="Specific agent instruction",
            agent_type="appropriate_agent_type",
            context=["relevant_context_documents"]
        )
        
        # 2. Wait for subtasks if coordination needed
        await self.sys.wait_for_tasks([subtask_id])
        
        # 3. Process results and set parent task state
        result = await self.sys.get_task_result(subtask_id)
        await self.sys.update_task_state(parent_id, TaskState.READY_FOR_AGENT)
        
        # Runtime automatically continues parent task conversation
```

### 3. **Tool Call Integration**
Agent tool calls trigger specific processes by creating subtasks:
- `break_down_task()` → `BreakDownTaskProcess`
- `end_task()` → `EndTaskProcess`
- `need_more_context()` → `NeedMoreContextProcess`
- `create_subtask()` → `CreateSubtaskProcess`

### 4. **Dependency Management**
Processes set up dependencies through subtask creation; Runtime handles automatic continuation when dependencies resolve.

This architecture ensures clean separation of concerns and enables automatic task progression through the Runtime engine.