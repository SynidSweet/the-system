# Script Usage Guide

This guide explains when and how to use the various scripts in the agent system.

## System State Management

### 1. Reset System to Fresh State
When you need to completely reset the system to a fresh, uninitialized state:

```bash
# Reset system to factory state (removes all data)
python scripts/reset_system.py

# Reset with backup (creates backup before wiping)
python scripts/reset_system.py --backup
```

### 2. Initialize System
After resetting or on first run, initialize the system:

**Option A: Web-Based Initialization (Recommended)**
1. Start the system: `./svc start`
2. Open http://localhost:3000
3. The initialization page will appear automatically
4. Configure settings and click "Initialize System"

**Option B: Command-Line Initialization**
```bash
# Full initialization with all agents and documents
python scripts/seed_system.py

# Minimal initialization (only agent_selector)
python scripts/minimal_init.py

# Standard initialization
python scripts/init_system.py
```

### 3. System Operations

#### Starting the System
```bash
# Recommended: Use service manager
./svc start    # Start backend and frontend
./svc status   # Check status
./svc logs     # View logs
./svc stop     # Stop services
./svc restart  # Restart services

# Alternative: Direct startup
./start.sh     # Foreground mode (shows output)
./startup.sh   # Background mode
```

#### First-Time Setup
```bash
# Deploy and initialize everything
./deploy.sh
```

## Development Workflows

### 1. Testing System Components
```bash
# Test entity system
python scripts/test_entity_system.py

# Test simple task flow
python scripts/test_simple_flow.py

# Test after cleanup
python scripts/test_phase8_cleanup.py
```

### 2. Knowledge System Management
```bash
# Bootstrap knowledge from documentation
python scripts/bootstrap_knowledge.py

# This converts all docs to structured knowledge entities
```

### 3. Process Discovery Setup
```bash
# Add process discovery capabilities
python scripts/add_process_discovery_agent.py
python scripts/init_process_discovery.py
```

### 4. Database Migrations
```bash
# Create entity tables
python scripts/create_entity_tables.py

# Migrate agents to new schema
python scripts/migrate_agents_to_tables.py

# Migrate tasks to new schema
python scripts/migrate_tasks_to_tables.py
```

## Backup and Recovery

### Creating Backups
```bash
# Create full system backup
python scripts/backup_system.py backup

# Create backup with description
python scripts/backup_system.py backup --description "Before major update"
```

### Restoring from Backup
```bash
# List available backups
python scripts/backup_system.py list

# Restore specific backup
python scripts/backup_system.py restore --backup-id backup_20240120_143022

# Cleanup old backups (keep latest 5)
python scripts/backup_system.py cleanup --keep 5
```

## Monitoring and Health

### System Health Check
```bash
# Monitor system health
python scripts/monitor_health.py

# Check specific components
curl http://localhost:8000/health
```

## Common Scenarios

### Scenario 1: Fresh Installation
```bash
1. ./deploy.sh                    # Install dependencies and build
2. ./svc start                    # Start services
3. Open http://localhost:3000     # Initialize via web UI
```

### Scenario 2: Reset and Reinitialize
```bash
1. python scripts/reset_system.py --backup  # Reset with backup
2. ./svc restart                            # Restart services
3. python scripts/seed_system.py            # Seed full system
```

### Scenario 3: Development Testing
```bash
1. python scripts/reset_system.py           # Clean slate
2. python scripts/minimal_init.py           # Minimal setup
3. python scripts/test_simple_flow.py       # Test basic flow
```

### Scenario 4: Production Deployment
```bash
1. python scripts/backup_system.py backup   # Backup current state
2. git pull                                 # Update code
3. ./deploy.sh                             # Update dependencies
4. ./svc restart                           # Restart services
```

## Important Notes

1. **Process-First Principle**: The system follows process-first architecture. Always ensure process frameworks exist before task execution.

2. **Initialization States**:
   - `uninitialized`: Fresh system, needs initialization
   - `initializing`: Currently running initialization tasks
   - `ready`: System fully initialized and operational

3. **Script Dependencies**:
   - Most scripts require virtual environment: `source venv/bin/activate`
   - Database must be accessible (SQLite file or configured connection)
   - Some scripts require the API server to be running

4. **Data Persistence**:
   - Database: `data/agent_system.db`
   - Knowledge entities: `knowledge/` directory
   - Logs: `logs/` directory
   - Backups: `backups/` directory

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill <PID>

# Restart services
./svc restart
```

### Database Locked
```bash
# Stop all services
./svc stop

# Check for hanging processes
ps aux | grep python

# Restart
./svc start
```

### Frontend Not Loading
```bash
# Check frontend logs
./svc logs frontend

# Rebuild frontend
cd web && npm install && npm run build

# Restart
./svc restart
```