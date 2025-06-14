# Real-time UI Architecture

## Overview

This document describes the real-time UI architecture for the self-improving agent system, implementing a chat-like interface with thread-based task visualization, real-time updates, and debugging controls.

## Core Requirements

1. **Real-time Updates**: Live streaming of agent messages, tool calls, and system events
2. **Thread-based View**: Each task tree displayed as a separate thread with ability to switch between them
3. **Parallel Task Control**: Configurable maximum number of concurrent agent threads
4. **Step Mode**: Debugging feature to pause agent execution and manually trigger each LLM call
5. **Full History**: Complete visibility into all agent activities including closed threads

## Architecture Design

### Backend Components

#### 1. Enhanced WebSocket Protocol
Instead of implementing the full ag-ui protocol (which would require significant refactoring), we'll enhance our existing WebSocket system with structured message types:

```python
class MessageType(Enum):
    # Agent lifecycle
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    
    # System events
    SYSTEM_MESSAGE = "system_message"
    USER_MESSAGE = "user_message"
    STEP_MODE_PAUSE = "step_mode_pause"
    
class WebSocketMessage:
    type: MessageType
    task_id: int
    tree_id: int
    agent_name: str
    content: dict
    timestamp: datetime
```

#### 2. Message Broadcasting System
Modify the `UniversalAgent` to emit WebSocket messages at key points:
- Before/after LLM calls
- Before/after tool execution
- On state changes
- On errors

#### 3. Step Mode Implementation
Add a pause mechanism in the agent execution flow:
```python
class TaskManager:
    step_mode_enabled: bool = False
    paused_agents: Dict[int, asyncio.Event] = {}
    
    async def pause_for_step(self, task_id: int):
        if self.step_mode_enabled:
            event = asyncio.Event()
            self.paused_agents[task_id] = event
            await self.broadcast_step_pause(task_id)
            await event.wait()
```

#### 4. Parallel Task Limiting
Enhance the existing `max_concurrent_agents` with dynamic configuration:
```python
@app.put("/system/config")
async def update_config(config: SystemConfig):
    task_manager.max_concurrent_agents = config.max_parallel_tasks
    task_manager.step_mode_enabled = config.step_mode
```

### Frontend Components

#### 1. Thread List Component
- Display all task trees (threads) with status indicators
- Show latest activity timestamp
- Filter controls (active/completed/all)
- Click to switch between threads

#### 2. Message Stream Component
- Real-time message display with different types:
  - Agent thoughts (thinking)
  - Tool calls with inputs/outputs
  - System messages
  - User messages
  - Error messages
- Auto-scroll with manual override
- Timestamp display

#### 3. Control Panel Component
- Max parallel tasks slider (1-10)
- Step mode toggle (global and per-thread)
- "Continue" button for step mode
- Thread status indicators

#### 4. WebSocket Manager
Enhanced WebSocket handling with reconnection and message queuing:
```javascript
class WebSocketManager {
  constructor(url, onMessage) {
    this.url = url;
    this.onMessage = onMessage;
    this.messageQueue = [];
    this.reconnectDelay = 1000;
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.onMessage(message);
    };
    // Handle reconnection logic
  }
}
```

## Implementation Plan

### Phase 1: Backend WebSocket Enhancement
1. Create structured message types and broadcasting system
2. Modify UniversalAgent to emit real-time messages
3. Add message persistence to database for history
4. Implement step mode pause mechanism

### Phase 2: Frontend Thread View
1. Create thread list component with filtering
2. Implement message stream with auto-scroll
3. Add WebSocket manager with reconnection
4. Style with clean, modern UI

### Phase 3: Control Features
1. Add control panel with settings
2. Implement step mode UI with continue button
3. Add parallel task limit control
4. Test debugging workflows

### Phase 4: Polish & Documentation
1. Add loading states and error handling
2. Implement message search/filter
3. Add keyboard shortcuts
4. Update system documentation

## Benefits of This Approach

1. **Minimal Refactoring**: Works with existing task/agent system
2. **Immediate Value**: Provides debugging capabilities quickly
3. **Extensible**: Can add ag-ui protocol later if needed
4. **Self-Documenting**: All changes visible to agents for self-improvement

## Implementation Status

### ✅ Completed Features

1. **Backend WebSocket Enhancement**
   - Created structured message types (WebSocketMessage, MessageBuilder)
   - Modified UniversalAgent to broadcast real-time updates
   - Added step mode pause mechanism with async events
   - Implemented configuration endpoints for dynamic control

2. **Frontend Thread View**
   - ThreadList component with filtering and status indicators
   - MessageStream component with auto-scroll and message types
   - WebSocket manager with automatic reconnection
   - Clean, modern dark theme UI

3. **Control Features**
   - Control panel with max parallel tasks slider
   - Global and per-thread step mode toggles
   - Continue button for paused tasks
   - Real-time configuration updates via WebSocket

4. **Message Types Implemented**
   - agent_started: Shows when agent begins execution
   - agent_thinking: Displays agent's thought process
   - agent_tool_call: Shows tool invocations with parameters
   - agent_tool_result: Displays tool execution results
   - step_mode_pause: Indicates pause points for debugging
   - system events: Task creation, completion, errors

## Usage Guide

### Basic Operation
1. Visit https://system.petter.ai
2. Enter a task instruction in the input field
3. Press Enter or click "Submit Task" to create a new thread
4. Watch real-time updates as agents work on your task

### Thread Management
- Click on any thread in the left sidebar to view its messages
- Active threads show a pulsing blue indicator
- Completed threads show a green checkmark
- Failed threads show a red X
- Toggle "Show completed" to filter thread list

### Debugging with Step Mode
1. Enable "Global Step Mode" to pause all agents before LLM calls
2. Or enable step mode for specific threads
3. When paused, click "Continue" to proceed to next step
4. Use this to debug agent behavior and inspect tool calls

### Parallel Task Control
- Adjust the "Max Parallel Tasks" slider (1-10)
- System will queue additional tasks when limit is reached
- Useful for controlling resource usage and debugging

## Architecture Benefits

1. **Real-time Visibility**: Complete transparency into agent operations
2. **Debugging Support**: Step-by-step execution for troubleshooting
3. **Resource Control**: Dynamic adjustment of parallel execution
4. **Thread Isolation**: Each task tree in its own conversation thread
5. **Extensible Design**: Easy to add new message types and features

## Future Enhancements

1. **Message Search**: Add ability to search within threads
2. **Export Functionality**: Export thread history as markdown/JSON
3. **Advanced Filtering**: Filter by message type, agent, or time
4. **Keyboard Shortcuts**: Navigate threads and control execution
5. **Performance Metrics**: Display token usage and execution times