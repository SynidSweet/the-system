# New UI Features - Agent System Browser

I've added three new browsing interfaces to give you better visibility into the agent system:

## 1. Agent Browser

Navigate to the "Agents" tab to:
- View all agents in the system
- See complete agent configurations including:
  - Instructions
  - Available tools
  - Context documents
  - Model configuration
  - Permissions
- **Edit agents directly** from the UI
- Changes are saved to the database immediately

### Key Features:
- List view showing all active agents
- Detailed view with all agent properties
- Edit mode for modifying instructions, tools, documents, etc.
- JSON editing for complex fields (tools, permissions, model config)
- Visual chips for tools and documents

## 2. Tool Browser

Navigate to the "Tools" tab to:
- Browse all available MCP tools by category:
  - **Core tools**: Essential MCP tools for agent collaboration
  - **System tools**: Internal system management tools
  - **Custom tools**: User-defined tools
- View detailed tool information:
  - Description
  - Parameters with types and requirements
  - Required permissions
  - Usage examples

### Key Features:
- Categorized tool listing
- Parameter documentation with required/optional indicators
- Auto-generated usage examples
- Permission requirements display

## 3. Document Browser

Navigate to the "Documents" tab to:
- Browse all context documents
- Filter documents by name, title, or category
- View document content
- **Edit documents directly** from the UI
- See metadata (format, size, timestamps)

### Key Features:
- Searchable document list
- Documents grouped by category
- Full content editor with syntax highlighting
- Metadata display
- Save changes directly to database

## Navigation

The main navigation bar now includes four tabs:
- **Tasks**: Original task submission and monitoring interface
- **Agents**: Browse and edit agent configurations
- **Tools**: Explore available tools and their usage
- **Documents**: View and edit context documents

## Technical Implementation

### Backend Endpoints Added:
- `PUT /agents/{agent_name}` - Update agent configuration
- `GET /documents` - List all documents with metadata
- `GET /documents/{doc_name}` - Get document content
- `PUT /documents/{doc_name}` - Update document content
- Enhanced `GET /system/tools` - Now returns detailed tool information

### Frontend Components:
- `AgentBrowser.js` - Agent browsing and editing interface
- `ToolBrowser.js` - Tool exploration interface
- `DocumentBrowser.js` - Document viewing and editing interface
- Corresponding CSS files for each component

## Usage Tips

1. **Editing Agents**: 
   - Click on an agent to view details
   - Click "Edit" to modify
   - Arrays and objects must be valid JSON
   - Save to persist changes

2. **Understanding Tools**:
   - Browse by category to find relevant tools
   - Check parameter requirements before using
   - Note permission requirements for restricted tools

3. **Managing Documents**:
   - Use the filter to quickly find documents
   - Edit content directly in the browser
   - Changes are saved with timestamps

The UI now provides full visibility and control over the agent system's configuration!