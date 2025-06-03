#!/bin/bash

# Install systemd services for automatic startup on boot
echo "📦 Installing Agent System systemd services..."

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then 
    echo "This script needs to be run with sudo"
    echo "Usage: sudo ./install-services.sh"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Copy service files
print_status "Copying service files to systemd directory..."
cp "$SCRIPT_DIR/agent-system-backend.service" /etc/systemd/system/
cp "$SCRIPT_DIR/agent-system-frontend.service" /etc/systemd/system/

# Create environment file if it doesn't exist in systemd
if [ -f "$SCRIPT_DIR/.env" ]; then
    print_status "Copying environment file..."
    cp "$SCRIPT_DIR/.env" /etc/systemd/system/agent-system.env
    chmod 600 /etc/systemd/system/agent-system.env
    
    # Update service files to use the new env location
    sed -i 's|EnvironmentFile=.*|EnvironmentFile=/etc/systemd/system/agent-system.env|g' /etc/systemd/system/agent-system-backend.service
else
    print_warning ".env file not found. Services will start without environment variables."
fi

# Reload systemd
print_status "Reloading systemd configuration..."
systemctl daemon-reload

# Enable services
print_status "Enabling services to start on boot..."
systemctl enable agent-system-backend.service
systemctl enable agent-system-frontend.service

# Check status
echo ""
echo "📊 Service Status:"
echo "=================="
systemctl is-enabled agent-system-backend.service | xargs -I {} echo "Backend: {}"
systemctl is-enabled agent-system-frontend.service | xargs -I {} echo "Frontend: {}"

echo ""
echo "🎯 Available Commands:"
echo "====================="
echo "Start services:    sudo systemctl start agent-system-backend agent-system-frontend"
echo "Stop services:     sudo systemctl stop agent-system-backend agent-system-frontend"
echo "Restart services:  sudo systemctl restart agent-system-backend agent-system-frontend"
echo "Check status:      sudo systemctl status agent-system-backend agent-system-frontend"
echo "View logs:         sudo journalctl -u agent-system-backend -f"
echo "                   sudo journalctl -u agent-system-frontend -f"
echo ""
echo "✅ Services installed successfully!"
echo "The Agent System will now start automatically on system boot."