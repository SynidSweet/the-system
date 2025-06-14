#!/bin/bash

# Self-Improving Agent System - Background Startup Script
echo "🚀 Starting Self-Improving Agent System in background..."

# Set up error handling
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "scripts/seed_system.py" ]; then
    print_error "Please run this script from the agent_system directory"
    exit 1
fi

# Check if system is initialized
if [ ! -f "data/agent_system.db" ]; then
    print_warning "System not initialized. Running deployment first..."
    ./deploy.sh
fi

# Check virtual environment
if [ ! -d "../venv" ]; then
    print_error "Virtual environment not found. Please run ./deploy.sh first"
    exit 1
fi

# Check environment file
if [ ! -f ".env" ]; then
    print_error "No .env file found. Please run ./deploy.sh first"
    exit 1
fi

# Stop any existing instances
print_status "Stopping any existing instances..."
pkill -f "uvicorn api.main:app" || true
pkill -f "yarn start" || true
pkill -f "react-scripts start" || true
sleep 2

# Create log directory if it doesn't exist
mkdir -p logs

# Start backend
print_status "Starting backend API server..."
source ../venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    print_error "No API key found in .env file. Please add ANTHROPIC_API_KEY or OPENAI_API_KEY"
    exit 1
fi

nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid
print_status "Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    print_error "Backend failed to start. Check logs/backend.log for details"
    exit 1
fi

# Start frontend
print_status "Starting frontend web interface..."
cd web
if [ ! -d "node_modules" ]; then
    print_warning "Installing frontend dependencies..."
    npm install
fi

nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
print_status "Frontend started (PID: $FRONTEND_PID)"

# Summary
echo ""
echo "=========================================="
echo "🤖 Agent System started successfully!"
echo "=========================================="
echo ""
echo "📚 Backend API: http://localhost:8000"
echo "📄 API Docs: http://localhost:8000/docs"
echo "🖥️  Frontend: http://localhost:3000"
echo "🏥 Health: http://localhost:8000/health"
echo ""
echo "📂 Logs:"
echo "   • Backend: logs/backend.log"
echo "   • Frontend: logs/frontend.log"
echo ""
echo "To stop the system, run: ./restart.sh stop"
echo "To check status, run: ./restart.sh status"