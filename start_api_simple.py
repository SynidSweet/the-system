#!/usr/bin/env python3
"""
Simplified startup wrapper for The System.
Uses unified startup configuration for database + basic functionality.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from start_unified import create_app
from agent_system.core.startup import StartupConfig, StartupMode
import uvicorn

if __name__ == "__main__":
    # Create simplified system configuration
    config = StartupConfig.for_mode(StartupMode.SIMPLIFIED)
    app = create_app(config)
    
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