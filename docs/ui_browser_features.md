# UI Browser Features Documentation

## Overview

The agent system web interface now includes three powerful browser interfaces that provide full visibility and control over the system's configuration. These browsers allow real-time exploration and editing of agents, tools, and context documents.

## 1. Agent Browser

The Agent Browser provides a comprehensive interface for viewing and modifying agent configurations.

### Features
- **List View**: Shows all active agents with their basic information
- **Detailed View**: Click any agent to see complete configuration including:
  - Agent instruction (full prompt)
  - Available tools list
  - Context documents
  - Model configuration (LLM settings)
  - Permissions (file system, database, web access, etc.)
  - Constraints and metadata

### Editing Capabilities
- **Direct Editing**: Click "Edit" to modify any agent configuration
- **Real-time Save**: Changes are immediately persisted to the database
- **JSON Validation**: Complex fields (tools, permissions, model config) require valid JSON
- **Visual Feedback**: Chips and badges for easy visualization of tools and documents

### Usage Tips
1. Be careful when editing agent instructions - they define core behavior
2. Tools and context documents must exist in the system before assignment
3. Model configuration changes affect cost and performance
4. Permission changes take effect on next agent execution

## 2. Tool Browser

The Tool Browser provides comprehensive documentation and exploration of all available MCP tools.

### Features
- **Categorized Display**: Tools organized by category
  - Core tools (essential MCP toolkit)
  - System tools (internal operations)
  - Custom tools (user-defined)
- **Detailed Documentation**: Each tool shows
  - Full description
  - Parameter specifications with types
  - Required vs optional parameters
  - Required permissions
  - Auto-generated usage examples

### Tool Categories

#### Core Tools
Essential MCP tools for agent collaboration:
- `break_down_task` - Recursive task decomposition
- `start_subtask` - Spawn specialized agents
- `request_context` - Knowledge expansion
- `request_tools` - Capability discovery
- `end_task` - Task completion
- `flag_for_review` - Human oversight
- `think_out_loud` - Transparent reasoning

#### System Tools
Internal system management:
- `list_agents` - Query available agents
- `list_documents` - Browse context documents
- `list_optional_tools` - Discover available tools
- `query_database` - Direct database access
- `create_agent` - Dynamic agent creation
- `send_message_to_user` - User communication

### Usage Examples
The browser automatically generates usage examples based on tool parameters, showing both required and optional parameter usage patterns.

## 3. Document Browser

The Document Browser provides access to all context documents in the system.

### Features
- **Searchable List**: Filter documents by name, title, or category
- **Category Organization**: Documents grouped by type
  - Agent guides
  - System documentation
  - Process guides
  - Technical references
- **Full Content Display**: View complete document content
- **Direct Editing**: Modify documents in-browser
- **Metadata Display**: Format, version, timestamps, size

### Document Management
- **Edit Mode**: Click "Edit" to modify document content
- **Save Changes**: Updates immediately saved to database
- **Version Tracking**: Updated timestamp recorded
- **Format Support**: Markdown, JSON, plain text

### Usage Tips
1. Use the search filter to quickly find specific documents
2. Check document category to understand its purpose
3. Be careful editing system-critical documents
4. Markdown preview helps verify formatting

## Technical Implementation

### API Endpoints
```
GET  /agents                    # List all agents
GET  /agents/{name}            # Get specific agent
PUT  /agents/{name}            # Update agent

GET  /tools                    # List all tools with details
GET  /tools/{name}             # Get specific tool

GET  /documents                # List all documents
GET  /documents/{name}         # Get document content  
PUT  /documents/{name}         # Update document
```

### Frontend Components
- `AgentBrowser.js` - Agent management interface
- `ToolBrowser.js` - Tool exploration interface
- `DocumentBrowser.js` - Document management interface
- Corresponding CSS files for styling

### WebSocket Integration
All browsers integrate with the WebSocket system for real-time updates when agents modify configurations.

## Security Considerations

1. **Permission Control**: Browsers respect agent permissions - only authorized modifications allowed
2. **Validation**: All inputs validated before database updates
3. **Audit Trail**: All modifications logged in system messages
4. **Safe Defaults**: Dangerous operations require confirmation

## Best Practices

1. **Before Editing Agents**:
   - Understand the agent's role in the system
   - Check which tasks currently use the agent
   - Test changes with simple tasks first

2. **Tool Assignment**:
   - Only assign tools the agent actually needs
   - Check tool permissions match agent permissions
   - Verify tool parameters in Tool Browser first

3. **Document Updates**:
   - Maintain consistent formatting
   - Update version information when making major changes
   - Test that agents can still parse updated documents

## Future Enhancements

Planned improvements include:
- Version history for all edits
- Diff view for changes
- Bulk operations support
- Import/export functionality
- Advanced search and filtering
- Real-time collaboration features