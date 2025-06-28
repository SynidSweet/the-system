#!/bin/bash
# Setup script for The System
# Creates virtual environment and installs dependencies

set -e

echo "🚀 Setting up The System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To start the system:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start API server: python start_api.py"
echo "3. Open browser to: http://localhost:8000/docs"