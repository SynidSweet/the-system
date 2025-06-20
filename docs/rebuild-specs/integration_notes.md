# Integration Notes: Process Architecture and Runtime System

## Overview

The new process architecture and runtime specifications introduce significant refinements to how the system operates:

1. **Hybrid Python + LLM Architecture**: Processes are now Python scripts that handle deterministic logic and make strategic LLM calls only when needed
2. **Event-Driven Runtime**: The system operates as a pure event-driven dependency resolver with no polling
3. **Neutral Task Process**: A default process for tasks without specific processes assigned
4. **Core Tool Processes**: Processes triggered by agent tool calls during execution

## Key Changes from Original Plan

### 1. Process Implementation Strategy

**Original Plan**: Process templates with parameter substitution and flow control
**New Specification**: Python-based processes with:
- Deterministic logic handling
- Strategic LLM calls only when reasoning needed
- Built-in error handling and rollback
- System function calls for entity operations

### 2. Runtime Architecture

**Original Plan**: Task queue with priority handling and agent spawning
**New Specification**: Event-driven runtime with:
- Task state machine (8 states)
- Automatic state transitions
- Dependency resolution
- No polling - pure event-driven

### 3. Default Task Handling

**New Addition**: Neutral Task Process
- Applied to tasks without specific processes
- Handles agent selection, context assignment, and tool assignment
- Creates subtasks for each decision point

### 4. Tool Process Integration

**New Clarity**: Core tool processes are triggered by agent tool calls:
- `break_down_task()` → `BreakDownTaskProcess`
- `start_subtask()` → `SubtaskSpawnProcess`
- `request_context()` → `ContextAdditionProcess`
- `request_tools()` → `ToolAdditionProcess`

## Impact on Migration Phases

### Phase 3: Entity Management Layer
- No significant changes needed
- Entity base classes still required
- Relationship management remains important

### Phase 4: Process Framework (Needs Update)
Should now focus on:
1. **Python Process Engine**
   - Process base class with system functions
   - Process registry and loading
   - Error handling and rollback framework

2. **Neutral Task Process**
   - Implement as the default process
   - Agent selection logic
   - Context and tool assignment

3. **Core Tool Processes**
   - Implement processes for each core tool
   - Integration with agent tool calls
   - Dependency management

4. **Runtime Engine**
   - Event-driven task progression
   - State machine implementation
   - Dependency graph management

### Phase 5: New Agent Integration
- Agents now work within the process framework
- Tool calls trigger processes instead of direct execution
- Planning agent works through the BreakDownTaskProcess

## Implementation Priorities

1. **Update Phase 4 Plan**: Revise to reflect Python-based processes and runtime engine
2. **Runtime Engine First**: Build the event-driven runtime before processes
3. **Neutral Task Process**: Implement as the foundation for task handling
4. **Tool Process Mapping**: Create processes for each core MCP tool

## Code Structure Implications

```
agent_system/
├── core/
│   ├── runtime/
│   │   ├── engine.py          # RuntimeEngine class
│   │   ├── state_machine.py   # Task state management
│   │   ├── dependency_graph.py # Dependency tracking
│   │   └── event_handler.py   # Event processing
│   ├── processes/
│   │   ├── base.py           # BaseProcess class
│   │   ├── neutral_task.py   # Default task process
│   │   ├── tool_processes/   # Core tool processes
│   │   └── registry.py       # Process registry
```

## Key Concepts to Preserve

1. **Entity-Based Architecture**: Still the foundation
2. **Event System**: Now central to runtime operation
3. **Self-Improvement**: Through process optimization
4. **Parallel Operation**: During migration phases

## Next Steps

1. Update system_update_plan.md Phase 4 to reflect new process architecture
2. Create detailed specifications for runtime engine
3. Design process base class with system functions
4. Plan the transition from current task execution to new runtime