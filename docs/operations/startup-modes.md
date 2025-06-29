# Startup Modes Documentation

*Created: 2025-06-28*

## Overview

The System now uses a unified startup architecture with configuration-driven initialization. This replaces the previous duplicated startup scripts with a systematic approach that follows process-first principles.

## Available Startup Modes

### 1. Full Mode (Recommended for Production)
```bash
python start_api.py
# or
python start_unified.py --mode full
```

**Features:**
- Complete system initialization with all components
- Database with full entity management
- Event system with comprehensive tracking
- Runtime engine with process framework
- Tool system with MCP integration
- Knowledge system with context assembly
- WebSocket support for real-time updates
- Web interface serving (React frontend)

**Port:** 8000  
**Use cases:** Production deployment, full feature access, complete system testing

### 2. Simplified Mode (Recommended for Development)
```bash
python start_api_simple.py
# or
python start_unified.py --mode simplified
```

**Features:**
- Database connectivity and entity management
- Basic API endpoints
- Event system (limited)
- No runtime engine or tool system
- WebSocket support
- Simplified initialization

**Port:** 8002  
**Use cases:** Development, API testing, database operations without complex initialization

### 3. Minimal Mode (Fastest Startup)
```bash
python start_api_minimal.py
# or
python start_unified.py --mode minimal
```

**Features:**
- Basic FastAPI server only
- No database connectivity
- No complex system components
- Health check endpoints only
- Fastest startup time

**Port:** 8001  
**Use cases:** API development, quick health checks, troubleshooting startup issues

### 4. Development Mode (Debug Features)
```bash
python start_unified.py --mode development
```

**Features:**
- Full system with debug features enabled
- Detailed logging and error reporting
- Non-failing validation (warnings only)
- Step-by-step debugging support
- Enhanced error messages

**Port:** 8000  
**Use cases:** System debugging, development with detailed feedback

## Unified Startup Script

The new `start_unified.py` script supports command-line options:

```bash
# Basic usage
python start_unified.py --mode simplified

# With custom port
python start_unified.py --mode full --port 9000

# Debug mode with custom host
python start_unified.py --mode development --host 127.0.0.1 --debug

# Disable validation
python start_unified.py --mode full --no-validation

# Custom log level
python start_unified.py --mode simplified --log-level debug
```

### Command Line Options

- `--mode`: Startup mode (full|simplified|minimal|development)
- `--port`: Override default port
- `--host`: Host to bind to (default: 0.0.0.0)
- `--debug`: Enable debug mode
- `--no-validation`: Disable startup validation
- `--log-level`: Set logging level (debug|info|warning|error)

## Architecture Benefits

### Process-First Compliance
- Systematic validation before initialization
- Framework establishment for component dependencies
- Configuration-driven approach eliminates ad-hoc startup logic

### Unified Configuration
```python
from agent_system.core.startup import StartupConfig, StartupMode

# Create configuration
config = StartupConfig.for_mode(StartupMode.SIMPLIFIED)

# Customize as needed
config.api.port = 9000
config.debug_mode = True

# Validate configuration
issues = config.validate()
```

### Component Management
- Clear separation of concerns
- Dependency-aware initialization order
- Graceful shutdown in reverse order
- Component health tracking

### Validation Framework
- Pre-startup system validation
- Dependency checking (Python packages, imports)
- Filesystem validation (directories, permissions)
- Configuration consistency checks
- Port availability verification

## Migration from Old Scripts

### Before (Duplicated Logic)
```
start_api.py (95 lines, complex initialization)
start_api_simple.py (95 lines, duplicated CORS setup)
start_api_minimal.py (72 lines, hardcoded configuration)
```

### After (Unified Wrappers)
```
start_api.py (34 lines, wrapper for full mode)
start_api_simple.py (33 lines, wrapper for simplified mode)
start_api_minimal.py (33 lines, wrapper for minimal mode)
start_unified.py (main script with full configuration)
```

**Benefits:**
- 70%+ code reduction in wrapper scripts
- Shared initialization logic
- Consistent CORS, middleware, and endpoint setup
- Single source of truth for configuration
- Easy to add new startup modes

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check which ports are in use
   netstat -tulpn | grep :800
   
   # Use custom port
   python start_unified.py --mode simplified --port 9002
   ```

2. **Validation Errors**
   ```bash
   # Skip validation for troubleshooting
   python start_unified.py --mode minimal --no-validation
   
   # See detailed validation
   python start_unified.py --mode development
   ```

3. **Virtual Environment Issues**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   
   # Verify dependencies
   pip list | grep fastapi
   ```

4. **Frontend Build Issues**
   ```bash
   # Dependencies aligned to React 18.x
   cd agent_system/web
   npm install
   npm run build
   ```

### Debug Mode Features

Enable debug mode for enhanced troubleshooting:
```bash
python start_unified.py --mode development --debug
```

**Debug Features:**
- Detailed component initialization logging
- Non-failing validation (warnings instead of errors)
- Enhanced error messages with stack traces
- Component status tracking
- Validation result details

## Best Practices

### Development Workflow
1. **Start with Minimal** for basic API testing
2. **Use Simplified** for database-dependent development
3. **Use Full** for complete feature testing
4. **Use Development** for debugging and troubleshooting

### Production Deployment
1. **Always use Full mode** for production
2. **Enable validation** to catch configuration issues
3. **Use appropriate ports** (8000 for full system)
4. **Monitor startup logs** for component initialization status

### Configuration Management
1. **Extend StartupConfig** for custom configurations
2. **Use environment variables** for deployment-specific settings
3. **Validate configurations** before deployment
4. **Document custom startup modes** for team consistency

## Future Enhancements

### Planned Features
- **Environment-based configurations** (dev/staging/prod)
- **Health check endpoints** with component status
- **Configuration hot-reloading** for development
- **Startup performance profiling** and optimization
- **Docker integration** with startup mode selection
- **Service discovery** for distributed deployments

### Configuration Extensions
- **Resource limits** (memory, CPU, connections)
- **Feature flags** for gradual rollout
- **Monitoring integration** (Prometheus, Grafana)
- **Security configurations** (HTTPS, authentication)
- **Cache settings** (Redis integration)

The unified startup system provides a solid foundation for systematic system initialization while maintaining the flexibility needed for different deployment scenarios and development workflows.