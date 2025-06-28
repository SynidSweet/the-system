# CLAUDE.md - Tool Ecosystem

## Module Overview

The tools module implements The System's comprehensive tool ecosystem using the Model Context Protocol (MCP). It provides three categories of tools: Core MCP tools for task orchestration, System tools for internal operations, and MCP Server integrations for external capabilities. All tools operate within process-defined permission boundaries.

## Key Components

- **base_tool.py**: Abstract base classes for tool implementation and MCP integration
- **core_mcp/**: Essential MCP tools for task decomposition and agent orchestration
- **system_tools/**: Internal system operations and agent management capabilities
- **mcp_servers/**: External integrations (GitHub, terminal, file system, database)

## Common Tasks

### Adding a New Core MCP Tool
1. Create tool class inheriting from `CoreMCPTool` in `core_mcp/core_tools.py`
2. Implement required methods: `__init__()`, `execute()`, `validate_parameters()`
3. Add tool to system seeding configuration in `config/seeds/tools.yaml`
4. Test tool execution within agent runtime
5. Document tool capabilities and usage patterns

### Creating MCP Server Integration
1. Create server implementation in `mcp_servers/[service_name].py`
2. Implement `BaseMCPServer` interface with connection management
3. Add server configuration to system settings
4. Test integration with permission management
5. Add error handling and retry logic

### Adding System Tool
1. Create tool class in appropriate `system_tools/` module
2. Implement internal operation with proper entity management
3. Add permission checks and validation
4. Register tool with system toolset
5. Test integration with agent runtime

### Updating Tool Permissions
1. Modify tool entity in database via EntityManager
2. Update permission constraints in tool configuration
3. Test permission enforcement during execution
4. Validate agent access controls
5. Document permission requirements

## Architecture & Patterns

- **MCP Protocol**: Standard tool integration using Model Context Protocol
- **Permission Management**: Database-driven access control with agent constraints
- **Tool Categories**: Core (task orchestration), System (internal ops), External (integrations)
- **Async Execution**: All tools support asynchronous operation patterns
- **Error Handling**: Comprehensive error capture with metadata and timing
- **Type Safety**: Strong typing with TypedDict integration for parameters/results

## Tool Categories

### Core MCP Tools (6 Essential Tools)
- `break_down_task()`: Recursive task decomposition
- `start_subtask()`: Agent spawning and task creation
- `request_context()`: Knowledge expansion and context requests
- `request_tools()`: Dynamic capability discovery
- `end_task()`: Task completion and result reporting
- `flag_for_review()`: Human oversight escalation

### System Tools
- **Agent Management**: Create, modify, query agent entities
- **Internal Operations**: Entity CRUD, database queries, health checks
- **User Communication**: Optional tool for agent-user messaging
- **MCP Integrations**: Server management and connection handling

### MCP Server Integrations
- **GitHub**: Repository operations, issue management, PR creation
- **Terminal**: Shell command execution with security constraints
- **File System**: File operations within sandboxed boundaries
- **Database**: Direct database queries and schema operations
- **Entity Manager**: System entity management through MCP interface

## Testing

### Tool Execution Testing
```python
# Test tool execution through runtime
tool = BreakDownTaskTool()
result = await tool.execute({
    "task_id": 123,
    "breakdown_criteria": "complexity > 5"
})
assert result.success == True
```

### Permission Testing
```python
# Test tool permission enforcement
agent = await entity_manager.agents.get_by_id(agent_id)
has_permission = await tool.check_permissions(agent, tool_name)
assert has_permission == expected_result
```

### MCP Server Testing
```python
# Test MCP server integration
server = GitHubMCPServer()
await server.connect()
result = await server.call_tool("create_issue", params)
assert result.success == True
```

## Performance Considerations

- **Connection Pooling**: MCP servers maintain persistent connections
- **Async Operations**: All tool calls non-blocking with proper timeout handling
- **Permission Caching**: Agent permissions cached for performance
- **Error Recovery**: Automatic retry logic for transient failures
- **Resource Limits**: Configurable timeouts and resource constraints

## Gotchas & Tips

### Tool Development
- Always inherit from appropriate base class (`CoreMCPTool`, `BaseMCPTool`)
- Implement comprehensive parameter validation
- Use TypedDict types from `core/types.py` for consistency
- Add proper error handling with meaningful messages
- Test tool both individually and within agent runtime

### Permission Management
- Tool permissions stored in database entity records
- Agents must request tools through proper channels
- Permission checks happen at both runtime and tool level
- Default deny policy - explicit permissions required
- Permission changes require entity manager updates

### MCP Integration
- Server connections managed automatically by framework
- Use async/await patterns for all MCP operations
- Implement proper connection error handling
- Test with actual MCP clients for validation
- Follow MCP specification for compatibility

### Error Handling
- Return `MCPToolResult` with success/error fields
- Include execution timing for performance monitoring
- Capture full error context in metadata
- Log errors for debugging and system improvement
- Implement graceful degradation where possible

### Security Considerations
- All external tool calls go through permission checks
- MCP servers run in controlled environment
- File system access limited to safe directories
- Terminal commands filtered for security
- Database access restricted by entity permissions

## Integration Points

- **Universal Agent Runtime**: Tools executed within process boundaries
- **Entity Manager**: Tools access entities through proper management layer
- **Permission System**: Database-driven access control integration
- **Event System**: Tool execution tracked for optimization
- **Knowledge System**: Tools can request context and capabilities

## Common Patterns

### Tool Implementation Pattern
```python
class CustomTool(CoreMCPTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Tool description",
            parameters=["param1", "param2"]
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        # Validate parameters
        # Perform operation
        # Return structured result
        return ToolResult(success=True, result=data)
```

### MCP Server Pattern
```python
class CustomMCPServer(BaseMCPServer):
    async def connect(self):
        # Establish connection
        # Configure server
        
    async def call_tool(self, tool_name: str, params: Dict[str, Any]):
        # Execute tool through MCP protocol
        # Handle errors and timeouts
        # Return standardized result
```

### Permission Check Pattern
```python
async def check_tool_permission(agent_id: int, tool_name: str) -> bool:
    agent = await entity_manager.agents.get_by_id(agent_id)
    return tool_name in agent.available_tools
```