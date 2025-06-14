#!/bin/bash
# Service management script for agent system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/../venv"
BACKEND_PID_FILE="$PROJECT_DIR/logs/backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/logs/frontend.pid"
BACKEND_LOG="$PROJECT_DIR/logs/backend.log"
FRONTEND_LOG="$PROJECT_DIR/logs/frontend.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
        kill "$pid" 2>/dev/null
        
        # Wait for process to stop (max 5 seconds)
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 5 ]; do
            sleep 0.5
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${RED}Force killing $service_name...${NC}"
            kill -9 "$pid" 2>/dev/null
        fi
        
        rm -f "$pid_file"
        echo -e "${GREEN}$service_name stopped${NC}"
    else
        echo -e "${YELLOW}$service_name is not running${NC}"
    fi
}

# Function to start backend
start_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        echo -e "${YELLOW}Backend is already running (PID: $(cat $BACKEND_PID_FILE))${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Starting backend...${NC}"
    cd "$PROJECT_DIR"
    
    # Clear previous log
    > "$BACKEND_LOG"
    
    # Start backend with proper environment
    source "$VENV_DIR/bin/activate"
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$BACKEND_PID_FILE"
    
    # Wait for backend to start (check for successful startup message)
    echo -n "Waiting for backend to start"
    local count=0
    while [ $count -lt 20 ]; do  # Max 10 seconds
        if grep -q "Application startup complete" "$BACKEND_LOG" 2>/dev/null; then
            echo -e "\n${GREEN}Backend started successfully (PID: $pid)${NC}"
            
            # Show any errors or important messages
            if grep -E "(ERROR|WARNING|CRITICAL)" "$BACKEND_LOG" 2>/dev/null; then
                echo -e "${YELLOW}Warnings/Errors found in backend log:${NC}"
                grep -E "(ERROR|WARNING|CRITICAL)" "$BACKEND_LOG" | head -5
            fi
            
            # Show the last few lines of the log
            echo -e "${GREEN}Backend log (last 5 lines):${NC}"
            tail -5 "$BACKEND_LOG"
            return 0
        fi
        
        # Check if process died
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo -e "\n${RED}Backend failed to start!${NC}"
            echo -e "${RED}Error output:${NC}"
            cat "$BACKEND_LOG"
            rm -f "$BACKEND_PID_FILE"
            return 1
        fi
        
        echo -n "."
        sleep 0.5
        count=$((count + 1))
    done
    
    echo -e "\n${YELLOW}Backend started but may not be ready yet (PID: $pid)${NC}"
    echo "Check $BACKEND_LOG for details"
    return 0
}

# Function to start frontend
start_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        echo -e "${YELLOW}Frontend is already running (PID: $(cat $FRONTEND_PID_FILE))${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Starting frontend...${NC}"
    cd "$PROJECT_DIR/web"
    
    # Clear previous log
    > "$FRONTEND_LOG"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install --legacy-peer-deps > "$FRONTEND_LOG" 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies!${NC}"
            tail -20 "$FRONTEND_LOG"
            return 1
        fi
    fi
    
    # Start frontend
    nohup npm start > "$FRONTEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID_FILE"
    
    # Wait for frontend to start
    echo -n "Waiting for frontend to start"
    local count=0
    while [ $count -lt 20 ]; do  # Max 10 seconds
        if grep -q "Compiled successfully\|webpack compiled\|On Your Network" "$FRONTEND_LOG" 2>/dev/null; then
            echo -e "\n${GREEN}Frontend started successfully (PID: $pid)${NC}"
            
            # Extract the URL
            local url=$(grep -oE "http://[0-9.:]+|On Your Network:.*http[s]?://[0-9.:]+" "$FRONTEND_LOG" | head -1)
            if [ -n "$url" ]; then
                echo -e "${GREEN}Frontend URL: $url${NC}"
            fi
            
            return 0
        fi
        
        # Check if process died
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo -e "\n${RED}Frontend failed to start!${NC}"
            echo -e "${RED}Error output:${NC}"
            tail -20 "$FRONTEND_LOG"
            rm -f "$FRONTEND_PID_FILE"
            return 1
        fi
        
        echo -n "."
        sleep 0.5
        count=$((count + 1))
    done
    
    echo -e "\n${YELLOW}Frontend started but may not be ready yet (PID: $pid)${NC}"
    echo "Check $FRONTEND_LOG for details"
    return 0
}

# Function to check status
check_status() {
    echo -e "${GREEN}=== Agent System Status ===${NC}"
    
    # Backend status
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        echo -e "Backend:  ${GREEN}Running${NC} (PID: $backend_pid)"
        
        # Check if backend is responding
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "  Health: ${GREEN}OK${NC}"
        else
            echo -e "  Health: ${YELLOW}Not responding${NC}"
        fi
    else
        echo -e "Backend:  ${RED}Stopped${NC}"
    fi
    
    # Frontend status
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "Frontend: ${GREEN}Running${NC} (PID: $frontend_pid)"
        
        # Check if frontend is responding
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "  Health: ${GREEN}OK${NC}"
        else
            echo -e "  Health: ${YELLOW}Not responding${NC}"
        fi
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi
}

# Function to tail logs
tail_logs() {
    local service=$1
    local lines=${2:-20}
    
    case $service in
        backend)
            echo -e "${GREEN}=== Backend Log (last $lines lines) ===${NC}"
            tail -n "$lines" "$BACKEND_LOG"
            ;;
        frontend)
            echo -e "${GREEN}=== Frontend Log (last $lines lines) ===${NC}"
            tail -n "$lines" "$FRONTEND_LOG"
            ;;
        both)
            echo -e "${GREEN}=== Backend Log (last $lines lines) ===${NC}"
            tail -n "$lines" "$BACKEND_LOG"
            echo -e "\n${GREEN}=== Frontend Log (last $lines lines) ===${NC}"
            tail -n "$lines" "$FRONTEND_LOG"
            ;;
        *)
            echo -e "${RED}Unknown service: $service${NC}"
            echo "Use: backend, frontend, or both"
            ;;
    esac
}

# Main command handling
case "$1" in
    start)
        case "$2" in
            backend)
                start_backend
                ;;
            frontend)
                start_frontend
                ;;
            all|"")
                start_backend
                echo
                start_frontend
                ;;
            *)
                echo -e "${RED}Unknown service: $2${NC}"
                echo "Usage: $0 start [backend|frontend|all]"
                exit 1
                ;;
        esac
        ;;
    
    stop)
        case "$2" in
            backend)
                stop_service "Backend" "$BACKEND_PID_FILE"
                ;;
            frontend)
                stop_service "Frontend" "$FRONTEND_PID_FILE"
                ;;
            all|"")
                stop_service "Frontend" "$FRONTEND_PID_FILE"
                stop_service "Backend" "$BACKEND_PID_FILE"
                ;;
            *)
                echo -e "${RED}Unknown service: $2${NC}"
                echo "Usage: $0 stop [backend|frontend|all]"
                exit 1
                ;;
        esac
        ;;
    
    restart)
        case "$2" in
            backend)
                stop_service "Backend" "$BACKEND_PID_FILE"
                sleep 1
                start_backend
                ;;
            frontend)
                stop_service "Frontend" "$FRONTEND_PID_FILE"
                sleep 1
                start_frontend
                ;;
            all|"")
                stop_service "Frontend" "$FRONTEND_PID_FILE"
                stop_service "Backend" "$BACKEND_PID_FILE"
                sleep 1
                start_backend
                echo
                start_frontend
                ;;
            *)
                echo -e "${RED}Unknown service: $2${NC}"
                echo "Usage: $0 restart [backend|frontend|all]"
                exit 1
                ;;
        esac
        ;;
    
    status)
        check_status
        ;;
    
    logs)
        tail_logs "${2:-both}" "${3:-20}"
        ;;
    
    health)
        # Quick health check
        echo -n "Backend: "
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAIL${NC}"
        fi
        
        echo -n "Frontend: "
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAIL${NC}"
        fi
        ;;
    
    *)
        echo -e "${YELLOW}Agent System Service Manager${NC}"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|health} [service]"
        echo
        echo "Commands:"
        echo "  start [backend|frontend|all]   - Start services"
        echo "  stop [backend|frontend|all]    - Stop services"
        echo "  restart [backend|frontend|all] - Restart services"
        echo "  status                         - Show service status"
        echo "  logs [backend|frontend|both] [lines] - Show recent logs"
        echo "  health                         - Quick health check"
        echo
        echo "Examples:"
        echo "  $0 start                      # Start all services"
        echo "  $0 restart backend            # Restart only backend"
        echo "  $0 logs backend 50            # Show last 50 lines of backend log"
        echo "  $0 status                     # Check service status"
        exit 1
        ;;
esac