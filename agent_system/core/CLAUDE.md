# CLAUDE.md - Core System Logic

## Module Overview

The core module contains the fundamental system logic for The System's process-first recursive agent architecture. It implements the entity-based design pattern with 6 core entity types, the universal agent runtime, knowledge system, event tracking, and process frameworks that enable systematic task execution.

## Key Components

- **entities/**: Entity definitions and management system with type-specific managers
- **universal_agent_runtime.py**: Core agent execution engine with process boundaries
- **processes/**: Process framework definitions and task execution patterns
- **knowledge/**: Context assembly engine and knowledge gap detection
- **events/**: Comprehensive event tracking and system optimization
  - **analyzers/**: Modular event analysis components (pattern, performance, success, optimization)
- **runtime/**: State machine and dependency management for agent execution
- **types.py**: Comprehensive TypedDict library for type safety
- **ai_models.py**: AI model integration and configuration management

## Common Tasks

### Adding a New Entity Type
1. Create entity definition in `entities/[entity_name]_entity.py`
2. Add type-specific manager in `entities/managers/[entity_name]_manager.py`
3. Register in `EntityManager` facade via property
4. Update `EntityType` enum in `events/event_types.py`
5. Add database schema migration
6. Test entity CRUD operations

### Creating a Process Framework
1. Define process class inheriting from `processes/base.py`
2. Implement required methods: `analyze_domain()`, `establish_framework()`
3. Register in `processes/registry.py`
4. Create process validation tests
5. Document framework patterns and success criteria

### Integrating New AI Model
1. Add model configuration to `ai_models.py`
2. Update `ModelConfig` TypedDict in `types.py`
3. Test model integration with runtime
4. Add model-specific error handling
5. Document model capabilities and limits

### Adding Knowledge Entities
1. Create JSON files in `../knowledge/[type]/` directory
2. Use knowledge entity format from bootstrap conversion
3. Test knowledge assembly with context engine
4. Validate knowledge completeness for task success
5. Monitor knowledge usage and effectiveness

### Working with Event Analyzers
1. Import specific analyzer from `events/analyzers/`
2. Each analyzer specializes in different analysis aspects:
   - `EventPatternAnalyzer`: Detect patterns and anomalies
   - `SuccessPatternDetector`: Identify success patterns
   - `EventPerformanceAnalyzer`: Analyze performance metrics
   - `OptimizationDetector`: Find optimization opportunities
3. For backward compatibility, use `event_analyzer` module
4. Analyzers operate independently without shared state
5. All analyzers return structured result objects

## Architecture & Patterns

- **Entity-Based Design**: 6 fundamental entity types (Agent, Task, Tool, Document, Process, Event)
- **Facade Pattern**: EntityManager provides unified interface to type-specific managers
- **Process-First Architecture**: Systematic framework establishment before execution
- **Event-Driven**: Comprehensive tracking enables system optimization
- **Type Safety**: Extensive TypedDict usage for better IDE support
- **Isolation Boundaries**: Tasks designed for independent success with context

## Testing

### Entity Testing
```python
# Test entity CRUD through manager
manager = AgentManager(db_path)
agent = await manager.create({
    "name": "test_agent",
    "instruction": "Test instruction"
})
assert agent.name == "test_agent"
```

### Process Testing
```python
# Test process framework establishment
process = TestProcess()
framework = await process.establish_framework(domain_data)
assert framework.completeness_score > 0.8
```

### Runtime Testing
```python
# Test agent execution within boundaries
runtime = UniversalAgentRuntime()
result = await runtime.execute_task(task_id, agent_id)
assert result.status == "completed"
```

## Performance Considerations

- **Entity Manager Caching**: Individual caches per entity type for memory efficiency
- **Database Connection Pooling**: Async SQLite with proper connection management
- **Knowledge Assembly**: Lazy loading with caching for context packages
- **Event Processing**: Batched event writes for high-throughput scenarios
- **Process Validation**: Cached framework patterns to reduce computation

## Gotchas & Tips

### Entity Management
- Always use EntityManager facade for backward compatibility
- Type-specific managers accessible via properties (e.g., `entity_manager.agents`)
- Event logging automatic for all entity operations

### Process Framework Design
- Never execute tasks without framework establishment
- Ensure isolated success capability for all subtasks
- Use knowledge system to provide complete context
- Validate framework completeness before decomposition

### Runtime Integration
- Universal runtime handles model switching automatically
- Tool execution within process-defined permission boundaries
- State persistence through event system
- Error recovery through systematic patterns

### Knowledge System
- Bootstrap converts existing docs to structured knowledge
- Context assembly provides complete packages for task success
- Gap detection identifies missing knowledge preventing completion
- Usage tracking enables knowledge evolution and optimization

### Debugging Approaches
- Check event logs for complete execution trace
- Use EntityManager queries to inspect system state
- Validate process frameworks before execution
- Monitor knowledge gap detection for context issues

## Integration Points

- **API Layer**: Entities exposed through REST endpoints
- **Web Interface**: Real-time updates via WebSocket integration
- **Tool System**: MCP protocol integration with permission management
- **Database**: SQLite with SQLModel ORM for persistence
- **External AI**: Multi-provider support through model configuration

## Common Patterns

### Creating Type-Specific Operations
```python
# Add to appropriate manager class
class AgentManager(BaseManager):
    async def find_by_capability(self, capability: str) -> List[AgentEntity]:
        # Agent-specific query logic
        return await self._query_by_field("capabilities", capability)
```

### Process Framework Implementation
```python
class CustomProcess(BaseProcess):
    async def establish_framework(self, domain_data: Dict[str, Any]) -> ProcessFramework:
        # Analyze domain requirements
        # Create systematic structure
        # Validate completeness
        return framework
```

### Knowledge Entity Creation
```json
{
  "id": "unique-id",
  "type": "pattern",
  "name": "Task Decomposition Pattern",
  "description": "Systematic approach to breaking down complex tasks",
  "content": {
    "steps": [...],
    "validation": [...],
    "examples": [...]
  }
}
```