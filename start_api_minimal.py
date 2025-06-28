#!/usr/bin/env python3
"""
Minimal API server launcher for The System.
Bypasses complex initialization to get basic API running.
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

# Create minimal FastAPI app
app = FastAPI(
    title="Self-Improving Agent System (Minimal)",
    description="Basic API server for The System",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "The System API is running (minimal mode)", "status": "healthy"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": "minimal",
        "message": "Basic API is operational"
    }

@app.get("/api/v1/health")
async def api_health():
    return {
        "status": "healthy", 
        "timestamp": "2025-06-28",
        "dependencies": {
            "fastapi": "installed",
            "uvicorn": "installed",
            "database": "not_initialized"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting The System API (Minimal Mode)...")
    print("📄 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )