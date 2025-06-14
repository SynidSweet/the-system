# Service Management Guide

This directory contains efficient service management tools for quickly starting, stopping, and monitoring the agent system services.

## Quick Commands

From the agent_system directory, use the `svc` wrapper:

```bash
# Start services
./svc start           # Start all services
./svc start backend   # Start only backend
./svc start frontend  # Start only frontend

# Stop services  
./svc stop            # Stop all services
./svc stop backend    # Stop only backend
./svc stop frontend   # Stop only frontend

# Restart services (quick)
./svc restart         # Restart all services
./svc restart backend # Restart only backend

# Check status
./svc status          # Show detailed status with health checks

# View logs
./svc logs            # Show recent logs from both services
./svc logs backend 50 # Show last 50 lines of backend log
./svc logs frontend   # Show only frontend logs
```

## Features

1. **Fast Startup Detection**: Services start in background and the script waits for actual startup confirmation (not timers)
2. **Health Checks**: Automatic health verification after startup
3. **Error Detection**: Shows relevant errors if startup fails
4. **Clean Process Management**: Proper PID tracking and graceful/forced shutdown
5. **Colored Output**: Clear visual feedback with color coding

## Service Details

### Backend (FastAPI)
- Port: 8000
- Health endpoint: http://localhost:8000/health
- PID file: logs/backend.pid
- Log file: logs/backend.log

### Frontend (React)
- Port: 3000
- URL: http://localhost:3000
- PID file: logs/frontend.pid
- Log file: logs/frontend.log

## Implementation

Two implementations are provided:

1. **manage_services.sh**: Bash script with basic functionality
2. **service_manager.py**: Python script with advanced features (used by `svc`)

The Python version provides:
- Process monitoring with psutil
- HTTP health checks
- Better error handling
- Detailed startup feedback

## For Claude Code

When you need to restart services, use:

```bash
# Quick backend restart with immediate feedback
./svc restart backend

# Check if services are healthy
./svc status

# View recent errors
./svc logs backend 20
```

This is much faster than manual process management and provides immediate, actionable feedback.