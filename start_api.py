#!/usr/bin/env python3
"""
Standalone API server launcher for The System.
Properly configures Python path and starts the FastAPI server.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path so agent_system module can be found
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now we can import the FastAPI app
from agent_system.api.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )