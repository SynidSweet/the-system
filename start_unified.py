#!/usr/bin/env python3
"""
Unified startup script for The System.

Configuration-driven startup with systematic validation following process-first principles.
Supports multiple startup modes: full, simplified, minimal, development.
"""

import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from agent_system.core.startup import StartupConfig, StartupMode, ServiceManager


def create_app(config: StartupConfig) -> FastAPI:
    """Create FastAPI application with unified configuration."""
    
    # Create service manager
    service_manager = ServiceManager(config)
    
    # Create FastAPI app
    app = FastAPI(
        title=config.get_title(),
        description=config.get_description(),
        version="1.0.0",
        lifespan=service_manager.lifespan
    )
    
    # Add CORS middleware
    if config.api.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Basic endpoints for all modes
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {config.get_title()}",
            "version": "1.0.0",
            "status": "running",
            "mode": config.mode.value,
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "mode": config.mode.value,
            "database": "enabled" if config.database.enabled else "disabled",
            "components": {
                "event_system": config.components.event_system,
                "entity_manager": config.components.entity_manager,
                "runtime_engine": config.components.runtime_engine,
                "tool_system": config.components.tool_system,
                "knowledge_system": config.components.knowledge_system
            }
        }
    
    @app.get("/api/v1/health")
    async def api_health():
        return {
            "status": "healthy",
            "timestamp": "2025-06-28",
            "mode": config.mode.value,
            "startup_config": {
                "database_enabled": config.database.enabled,
                "validation_enabled": config.validation.enabled,
                "debug_mode": config.debug_mode
            }
        }
    
    # Add full API routes for non-minimal modes
    if config.mode != StartupMode.MINIMAL:
        try:
            from agent_system.api.routes import tasks, entities, admin
            from agent_system.api.websocket.handlers import websocket_endpoint
            
            app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
            app.include_router(entities.router, prefix="/entities", tags=["entities"])
            app.include_router(admin.router, prefix="/admin", tags=["admin"])
            
            if config.components.websocket_manager:
                app.add_websocket_route("/ws", websocket_endpoint)
                
        except ImportError as e:
            print(f"⚠️  Could not load full API routes: {e}")
            print("   Running in basic mode only")
    
    # Serve static files for full mode
    if config.api.serve_static and config.mode == StartupMode.FULL:
        try:
            from fastapi.staticfiles import StaticFiles
            static_path = Path(config.api.static_path)
            if static_path.exists():
                app.mount("/app", StaticFiles(directory=str(static_path), html=True), name="app")
        except Exception as e:
            print(f"⚠️  Could not mount static files: {e}")
    
    # Store service manager for access
    app.state.service_manager = service_manager
    
    return app


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Start The System with unified configuration")
    parser.add_argument(
        "--mode", 
        choices=["full", "simplified", "minimal", "development"],
        default="full",
        help="Startup mode (default: full)"
    )
    parser.add_argument("--port", type=int, help="Override default port")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-validation", action="store_true", help="Disable startup validation")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Create configuration
    mode = StartupMode(args.mode)
    config = StartupConfig.for_mode(mode)
    
    # Apply overrides
    if args.port:
        config.api.port = args.port
    if args.host:
        config.api.host = args.host
    if args.debug:
        config.debug_mode = True
    if args.no_validation:
        config.validation.enabled = False
    if args.log_level:
        config.api.log_level = args.log_level
    
    # Create and run app
    app = create_app(config)
    
    print(f"🚀 Starting {config.get_title()} on {config.api.host}:{config.api.port}")
    
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        log_level=config.api.log_level
    )


if __name__ == "__main__":
    main()