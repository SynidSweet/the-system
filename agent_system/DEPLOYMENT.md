# Production Deployment Guide

## 🚀 Quick Start

### 1. Clone and Deploy
```bash
git clone <your-repo-url> the-system
cd the-system/agent_system
./deploy.sh
```

### 2. Configure Environment
```bash
# Edit .env with your API keys
nano .env

# Add either:
ANTHROPIC_API_KEY=your_anthropic_key_here
# OR
OPENAI_API_KEY=your_openai_key_here
```

### 3. Start the System
```bash
./start.sh
```

Access at: http://your-server:8000

## 🔧 Production Setup (EC2/VPS)

### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.11+
- Node.js 16+
- At least 2GB RAM, 10GB disk space

### Step-by-Step Setup

1. **Update System**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip nodejs npm git -y
```

2. **Clone Repository**
```bash
cd ~
git clone <your-repo-url> the-system
cd the-system/agent_system
```

3. **Deploy System**
```bash
./deploy.sh
```

4. **Configure Environment**
```bash
nano .env
# Add your API keys
```

5. **Install as System Service** (optional)
```bash
# Copy service file
sudo cp agent-system.service /etc/systemd/system/

# Update paths in service file if needed
sudo nano /etc/systemd/system/agent-system.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable agent-system
sudo systemctl start agent-system

# Check status
sudo systemctl status agent-system
```

6. **Setup Reverse Proxy** (optional)
```bash
# Install nginx
sudo apt install nginx -y

# Create nginx config
sudo tee /etc/nginx/sites-available/agent-system << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/agent-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🛡️ Security Configuration

### Firewall Setup
```bash
# Basic firewall setup
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

### SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Test renewal
sudo certbot renew --dry-run
```

## 📊 Monitoring

### System Logs
```bash
# Service logs
sudo journalctl -u agent-system -f

# Application logs
tail -f ~/the-system/agent_system/logs/app.log
```

### Health Checks
```bash
# API health check
curl http://localhost:8000/health

# System status
sudo systemctl status agent-system
```

## 🔄 Updates

### Update Application
```bash
cd ~/the-system
git pull origin main
cd agent_system
./deploy.sh

# If using systemd service
sudo systemctl restart agent-system
```

## 📱 Web Interface Features

The production UI includes:

- **📋 Tasks Tab**: Real-time task monitoring and management
- **🤖 Agents Tab**: View all 9 available agents and their capabilities
- **⚙️ System Tab**: System health monitoring and status
- **🔌 Real-time Updates**: WebSocket integration for live updates
- **📱 Mobile Responsive**: Works on all devices
- **🚨 Error Handling**: Comprehensive error reporting and recovery

## 🎯 Complete Foundation

The system includes:
- ✅ **9 Specialized Agents** with detailed instructions
- ✅ **Full Context Documentation** (20+ documents)
- ✅ **Complete MCP Toolkit** (7 core + 6 system tools)
- ✅ **Advanced Database Schema** (5 tables)
- ✅ **Real-time Web Interface** with 3 monitoring tabs
- ✅ **Production Configuration** with security hardening

## 🚨 Troubleshooting

### Common Issues

1. **Port 8000 in use**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

2. **Database locked**
```bash
# Stop service and restart
sudo systemctl stop agent-system
sudo systemctl start agent-system
```

3. **Permission errors**
```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu ~/the-system
```

4. **API key errors**
```bash
# Check environment
source venv/bin/activate
python -c "import os; print('ANTHROPIC_API_KEY' in os.environ)"
```

## 📞 Support

For issues:
1. Check logs: `sudo journalctl -u agent-system -f`
2. Verify health: `curl http://localhost:8000/health`
3. Review environment: Check `.env` file
4. Restart system: `sudo systemctl restart agent-system`

The complete foundation is ready for advanced tasks! 🚀