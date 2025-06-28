#!/usr/bin/env python3
"""
FastAPI application for the self-improving agent system.

This provides:
- REST API endpoints for task submission and management
- WebSocket connections for real-time updates
- Admin endpoints for system control
- Health checks and monitoring
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Import database and global instances
from agent_system.config.database import DatabaseManager

# Import modular components
from agent_system.api.startup import lifespan, get_runtime_integration
from agent_system.api.websocket.handlers import manager, websocket_endpoint
from agent_system.api.routes import tasks, entities, admin

# Import exception handling middleware
from agent_system.api.middleware.exception_handler import ExceptionHandlerMiddleware

# Import temporary compatibility models
from agent_system.api.routes.tasks import TaskStatus


# Create global database instance
database = DatabaseManager()

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Self-Improving Agent System",
    description="A process-first recursive agent system that transforms undefined problems into systematic domains",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handling middleware
app.add_middleware(ExceptionHandlerMiddleware)

# Include API routers
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(entities.router, prefix="", tags=["entities"])
app.include_router(admin.router, prefix="", tags=["admin", "system"])

# Add WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)


# Core API endpoints
@app.get("/")
async def root():
    """Welcome message"""
    return {
        "message": "Welcome to the Self-Improving Agent System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """System health check"""
    # Check database
    agents = await database.agents.get_all_active()
    
    # Get runtime stats if available
    runtime_integration = get_runtime_integration()
    runtime_stats = {}
    if runtime_integration:
        runtime_stats = {"runtime": "active"}
    
    return {
        "status": "healthy",
        "database": "connected", 
        "active_agents": len(agents),
        "runtime": runtime_stats,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Static files for web interface (production-ready)
web_build_path = Path(__file__).parent.parent / "web" / "build"
web_static_path = web_build_path / "static"
web_index_path = web_build_path / "index.html"

if web_build_path.exists() and web_index_path.exists():
    # Production build available
    app.mount("/static", StaticFiles(directory=str(web_static_path)), name="static")
    
    @app.get("/app", response_class=HTMLResponse)
    async def serve_app():
        """Serve the React app"""
        try:
            with open(web_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        except Exception as e:
            return HTMLResponse(
                content=f"<h1>Error loading web interface</h1><p>{str(e)}</p>",
                status_code=500
            )
    
    # Serve React app for any unmatched routes (SPA routing)
    @app.get("/app/{path:path}", response_class=HTMLResponse)
    async def serve_app_routes(path: str):
        """Serve React app for client-side routing"""
        return await serve_app()
        
    print(f"✅ Web interface available at /app")
        
else:
    # Web interface not built yet - provide helpful placeholder
    @app.get("/app", response_class=HTMLResponse)
    async def serve_placeholder():
        """Enhanced placeholder for web interface"""
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Self-Improving Agent System - Process-First Architecture</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; line-height: 1.6; }
                    .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .status { background: #e8f5e8; padding: 15px; border-radius: 6px; margin: 10px 0; }
                    .warning { background: #fff3e0; padding: 15px; border-radius: 6px; margin: 10px 0; }
                    .links { background: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
                    .link { display: inline-block; margin: 5px 10px 5px 0; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                    .link:hover { background: #0056b3; }
                    code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Consolas', monospace; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🤖 Self-Improving Agent System</h1>
                    <h2>Process-First Recursive Architecture</h2>
                    <p><strong>Status:</strong> API Server Running | <strong>Architecture:</strong> Process-First Framework Established</p>
                </div>
                
                <div class="status">
                    <h3>✅ System Status</h3>
                    <p>The process-first foundation is operational and ready for systematic task execution.</p>
                </div>
                
                <div class="warning">
                    <h3>🔧 Web Interface Not Built</h3>
                    <p>The React web interface has not been built yet. To build it:</p>
                    <ol>
                        <li>Navigate to the <code>web/</code> directory</li>
                        <li>Run <code>npm install</code></li>
                        <li>Run <code>npm run build</code></li>
                        <li>Refresh this page</li>
                    </ol>
                </div>
                
                <div class="links">
                    <h3>🚀 Quick Access</h3>
                    <a href="/docs" class="link">API Documentation</a>
                    <a href="/health" class="link">Health Check</a>
                    <a href="/system/stats" class="link">System Stats</a>
                    <a href="/agents" class="link">Agents</a>
                    <a href="/tasks/active" class="link">Active Tasks</a>
                    
                    <h4>Process-First Architecture</h4>
                    <p>This system operates on systematic framework establishment before execution. Every task goes through:</p>
                    <ol>
                        <li><strong>Process Discovery</strong> - Analyze domain requirements</li>
                        <li><strong>Framework Establishment</strong> - Create systematic structures</li>
                        <li><strong>Context Assembly</strong> - Provide complete knowledge</li>
                        <li><strong>Isolated Execution</strong> - Tasks succeed independently</li>
                    </ol>
                </div>
            </body>
        </html>
        """)


# Make global instances available for dependency injection
def get_database():
    """Get database instance for dependency injection"""
    return database


def get_websocket_manager():
    """Get WebSocket manager for dependency injection"""
    return manager


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )