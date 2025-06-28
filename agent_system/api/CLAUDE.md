# CLAUDE.md - Web API Interface

## Module Overview

The API module provides a comprehensive FastAPI-based web interface for The System. It implements modular endpoint organization with task management, entity operations, admin controls, and real-time WebSocket communication. The API serves as the primary interface for task submission, system monitoring, and agent orchestration.

## Key Components

- **main.py**: Core FastAPI application with middleware and routing (220 lines)
- **routes/**: Modular endpoint organization
  - `tasks.py`: Task submission, monitoring, and tree management (287 lines)
  - `entities.py`: Entity CRUD operations for all 6 entity types (243 lines)
  - `admin.py`: System administration and control endpoints (359 lines)
- **websocket/handlers.py**: Real-time communication and updates (159 lines)
- **middleware/exception_handler.py**: Centralized error handling
- **exceptions.py**: Custom exception definitions
- **startup.py**: Application lifecycle management (155 lines)

## Common Tasks

### Adding New API Endpoint
1. Create endpoint function in appropriate route module
2. Define request/response models using Pydantic
3. Add proper error handling (exceptions handled by middleware)
4. Update OpenAPI documentation with descriptions
5. Test endpoint with various input scenarios

### Creating WebSocket Handler
1. Add handler function to `websocket/handlers.py`
2. Implement message routing and validation
3. Add real-time update logic for task status
4. Test WebSocket connection and message flow
5. Document message format and behavior

### Adding Request/Response Model
1. Create Pydantic model class in appropriate route file
2. Use existing patterns for validation and documentation
3. Integrate with TypedDict types from `core/types.py`
4. Add model to endpoint function signatures
5. Test model validation and serialization

### Updating Middleware
1. Modify middleware in `middleware/` directory
2. Update middleware registration in `main.py`
3. Test middleware behavior across all endpoints
4. Validate error handling and logging
5. Document middleware functionality

## Architecture & Patterns

- **Modular Router Design**: Separate routers for logical endpoint grouping
- **Dependency Injection**: Database and runtime dependencies injected properly
- **Centralized Exception Handling**: Middleware handles all exceptions consistently
- **WebSocket Integration**: Real-time updates for task execution monitoring
- **Automatic Documentation**: OpenAPI/Swagger documentation auto-generated
- **CORS Support**: Proper cross-origin request handling for web UI

## API Endpoint Categories

### Task Management (`/tasks`)
- `POST /tasks`: Submit new task for execution
- `GET /tasks/tree/{tree_id}`: Get complete task tree status
- `GET /tasks/{task_id}`: Get individual task details
- `PUT /tasks/{task_id}/pause`: Pause task execution
- `PUT /tasks/{task_id}/resume`: Resume paused task
- `DELETE /tasks/{task_id}`: Cancel task execution

### Entity Operations (`/entities`)
- `GET /entities/{entity_type}`: List entities by type
- `POST /entities/{entity_type}`: Create new entity
- `GET /entities/{entity_type}/{id}`: Get specific entity
- `PUT /entities/{entity_type}/{id}`: Update entity
- `DELETE /entities/{entity_type}/{id}`: Delete entity

### System Administration (`/admin`)
- `GET /health`: System health check and status
- `POST /admin/init`: Initialize or reinitialize system
- `GET /admin/stats`: System performance and usage statistics
- `POST /admin/cleanup`: Clean up completed tasks and optimize
- `GET /admin/logs`: Retrieve system logs and events

### Real-time Updates (WebSocket `/ws`)
- Task status updates and progress monitoring
- Agent execution notifications
- System health and performance updates
- Error notifications and alerts

## Testing

### Endpoint Testing
```python
# Test API endpoint
from fastapi.testclient import TestClient
client = TestClient(app)

response = client.post("/tasks", json={
    "instruction": "Test task",
    "priority": 1
})
assert response.status_code == 200
```

### WebSocket Testing
```python
# Test WebSocket connection
with client.websocket_connect("/ws") as websocket:
    data = websocket.receive_json()
    assert data["type"] == "task_update"
```

### Exception Handling Testing
```python
# Test error handling
response = client.get("/tasks/99999")
assert response.status_code == 404
assert response.json()["type"] == "not_found"
```

## Performance Considerations

- **Async Operations**: All endpoints use async/await for non-blocking execution
- **Database Connection Pooling**: Efficient connection management
- **WebSocket Management**: Connection lifecycle and cleanup
- **Response Streaming**: Large responses streamed for memory efficiency
- **Caching**: Strategic caching for frequently accessed data

## Gotchas & Tips

### Endpoint Development
- Use centralized exception handling - don't catch exceptions in endpoints
- Follow existing Pydantic model patterns for consistency
- Add proper OpenAPI documentation with descriptions and examples
- Test all error scenarios including validation failures
- Use dependency injection for database and runtime access

### WebSocket Implementation
- Handle connection lifecycle properly (connect/disconnect)
- Implement message validation and error handling
- Use async patterns for real-time updates
- Test connection stability under load
- Document message format and expected behavior

### Request/Response Design
- Use clear, descriptive model names
- Include validation rules and constraints
- Provide meaningful error messages
- Follow REST conventions for endpoint design
- Keep response models focused and minimal

### Error Handling
- Custom exceptions automatically handled by middleware
- Use appropriate HTTP status codes
- Include error context and helpful messages
- Log errors with sufficient detail for debugging
- Don't expose internal system details in error responses

### Security Considerations
- Validate all input data through Pydantic models
- Implement proper CORS configuration
- Use secure headers and middleware
- Validate WebSocket connections and messages
- Sanitize log output to prevent information disclosure

## Integration Points

- **Universal Agent Runtime**: Direct integration for task execution
- **Entity Manager**: All CRUD operations through entity management layer
- **Event System**: Real-time updates via event tracking
- **Knowledge System**: Context requests and knowledge gap reporting
- **Web Interface**: React frontend consumes API and WebSocket updates

## Common Patterns

### Endpoint Function Pattern
```python
@router.post("", response_model=TaskResponse)
async def create_task(request: TaskSubmission, db: DatabaseManager = Depends(get_db)):
    # No try-catch needed - middleware handles exceptions
    result = await task_service.create_task(request.dict())
    return TaskResponse(**result)
```

### WebSocket Handler Pattern
```python
async def handle_task_updates(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Listen for events and send updates
            event = await event_manager.get_next_event()
            await websocket.send_json(event.to_dict())
    except WebSocketDisconnect:
        # Handle cleanup
        pass
```

### Custom Exception Pattern
```python
# Define in exceptions.py
class TaskNotFoundError(EntityNotFoundError):
    def __init__(self, task_id: int):
        super().__init__(f"Task {task_id} not found")

# Use in endpoint
if not task:
    raise TaskNotFoundError(task_id)
```

### Dependency Injection Pattern
```python
async def get_database() -> DatabaseManager:
    return DatabaseManager()

async def get_runtime() -> RuntimeIntegration:
    return RuntimeIntegration()

# Use in endpoint
async def endpoint(db: DatabaseManager = Depends(get_database)):
    # Use db for operations
```