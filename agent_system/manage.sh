#!/bin/bash

# Agent System Management Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/../venv"

case "$1" in
    start)
        echo "Starting Agent System..."
        
        # Start backend
        cd "$SCRIPT_DIR"
        source "$VENV_PATH/bin/activate"
        nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        echo "Backend started (PID: $!)"
        
        # Start frontend
        cd "$SCRIPT_DIR/web"
        nohup yarn start > web.log 2>&1 &
        echo "Frontend started (PID: $!)"
        
        echo "Agent System is starting up..."
        echo "Backend: http://localhost:8000"
        echo "Frontend: http://localhost:3000"
        ;;
        
    stop)
        echo "Stopping Agent System..."
        pkill -f "uvicorn api.main:app"
        pkill -f "yarn start"
        pkill -f "react-scripts start"
        echo "Agent System stopped"
        ;;
        
    status)
        echo "Agent System Status:"
        if pgrep -f "uvicorn api.main:app" > /dev/null; then
            echo "✓ Backend is running"
        else
            echo "✗ Backend is not running"
        fi
        
        if pgrep -f "react-scripts start" > /dev/null; then
            echo "✓ Frontend is running"
        else
            echo "✗ Frontend is not running"
        fi
        ;;
        
    logs)
        case "$2" in
            backend)
                tail -f "$SCRIPT_DIR/backend.log"
                ;;
            frontend)
                tail -f "$SCRIPT_DIR/web/web.log"
                ;;
            *)
                echo "Usage: $0 logs [backend|frontend]"
                ;;
        esac
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|logs}"
        exit 1
        ;;
esac