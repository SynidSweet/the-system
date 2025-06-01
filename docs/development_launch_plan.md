# Self-Improving Agent System - Minimal MVP Development Plan

## Technical Stack (Minimal)

### Core Components
- **Runtime**: Python 3.11+ with asyncio
- **Database**: SQLite with simple ORM (SQLModel/Pydantic)
- **API**: FastAPI with WebSocket support
- **Frontend**: React with basic real-time updates
- **Agent Integration**: MCP Python SDK
- **Task Queue**: Simple in-memory queue with database persistence

### Required Libraries
```txt
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
sqlmodel==0.0.14
mcp-python-sdk==0.1.0
gitpython==3.1.40
asyncio-mqtt==0.16.1
cryptography==41.0.7
python-dotenv==1.0.0
authlib==1.2.1
google-auth==2.23.4
google-auth-oauthlib==1.1.0
```

### Environment Configuration
```bash
# .env file for secure configuration
ANTHROPIC_API_KEY=your_api_key_here
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_secret
SYSTEM_SECRET_KEY=random_secret_for_sessions
DATABASE_URL=sqlite:///data/agent_system.db
MAX_CONCURRENT_AGENTS=3
DEFAULT_TIMEOUT_SECONDS=300
ENVIRONMENT=development
DEBUG_MODE=true
SUPERVISOR_CHECK_INTERVAL=60
```

## Core Implementation Architecture

### 1. Universal Agent Runtime (`core/agent.py`)
```python
class UniversalAgent:
    def __init__(self, task_id: int, db: Database):
        self.task_id = task_id
        self.task = db.get_task(task_id)
        self.agent_config = db.get_agent(self.task.agent_id)
        self.tools = self._load_tools()
        
    async def execute(self):
        # Build prompt: core_instruction + task_instruction + context
        # Log initial message
        await self._log_message("system", f"Starting task: {self.task.instruction}")
        
        # Execute with AI model
        response = await self._call_ai_model()
        await self._log_message("agent_response", response)
        
        # Parse tool calls and execute
        for tool_call in self._parse_tool_calls(response):
            await self._log_message("tool_call", tool_call)
            result = await self._execute_tool(tool_call)
            await self._log_message("tool_response", result)
        
        # Update task status
        await self._complete_task()
        
    async def _log_message(self, msg_type: str, content: str, metadata: dict = None):
        # Log all agent communications to messages table
        
    def _load_tools(self):
        # Always include core MCP toolkit
        # Add agent-specific optional tools
```

### 2. Task Manager (`core/task_manager.py`)
```python
class TaskManager:
    async def create_task_tree(self, user_input: str) -> int:
        # Create new tree_id
        # Create initial task with agent_selector
        # Return tree_id
        
    async def spawn_subtask(self, parent_id: int, instruction: str, agent_type: str):
        # Create child task
        # Add to queue
        # Maintain tree isolation
        
    async def process_queue(self):
        # Respect concurrent agent limits
        # Process tasks in priority order
        # Handle manual/automatic stepping
```

### 3. Core MCP Toolkit (`tools/core_mcp.py`)
```python
class CoreMCPTools:
    @mcp_tool
    async def break_down_task(self, reasoning: str):
        # Spawn task_breakdown agent with current task
        
    @mcp_tool  
    async def start_subtask(self, task_instruction: str, agent_type: str):
        # Create subtask in same tree
        
    @mcp_tool
    async def request_context(self, context_needed: str):
        # Spawn context_addition agent
        
    @mcp_tool
    async def request_tools(self, tools_needed: str):
        # Spawn tool_addition agent
        
    @mcp_tool
    async def end_task(self, status: str, result: str):
        # Mark task complete
        # Trigger evaluator, documentation, and summary agents in parallel
        # Return summary to parent agent
        
    @mcp_tool
    async def flag_for_review(self, issue: str):
        # Add to review queue for manual inspection
```

## Development Timeline (6 Weeks)

### Week 1: Foundation
**Goal**: Basic agent runtime and database

**Deliverables**:
- SQLite database with schema
- Universal agent class that can execute simple tasks
- Basic FastAPI server
- Core MCP toolkit skeleton

**Success Criteria**:
- Can create agent, load from database, execute simple instruction
- Database operations work correctly
- MCP tools can be called and registered

### Week 2: Task Management  
**Goal**: Task trees and recursive spawning

**Deliverables**:
- Task queue and tree management
- Agent spawning system
- Basic concurrency controls
- Initial agent configurations in database

**Success Criteria**:
- Can create task tree from user input
- Agent can spawn subtask via MCP tool
- Multiple agents can run concurrently
- Task trees remain isolated

### Week 3: Core Agents
**Goal**: Implement required agent types

**Deliverables**:
- Agent selector implementation
- Task breakdown agent
- Context and tool addition agents
- Database seeding script

**Success Criteria**:
- Agent selector chooses appropriate agents
- Complex tasks get broken down automatically
- Agents can request additional context/tools

### Week 4: Self-Modification
**Goal**: System can modify itself

**Deliverables**:
- Git integration MCP tools
- System restart mechanism  
- Review agent implementation
- Basic testing framework

**Success Criteria**:
- Agent can commit changes to git
- System can restart itself cleanly
- Changes persist across restarts

### Week 5: Supervision & UI
**Goal**: Monitoring and user interface

**Deliverables**:
- Supervisor agent with timeout handling
- Task evaluator agent
- React frontend with real-time updates
- Review queue interface

**Success Criteria**:
- Stuck agents are detected and handled
- Task results are evaluated automatically
- Users can monitor task progress visually

### Week 6: Integration & Testing
**Goal**: End-to-end testing and deployment

**Deliverables**:
- Cloud deployment configuration
- Integration tests for core workflows
- Documentation and system guides
- Performance optimization

**Success Criteria**:
- Complete user workflow works end-to-end
- System demonstrates self-improvement
- Deployment to cloud successful

## Hosting Architecture

### Cloud VM Specifications
**Provider**: AWS EC2 or DigitalOcean Droplet
- **Instance**: t3.medium (2 vCPU, 4GB RAM)
- **Storage**: 50GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Cost**: ~$30-40/month

### System Architecture
```bash
/opt/agent-system/
├── app/                    # Python application
├── data/
│   ├── agent_system.db    # SQLite database
│   └── logs/              # System logs
├── .git/                  # Git repository (agents can modify)
├── docker-compose.yml     # Container orchestration
└── restart.sh            # System restart script
```

### Deployment Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports: ["80:8000"]
    volumes:
      - "./data:/app/data"
      - "./app:/app"
      - "./.git:/app/.git"
      - "/var/run/docker.sock:/var/run/docker.sock"  # For self-restart
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
```

### Self-Restart Mechanism
```bash
#!/bin/bash
# restart.sh - Called by agents to restart system
echo "System restart requested at $(date) by task $1" >> /opt/agent-system/data/logs/restarts.log

# Graceful shutdown - wait for current agents to finish or timeout
cd /opt/agent-system
curl -X POST http://localhost:8000/admin/graceful-shutdown || echo "Graceful shutdown failed"
sleep 10

# Pull any agent-committed changes
git pull origin main

# Create backup before restart
./scripts/backup.py

# Restart with new code
docker-compose down
docker-compose up -d --build

# Wait for system to be ready
sleep 15
curl -f http://localhost:8000/health || echo "System restart may have failed"
echo "System restart completed at $(date)" >> /opt/agent-system/data/logs/restarts.log
```

### Basic Monitoring Setup
```python
# core/monitoring.py
import psutil
import asyncio
from datetime import datetime

class SystemMonitor:
    async def get_system_stats(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "active_agents": await self.count_active_agents(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def check_resource_limits(self):
        stats = await self.get_system_stats()
        alerts = []
        
        if stats["cpu_percent"] > 90:
            alerts.append("High CPU usage")
        if stats["memory_percent"] > 90:
            alerts.append("High memory usage")
        if stats["disk_percent"] > 90:
            alerts.append("High disk usage")
            
        return alerts
```

## Database Seeding

### Initial Agent Configurations
```sql
-- Core system agents
INSERT INTO agents (name, instruction, context_documents, available_tools, web_search_allowed) VALUES
('agent_selector', 'Analyze task and select appropriate agent type...', '["system_overview", "agent_registry"]', '["list_agents", "query_database"]', TRUE),
('task_breakdown', 'Break task into sequential subtasks...', '["breakdown_guidelines"]', '[]', FALSE),
('context_addition', 'Determine needed context documents...', '["available_context"]', '["list_documents", "use_terminal"]', TRUE),
('tool_addition', 'Find or create needed MCP tools...', '["tool_registry", "mcp_docs"]', '["list_optional_tools", "github_operations"]', TRUE),
('task_evaluator', 'Evaluate task completion quality...', '["evaluation_criteria"]', '["query_database"]', FALSE),
('documentation_agent', 'Document system changes and discoveries...', '["documentation_standards"]', '["list_documents", "query_database"]', FALSE),
('summary_agent', 'Create concise task summary for parent agent...', '["summarization_guidelines"]', '["query_database"]', FALSE),
('supervisor', 'Monitor agent execution and handle issues...', '["monitoring_guidelines"]', '["use_terminal", "query_database"]', FALSE),
('review_agent', 'Analyze issues and improve system...', '["improvement_guide"]', '["github_operations", "use_terminal", "query_database"]', TRUE);

-- Core context documents
INSERT INTO context_documents (name, content) VALUES
('system_overview', '# System Overview\nThis is a recursive agent system...'),
('system_architecture', '# System Architecture\nDatabase schema...'),
('environment_details', '# Environment Details\nUbuntu 22.04, Docker...'),
('improvement_guide', '# System Improvement Guide\n1. Create branch...');

-- Initial optional tools
INSERT INTO tools (name, description, mcp_config) VALUES
('list_agents', 'Query available agent configurations', '{"type": "database_query", "table": "agents"}'),
('list_documents', 'Query available context documents', '{"type": "database_query", "table": "context_documents"}'),
('list_optional_tools', 'Query tools registry', '{"type": "database_query", "table": "tools"}'),
('use_terminal', 'Execute shell commands', '{"type": "shell_access", "permissions": "full"}'),
('github_operations', 'Git operations and repository management', '{"type": "git_integration", "permissions": "full"}'),
('query_database', 'Direct SQLite database queries', '{"type": "database_access", "permissions": "read_write"}');
```

### Core System Instruction
```
You are a universal agent in a recursive task-solving system. Your specific task is: {task_instruction}

CORE PRINCIPLES:
1. Solve ONLY the specific task you've been given
2. Use available tools when you need to spawn other agents or modify the system
3. If the task is too complex, break it down using break_down_task()
4. If you need more context or tools, request them explicitly
5. Always end with end_task() indicating success or failure

AVAILABLE TOOLS:
- break_down_task(): Split current task into subtasks
- start_subtask(): Create isolated subtask with specific agent
- request_context(): Get additional context documents  
- request_tools(): Get additional MCP tools
- end_task(): Mark task complete with result
- flag_for_review(): Flag issues for human review
{additional_tools}

CONTEXT DOCUMENTS:
{context_documents}

Complete your assigned task efficiently and precisely.
```

## Testing Strategy

### Core Workflow Tests
1. **Basic Task Execution**: Simple task → agent selection → completion → documentation & summary
2. **Task Breakdown**: Complex task → breakdown → subtask execution → parent receives summary
3. **Tool Discovery**: Agent needs tool → tool creation → tool usage → documentation update
4. **Self-Modification**: System improvement → code change → restart → validation → documentation
5. **Supervision**: Long-running task → supervisor intervention → resolution
6. **Message History**: All agent communications logged → queryable by system → visible in UI

### Safety Testing
1. **Infinite Recursion**: Depth limits and cycle detection
2. **Resource Exhaustion**: Memory and CPU limits per agent
3. **Database Corruption**: Transaction safety and rollback
4. **Git Safety**: Validate changes before committing

## Deployment Process

### Initial Setup
```bash
# Cloud VM setup
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clone and deploy
git clone <repository> /opt/agent-system
cd /opt/agent-system
chmod +x restart.sh
./restart.sh
```

### Agent Permissions Setup
```bash
# Give agents full system access
sudo usermod -aG sudo ubuntu
echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Git configuration for agents
git config --global user.name "Agent System"
git config --global user.email "agents@yoursystem.com"
```

## Success Metrics

### Technical Validation
- **Basic Function**: User input → task completion in <5 minutes
- **Recursion**: 3+ level task breakdown completes successfully  
- **Self-Modification**: Agent successfully improves system code
- **Supervision**: Stuck agent detected and resolved within 60 seconds
- **Concurrency**: 3 agents running simultaneously without conflicts

### System Validation  
- **Restart Survival**: System restart preserves all task history
- **Tool Creation**: Agent creates new MCP tool and uses it successfully
- **Context Addition**: Agent adds context document and references it
- **Error Recovery**: Failed task marked correctly, doesn't crash system

## Post-MVP Evolution

Once core system is working, all subsequent development should be performed by the agents themselves:

1. **Performance Optimization**: Agents analyze slow operations and optimize
2. **UI Improvements**: Agents enhance web interface based on usage patterns
3. **Tool Ecosystem**: Agents discover and integrate useful external tools
4. **Advanced Features**: Agents implement features like better task visualization
5. **Security Hardening**: Agents implement security improvements as needed

The human developer's role shifts from coding to:
- Providing high-level direction and feedback
- Manual review of flagged improvements  
- System administration and maintenance
- Guiding the system's evolution priorities