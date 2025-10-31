# 🚀 Service Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the Cryptocurrency Trading System as a service across different platforms and environments.

## 📁 Service Files Structure

```
services/
├── crypto-trading.service      # Linux systemd service
├── com.crypto.trading.plist    # macOS launchd service
└── install-windows-service.ps1 # Windows service installer

scripts/
├── service-manager.sh          # Universal service management
└── deploy.sh                  # Deployment automation

Dockerfile                     # Container deployment
docker-compose.yml             # Multi-container setup
```

## 🐧 Linux Deployment (systemd)

### Automatic Installation
```bash
# Use the service manager (recommended)
./scripts/service-manager.sh install
./scripts/service-manager.sh start
```

### Manual Installation
```bash
# 1. Copy service file
sudo cp services/crypto-trading.service /etc/systemd/system/

# 2. Update paths in service file (replace /opt/crypto-trading with your path)
sudo nano /etc/systemd/system/crypto-trading.service

# 3. Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable crypto-trading.service

# 4. Start service
sudo systemctl start crypto-trading.service

# 5. Check status
sudo systemctl status crypto-trading.service
```

### Management Commands
```bash
# Status
sudo systemctl status crypto-trading

# Start/Stop/Restart
sudo systemctl start crypto-trading
sudo systemctl stop crypto-trading
sudo systemctl restart crypto-trading

# View logs
sudo journalctl -u crypto-trading -f

# Enable/Disable auto-start
sudo systemctl enable crypto-trading
sudo systemctl disable crypto-trading
```

## 🍎 macOS Deployment (launchd)

### Automatic Installation
```bash
# Use the service manager (recommended)
./scripts/service-manager.sh install
./scripts/service-manager.sh start
```

### Manual Installation
```bash
# 1. Copy plist file
cp services/com.crypto.trading.plist ~/Library/LaunchAgents/

# 2. Update paths in plist file (replace USERNAME with your username)
nano ~/Library/LaunchAgents/com.crypto.trading.plist

# 3. Load service
launchctl load ~/Library/LaunchAgents/com.crypto.trading.plist

# 4. Start service
launchctl start com.crypto.trading
```

### Management Commands
```bash
# Status
launchctl list | grep crypto.trading

# Start/Stop
launchctl start com.crypto.trading
launchctl stop com.crypto.trading

# View logs
tail -f ~/Library/Logs/crypto-trading.log

# Unload service
launchctl unload ~/Library/LaunchAgents/com.crypto.trading.plist
```

## 🪟 Windows Deployment (NSSM)

### Prerequisites
1. Download and install [NSSM](https://nssm.cc/download)
2. Run PowerShell as Administrator

### Installation
```powershell
# Run the installation script
.\services\install-windows-service.ps1
```

### Management Commands
```cmd
# Status
sc query CryptoTrading

# Start/Stop
net start CryptoTrading
net stop CryptoTrading

# View service properties
nssm edit CryptoTrading

# Remove service
nssm remove CryptoTrading confirm
```

## 🐳 Docker Deployment

### Single Container
```bash
# Build image
docker build -t crypto-trading:latest .

# Run container
docker run -d \
  --name crypto-trading \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env:ro \
  crypto-trading:latest
```

### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f crypto-trading

# Stop services
docker-compose down

# Update and restart
docker-compose pull
docker-compose up -d --force-recreate
```

## 🔧 Universal Service Manager

The `scripts/service-manager.sh` script provides unified service management across all platforms:

```bash
# Install service for current platform
./scripts/service-manager.sh install

# Start service
./scripts/service-manager.sh start

# Stop service
./scripts/service-manager.sh stop

# Restart service
./scripts/service-manager.sh restart

# Check status
./scripts/service-manager.sh status

# View logs (follow mode)
./scripts/service-manager.sh logs

# Uninstall service
./scripts/service-manager.sh uninstall
```

## 🚀 Automated Deployment

Use the deployment script for automated server deployment:

```bash
# Deploy to different environments
./scripts/deploy.sh development
./scripts/deploy.sh staging
./scripts/deploy.sh production
```

## 📊 Monitoring & Logs

### Log Locations
- **Linux**: `/opt/crypto-trading/logs/` or `journalctl -u crypto-trading`
- **macOS**: `~/Library/Logs/crypto-trading.log` or project `logs/` directory
- **Windows**: Project `logs/` directory
- **Docker**: `docker logs crypto-trading` or `docker-compose logs`

### Log Files
```
logs/
├── service.log           # Service stdout
├── service-error.log     # Service stderr
└── trading_system.log    # Application logs
```

## 🔒 Security Considerations

### File Permissions
```bash
# Secure the .env file
chmod 600 .env

# Set proper ownership
sudo chown -R $USER:$USER /opt/crypto-trading
chmod +x scripts/*.sh
```

### Firewall Configuration
```bash
# Linux (UFW)
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 8080/tcp      # Optional: monitoring port

# Deny unnecessary access
sudo ufw --force enable
```

### User Configuration
```bash
# Create dedicated user (recommended for production)
sudo useradd --system --home /opt/crypto-trading --shell /bin/bash crypto-trading
sudo chown -R crypto-trading:crypto-trading /opt/crypto-trading
```

## 🔄 Auto-Updates with Watchtower (Docker)

The `docker-compose.yml` includes Watchtower for automatic updates:

```yaml
watchtower:
  image: containrrr/watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  environment:
    - WATCHTOWER_CLEANUP=true
    - WATCHTOWER_POLL_INTERVAL=3600
```

## 📈 Health Checks & Monitoring

### Built-in Health Checks
- Docker containers include health check endpoints
- Service manager provides status monitoring
- Log rotation and retention policies

### External Monitoring Integration
- Prometheus metrics endpoint (if enabled)
- Grafana dashboards
- Telegram alerts for service status

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Denied**
```bash
# Fix file permissions
chmod +x scripts/*.sh
sudo chown -R $USER:$USER .
```

2. **Service Won't Start**
```bash
# Check logs
./scripts/service-manager.sh status
tail -f logs/service-error.log
```

3. **Python Environment Issues**
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. **Port Already in Use**
```bash
# Find process using port
sudo lsof -i :8080
sudo netstat -tulpn | grep :8080
```

### Service Recovery
```bash
# Restart failed service
./scripts/service-manager.sh restart

# View detailed status
./scripts/service-manager.sh status

# Check system resources
htop
df -h
free -h
```

## 📚 Additional Resources

- [systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [launchd Documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [NSSM Documentation](https://nssm.cc/usage)

---

## Quick Start Summary

1. **Clone repository**: `git clone <repo-url>`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure environment**: `cp .env.example .env` (edit as needed)
4. **Install service**: `./scripts/service-manager.sh install`
5. **Start trading**: `./scripts/service-manager.sh start`
6. **Monitor logs**: `./scripts/service-manager.sh logs`

🎉 **Your crypto trading system is now running as a service!**