# Service Management Documentation

## Overview

The agent system includes a comprehensive service management system for controlling the backend API and frontend React application. The `svc` command provides quick, reliable service control with health monitoring and log access.

## Quick Start

From the `agent_system` directory:

```bash
# Start all services
./svc start

# Stop all services  
./svc stop

# Check status
./svc status

# View logs
./svc logs
```

## Command Reference

### Starting Services

```bash
./svc start              # Start both backend and frontend
./svc start backend      # Start only backend API
./svc start frontend     # Start only frontend React app
```

**Features**:
- Automatic virtual environment activation for backend
- Health check verification after startup
- Clear feedback on startup success/failure
- Shows relevant errors if startup fails

### Stopping Services

```bash
./svc stop               # Stop all services
./svc stop backend       # Stop only backend
./svc stop frontend      # Stop only frontend
```

**Features**:
- Graceful shutdown attempt first
- Forced termination after timeout
- PID file cleanup
- Confirmation of stopped services

### Restarting Services

```bash
./svc restart            # Restart all services
./svc restart backend    # Restart only backend
./svc restart frontend   # Restart only frontend
```

**Features**:
- Quick stop and start cycle
- Maintains service configuration
- Useful for applying code changes

### Checking Status

```bash
./svc status             # Detailed status of all services
```

**Output includes**:
- Running/Stopped state
- Process ID (PID)
- Port availability
- Health check results
- Uptime information

### Viewing Logs

```bash
./svc logs               # Show recent logs from both services
./svc logs backend       # Show only backend logs
./svc logs frontend      # Show only frontend logs
./svc logs backend 50    # Show last 50 lines of backend log
```

**Features**:
- Tail recent log entries
- Configurable number of lines
- Combined or individual service logs

## Service Details

### Backend Service (FastAPI)
- **Port**: 8000
- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **PID File**: `logs/backend.pid`
- **Log File**: `logs/backend.log`
- **Virtual Env**: Automatically activated

### Frontend Service (React)
- **Port**: 3000  
- **URL**: http://localhost:3000
- **PID File**: `logs/frontend.pid`
- **Log File**: `logs/frontend.log`
- **Build**: Development mode with hot reload

## Implementation Details

### Service Manager Architecture

The system provides two implementations:

1. **Python Implementation** (`scripts/service_manager.py`):
   - Advanced process management with psutil
   - HTTP health checking
   - Colored output for clarity
   - Detailed error reporting

2. **Bash Implementation** (`scripts/manage_services.sh`):
   - Lightweight alternative
   - Basic process control
   - Fallback option

The `svc` wrapper automatically uses the Python implementation for better functionality.

### Health Monitoring

Services are monitored using:
- **Process Detection**: Checks if PID is running
- **Port Availability**: Verifies service ports are listening  
- **HTTP Health Checks**: Confirms services respond correctly
- **Startup Verification**: Waits for actual startup, not timers

### Process Management

**Startup Flow**:
1. Check if service already running
2. Start service in background
3. Write PID to file
4. Wait for health check pass
5. Report success or failure with details

**Shutdown Flow**:
1. Read PID from file
2. Send SIGTERM for graceful shutdown
3. Wait up to 5 seconds
4. Force kill if needed
5. Clean up PID file

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check if port is in use
lsof -i :8000  # For backend
lsof -i :3000  # For frontend

# Check recent errors
./svc logs backend 50

# Try manual start for detailed errors
cd agent_system
source venv/bin/activate
python -m api.main
```

**Service crashes immediately**:
```bash
# Check for Python errors
./svc logs backend 100 | grep -i error

# Verify dependencies
source venv/bin/activate
pip install -r requirements.txt
```

**Can't stop service**:
```bash
# Force kill if needed
kill -9 $(cat logs/backend.pid)
rm logs/backend.pid
```

### Log Files

All services write detailed logs:
- **Backend**: `logs/backend.log` - API requests, errors, agent execution
- **Frontend**: `logs/frontend.log` - Build output, webpack details

## Best Practices

1. **Always check status** before starting services
2. **Review logs** if services fail to start
3. **Use restart** instead of stop/start for quick updates
4. **Monitor health** endpoint for production deployments

## Integration with Development

### Hot Reload
- Backend: Add `--reload` flag for development
- Frontend: Automatically enabled in development mode

### Debug Mode
Set environment variables before starting:
```bash
export DEBUG=true
./svc start
```

### Custom Ports
Edit service files to change default ports:
- Backend: `api/main.py`
- Frontend: `web/package.json`

## Advanced Usage

### Running Multiple Instances
```bash
# Start on different ports
PORT=8001 ./svc start backend
PORT=3001 ./svc start frontend
```

### Background Operations
All services run in background by default. To run in foreground for debugging:
```bash
# Manual foreground execution
python -m api.main
npm start --prefix web
```

### System Integration
The service manager integrates with:
- Git workflows (restart after pulls)
- Deployment scripts
- Health monitoring systems
- CI/CD pipelines

## Security Notes

1. **PID Files**: Stored in `logs/` with appropriate permissions
2. **Port Binding**: Services bind to localhost only by default
3. **Process Isolation**: Each service runs in its own process
4. **Clean Shutdown**: Ensures database connections close properly