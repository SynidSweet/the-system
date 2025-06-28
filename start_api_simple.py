#!/usr/bin/env python3
"""
Simplified API server launcher for The System.
Starts the main API without complex initialization.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path so agent_system module can be found
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import database manager
from agent_system.config.database import DatabaseManager

# Create FastAPI app without lifespan management
app = FastAPI(
    title="Self-Improving Agent System",
    description="A process-first recursive agent system (simplified startup)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create global database instance
database = DatabaseManager()

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Self-Improving Agent System", 
        "version": "1.0.0",
        "status": "running",
        "mode": "simplified",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    try:
        # Test database connection
        await database.connect()
        db_status = "connected"
        await database.disconnect()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "mode": "simplified",
        "database": db_status,
        "message": "System is operational with basic functionality"
    }

@app.get("/api/v1/health")
async def api_health():
    return {
        "status": "healthy",
        "timestamp": "2025-06-28",
        "dependencies": {
            "fastapi": "installed",
            "uvicorn": "installed", 
            "database": "available",
            "entity_system": "not_initialized",
            "runtime": "not_initialized"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting The System API (Simplified Mode)...")
    print("📄 API Documentation: http://localhost:8002/docs")
    print("❤️  Health Check: http://localhost:8002/health")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )