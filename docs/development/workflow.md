# Development Workflow Guide

*Last updated: 2025-06-28 | Updated by: /document command*

## 🚨 Current System Status

**MAJOR REFACTORING COMPLETED** - All architectural improvements have been successfully committed (95 files changed, 14,489 insertions). 

**⚠️ CRITICAL ISSUE**: System initialization is currently blocked by 175 absolute imports across 63 files that need conversion to relative imports. This must be resolved before normal development can proceed.

**Next Steps**: 
1. Fix absolute import paths (P0 priority)
2. Verify system initialization works
3. Resume normal development workflow

## Getting Started

### Prerequisites

- **Python 3.11+** (required for advanced async features)
- **Node.js 18+** (for React frontend development)
- **Git** (for version control and self-modification features)
- **API Keys** for at least one AI provider:
  - Google Gemini API key (recommended - default provider)
  - Anthropic API key (alternative)
  - OpenAI API key (alternative)

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd the-system/agent_system

# Run automated setup
./deploy.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize system
python scripts/seed_system.py
python scripts/bootstrap_knowledge.py

# Start services
./svc start
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the `agent_system` directory:

```bash
# AI Provider Keys (at least one required)
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Default Configuration
DEFAULT_MODEL_PROVIDER=google
DEFAULT_MODEL_NAME=gemini-2.0-flash-exp
MAX_CONCURRENT_AGENTS=3

# Optional Configuration
DATABASE_URL=sqlite:///data/agent_system.db
LOG_LEVEL=INFO
ENABLE_STEP_MODE=false
```

### Initial System Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database and core entities
python scripts/init_system.py

# 3. Seed with all agents and processes (configuration-driven)
python scripts/seed_system.py

# 4. Bootstrap knowledge system
python scripts/bootstrap_knowledge.py

# 5. Build frontend
cd web && npm install && npm run build && cd ..
```

## Development Environment

### Running the System

#### Using Service Manager (Recommended)

```bash
# Start all services
./svc start

# Check status
./svc status

# View logs
./svc logs

# Stop services
./svc stop
```

#### Manual Startup

```bash
# Terminal 1: Backend API
python api/main.py

# Terminal 2: Frontend development server
cd web && npm start

# Access points:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000 (dev) or http://localhost:8000/app (prod)
```

### Project Structure

```
agent_system/
├── api/                    # FastAPI backend
│   ├── main.py            # API entry point
│   ├── routes/            # API endpoints
│   └── websocket.py       # Real-time updates
├── core/                   # Core system components
│   ├── entities/          # 6 entity types
│   ├── processes/         # Process implementations
│   ├── runtime/           # Execution engine
│   └── knowledge/         # Knowledge system
├── tools/                  # Tool implementations
│   ├── core_mcp/          # Core MCP tools
│   └── mcp_servers/       # MCP integrations
├── web/                    # React frontend
│   ├── src/               # Source code
│   └── public/            # Static assets
├── scripts/               # Management scripts
├── context_documents/     # System documentation
└── knowledge/             # Knowledge entities
```

## Testing Strategy

### Running Tests

```bash
# Run complete test suite
python scripts/test_system.py

# Run specific test suite
python scripts/test_system.py --suite health
python scripts/test_system.py --suite functional
python scripts/test_system.py --suite performance
python scripts/test_system.py --suite integration

# Test individual components
python scripts/test_tool_system.py
python scripts/test_phase8_simple.py
```

### Test Categories

1. **Health Tests**
   - Database connectivity
   - Agent configurations
   - Tool registry integrity
   - System initialization

2. **Functional Tests**
   - Tool execution
   - Database operations
   - Agent instantiation
   - Process execution

3. **Performance Tests**
   - Query performance
   - Memory usage
   - Execution speed
   - Concurrent operations

4. **Integration Tests**
   - End-to-end workflows
   - Component interactions
   - WebSocket communications
   - Knowledge assembly

### Writing Tests

Follow the process-first testing approach:

```python
class TestProcessDiscovery:
    async def test_framework_establishment(self):
        """Test that process discovery establishes proper frameworks"""
        # Arrange: Create test task
        task = create_test_task("Implement user authentication")
        
        # Act: Run process discovery
        framework = await process_discovery.establish_framework(task)
        
        # Assert: Framework enables isolated execution
        assert framework.has_complete_context()
        assert framework.defines_boundaries()
        assert framework.enables_isolated_success()
```

## Debugging Techniques

### Interactive Debugging

1. **Web Interface Step Mode**
   - Enable step mode in system config
   - Approve/reject each agent action
   - Inspect intermediate states
   - View real-time message stream

2. **Logging Configuration**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger(__name__)
   ```

3. **Database Inspection**
   ```bash
   sqlite3 data/agent_system.db
   .tables
   .schema entities
   SELECT * FROM tasks WHERE status = 'failed';
   ```

### Common Debugging Commands

```bash
# Monitor system health
python scripts/monitor_health.py --duration 300

# Check event logs
sqlite3 data/agent_system.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 20"

# View task tree
python -c "from tools.system_tools import view_task_tree; view_task_tree('tree_id')"

# Test specific tool
python -c "from tools.core_mcp import test_tool; test_tool('tool_name')"
```

## Building and Deployment

### Development Build

```bash
# Backend (auto-reload enabled)
python api/main.py

# Frontend (hot-reload enabled)
cd web && npm start
```

### Production Build

```bash
# Build frontend
cd web
npm run build

# Package application
python scripts/package_app.py

# Docker build
docker build -t the-system .
docker-compose up -d
```

### Deployment Options

1. **Docker Deployment**
   ```bash
   docker-compose up -d
   # Includes: backend, frontend, database
   ```

2. **SystemD Services (Linux)**
   ```bash
   sudo cp services/*.service /etc/systemd/system/
   sudo systemctl enable agent-system-backend
   sudo systemctl start agent-system-backend
   ```

3. **Manual Deployment**
   ```bash
   ./deploy.sh
   # Handles: dependencies, build, service setup
   ```

## Self-Modification Workflow

### Safe Self-Improvement Process

```bash
# 1. Create backup before changes
python scripts/backup_system.py backup --description "Before feature X"

# 2. Execute self-modification task
python scripts/self_modify.py --task-description "Add capability Y"

# 3. Monitor during execution
python scripts/monitor_health.py --duration 300

# 4. Verify changes
python scripts/test_system.py

# 5. Rollback if needed
python scripts/backup_system.py restore --backup-id <id>
```

### Safety Features

- **Branch Isolation**: All changes in separate git branches
- **Automatic Testing**: Tests run after modifications
- **Approval Gates**: User confirmation for major changes
- **Rollback Capability**: Quick restoration to previous state
- **Comprehensive Logging**: Full audit trail of changes

## Knowledge System Management

### Knowledge Bootstrap

```bash
# Convert documentation to knowledge entities
python scripts/bootstrap_knowledge.py

# Knowledge organization:
knowledge/
├── agents/      # Agent capabilities and patterns
├── domains/     # Domain-specific knowledge
├── processes/   # Process frameworks
├── tools/       # Tool documentation
├── patterns/    # Success patterns
└── system/      # System operations
```

### Adding Knowledge

1. **Manual Addition**
   - Create JSON file in appropriate directory
   - Follow entity schema
   - Include relationships and context

2. **Automatic Capture**
   - System learns from successful executions
   - Patterns extracted and stored
   - Knowledge effectiveness tracked

## Monitoring and Maintenance

### Health Monitoring

```bash
# Real-time health check
curl http://localhost:8000/health

# Continuous monitoring
python scripts/monitor_health.py --interval 60

# Performance metrics
python scripts/analyze_performance.py
```

### Maintenance Tasks

1. **Daily**
   - Check system health
   - Review error logs
   - Monitor task success rates

2. **Weekly**
   - Backup database
   - Review optimization opportunities
   - Update knowledge base

3. **Monthly**
   - Performance analysis
   - Security updates
   - Framework optimization

## Best Practices

### Process-First Development

1. **Always Establish Frameworks First**
   ```python
   # Before implementing any feature:
   process = await discover_process(feature)
   framework = await establish_framework(process)
   # Then implement within framework
   ```

2. **Ensure Isolated Task Success**
   - Every task must have complete context
   - Dependencies clearly defined
   - Success criteria explicit

3. **Work Within Boundaries**
   - Respect process limitations
   - Use only permitted tools
   - Follow established patterns

### Code Quality

1. **Type Hints**: Use throughout codebase
2. **Async/Await**: For all I/O operations
3. **Error Handling**: Comprehensive try-except blocks
4. **Documentation**: Clear docstrings and comments
5. **Testing**: Test framework compliance

### Version Control

```bash
# Feature development
git checkout -b feature/process-enhancement
# Make changes following conventions
git commit -m "feat: enhance process discovery framework"
git push origin feature/process-enhancement
# Create pull request
```

## Configuration Management

### Seeding Configuration System

The system uses a **configuration-driven seeding approach** with YAML files that separate data from execution logic:

```
agent_system/config/seeds/
├── agents.yaml      # Agent definitions with instructions & permissions
├── tools.yaml       # Tool configurations with implementations
├── documents.yaml   # Context document specifications
└── README.md        # Configuration documentation
```

#### Modifying System Configuration

1. **Adding New Agents**:
   ```yaml
   # config/seeds/agents.yaml
   - name: new_agent
     instruction: |
       Agent instructions here...
     context_documents:
       - required_document_name
     available_tools:
       - tool_name
     permissions:
       web_search: true
   ```

2. **Adding New Tools**:
   ```yaml
   # config/seeds/tools.yaml
   - name: new_tool
     description: Tool purpose
     category: system
     implementation:
       type: python_class
       module_path: tools.module
       class_name: ToolClass
   ```

3. **Adding Context Documents**:
   ```yaml
   # config/seeds/documents.yaml - choose one approach:
   
   # File-based (auto-discovered)
   filesystem_docs:
     docs_directory: "../../../docs"
     pattern: "*.md"
   
   # Explicit file reference
   agent_guides:
     - name: guide_name
       file_path: "../../../docs/path/file.md"
   
   # Inline content
   system_references:
     - name: reference_name
       content: |
         Inline content here...
   ```

#### Configuration Validation

```bash
# Test configuration loading
python3 -c "
from scripts.seeders import load_configuration
config = load_configuration('config/seeds')
print('Configuration valid!')
"

# Full seeding with validation
python scripts/seed_system.py
```

#### Configuration Architecture Benefits

- **87% Line Reduction**: Seed script reduced from 1,228 to 161 lines
- **Separation of Concerns**: Data completely separated from execution logic
- **Type Safety**: Comprehensive Pydantic validation
- **Maintainability**: Easy to modify without code changes
- **Version Control**: YAML files track configuration history
- **Rollback Safety**: Legacy version preserved as backup

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify .env file exists and contains valid keys
   - Check API key permissions and quotas

2. **Database Locked**
   - Stop all services: `./svc stop`
   - Remove lock: `rm data/agent_system.db-journal`

3. **Frontend Build Errors**
   - Clear cache: `cd web && npm clean-install`
   - Rebuild: `npm run build`

4. **Task Timeouts**
   - Increase timeout in task configuration
   - Check for infinite loops in processes
   - Verify API rate limits

### Getting Help

1. Check comprehensive logs in `logs/` directory
2. Review documentation in `docs/` and `context_documents/`
3. Run diagnostic scripts in `scripts/`
4. Enable debug logging for detailed traces

This workflow guide ensures systematic development aligned with the process-first architecture, enabling safe and effective enhancement of the recursive agent system.