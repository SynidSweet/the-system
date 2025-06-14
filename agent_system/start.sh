#!/bin/bash

# Production startup script for Self-Improving Agent System
echo "🚀 Starting Self-Improving Agent System - Complete Foundation"
echo "=============================================================="

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

# Check if we're in the right directory
if [ ! -f "scripts/seed_system.py" ]; then
    print_error "Please run this script from the agent_system directory"
    exit 1
fi

# Check if system is initialized
if [ ! -f "agent_system.db" ]; then
    print_warning "System not initialized. Running deployment first..."
    ./deploy.sh
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./deploy.sh first"
    exit 1
fi

source venv/bin/activate
print_status "Virtual environment activated"

# Check environment
if [ ! -f ".env" ]; then
    print_error "No .env file found. Please run ./deploy.sh first"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    print_error "No API key found in .env file. Please add ANTHROPIC_API_KEY or OPENAI_API_KEY"
    exit 1
fi

print_status "Environment configuration loaded"

# Start the system
echo ""
echo "🤖 Starting Complete Agent System..."
echo "   • 9 Specialized Agents Ready"
echo "   • Full MCP Toolkit Loaded"
echo "   • Real-time Web Interface"
echo "   • Database: agent_system.db"
echo ""

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    print_error "Port 8000 is already in use. Please stop the existing process."
    exit 1
fi

print_status "Port 8000 available"
echo ""
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🖥️ Web interface: http://localhost:8000/app"
echo "🏥 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
python -m api.main