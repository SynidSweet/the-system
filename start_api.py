#!/usr/bin/env python3
"""
Full system startup wrapper for The System.
Uses unified startup configuration for complete system initialization.
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
    # Create full system configuration
    config = StartupConfig.for_mode(StartupMode.FULL)
    app = create_app(config)
    
    print("🚀 Starting The System API (Full Mode)...")
    print("📄 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    print("🌐 Web Interface: http://localhost:8000/app")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )