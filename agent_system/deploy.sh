#!/bin/bash

# Deployment script for Self-Improving Agent System
echo "🚀 Deploying Self-Improving Agent System - Complete Foundation"
echo "=============================================================="

# Set up error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ $(echo $python_version | cut -d. -f1) -lt 3 ]] || [[ $(echo $python_version | cut -d. -f2) -lt 11 ]]; then
    print_error "Python 3.11+ required, found $python_version"
    exit 1
fi
print_status "Python $python_version detected"

# Check Node.js version
echo "📋 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    exit 1
fi
node_version=$(node --version)
print_status "Node.js $node_version detected"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
fi

source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
print_status "Python dependencies installed"

# Install Node.js dependencies and build frontend
echo "📦 Installing Node.js dependencies..."
cd web
npm install > /dev/null 2>&1
print_status "Node.js dependencies installed"

echo "🏗️ Building production frontend..."
npm run build > /dev/null 2>&1
print_status "Frontend built successfully"
cd ..

# Check environment configuration
echo "🔧 Checking environment configuration..."
if [ ! -f ".env" ]; then
    print_warning "No .env file found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning "Please edit .env with your API keys before starting"
    else
        print_error "No .env.example file found"
        exit 1
    fi
fi
print_status "Environment configuration ready"

# Initialize the complete system
echo "🤖 Initializing complete agent system..."
python scripts/seed_system.py
if [ $? -eq 0 ]; then
    print_status "Complete system initialized successfully"
else
    print_error "System initialization failed"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the API server:"
echo "   python -m api.main"
echo ""
echo "2. Access the web interface:"
echo "   http://localhost:8000/app (served by FastAPI)"
echo "   or"
echo "   http://localhost:3000 (development server: cd web && npm start)"
echo ""
echo "3. API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. System health check:"
echo "   http://localhost:8000/health"
echo ""
echo "🤖 Complete Foundation Ready:"
echo "   • 9 Specialized Agents"
echo "   • Full Context Documentation"
echo "   • Comprehensive MCP Toolkit"
echo "   • Advanced Integration Tools"
echo "   • Real-time Web Interface"
echo ""
echo "Submit advanced tasks and watch unlimited growth! 🚀"