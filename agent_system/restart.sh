#!/bin/bash

# Self-Improving Agent System - Restart/Control Script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check if process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to stop the system
stop_system() {
    echo "🛑 Stopping Agent System..."
    
    # Stop backend
    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_status "Backend stopped (PID: $PID)"
        fi
        rm -f logs/backend.pid
    else
        pkill -f "uvicorn api.main:app" || true
    fi
    
    # Stop frontend
    if [ -f "logs/frontend.pid" ]; then
        PID=$(cat logs/frontend.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_status "Frontend stopped (PID: $PID)"
        fi
        rm -f logs/frontend.pid
    else
        pkill -f "yarn start" || true
        pkill -f "react-scripts start" || true
    fi
    
    # Wait for processes to stop
    sleep 2
    
    # Force kill if still running
    pkill -9 -f "uvicorn api.main:app" 2>/dev/null || true
    pkill -9 -f "react-scripts start" 2>/dev/null || true
    
    print_status "Agent System stopped"
}

# Function to show status
show_status() {
    echo "📊 Agent System Status"
    echo "===================="
    
    # Check backend
    if check_process "uvicorn api.main:app"; then
        print_status "Backend is running"
        if [ -f "logs/backend.pid" ]; then
            echo "    PID: $(cat logs/backend.pid)"
        fi
    else
        print_error "Backend is not running"
    fi
    
    # Check frontend
    if check_process "react-scripts start"; then
        print_status "Frontend is running"
        if [ -f "logs/frontend.pid" ]; then
            echo "    PID: $(cat logs/frontend.pid)"
        fi
    else
        print_error "Frontend is not running"
    fi
    
    # Check health endpoint
    echo ""
    print_info "Checking health endpoint..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        HEALTH=$(curl -s http://localhost:8000/health)
        print_status "Backend API is healthy"
        echo "    Response: $HEALTH"
    else
        print_warning "Backend API is not responding"
    fi
    
    echo ""
    echo "📂 Log files:"
    if [ -f "logs/backend.log" ]; then
        echo "   • Backend: logs/backend.log ($(wc -l < logs/backend.log) lines)"
    fi
    if [ -f "logs/frontend.log" ]; then
        echo "   • Frontend: logs/frontend.log ($(wc -l < logs/frontend.log) lines)"
    fi
}

# Function to show logs
show_logs() {
    case "$1" in
        backend)
            if [ -f "logs/backend.log" ]; then
                tail -f logs/backend.log
            else
                print_error "Backend log file not found"
            fi
            ;;
        frontend)
            if [ -f "logs/frontend.log" ]; then
                tail -f logs/frontend.log
            else
                print_error "Frontend log file not found"
            fi
            ;;
        *)
            print_error "Please specify 'backend' or 'frontend'"
            echo "Usage: $0 logs [backend|frontend]"
            ;;
    esac
}

# Main command handling
case "$1" in
    start)
        if check_process "uvicorn api.main:app" || check_process "react-scripts start"; then
            print_warning "Agent System is already running"
            show_status
            exit 1
        fi
        ./startup.sh
        ;;
        
    stop)
        stop_system
        ;;
        
    restart)
        echo "🔄 Restarting Agent System..."
        stop_system
        sleep 2
        ./startup.sh
        ;;
        
    status)
        show_status
        ;;
        
    logs)
        show_logs "$2"
        ;;
        
    *)
        echo "🤖 Agent System Control Script"
        echo "=============================="
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the agent system"
        echo "  stop     - Stop the agent system"
        echo "  restart  - Restart the agent system"
        echo "  status   - Show system status"
        echo "  logs     - Show logs (specify backend or frontend)"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 logs backend"
        exit 1
        ;;
esac