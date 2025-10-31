# 🚀 Server Deployment Quick Guide

## Simple Docker Deployment for Server

### 1. Clone Repository on Server
```bash
git clone https://github.com/mrrezakarimi99/trading_alert.git
cd trading_alert
git checkout development
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp .env .env.production
nano .env.production

# Create symbolic link
ln -sf .env.production .env
```

### 3. Deploy with Docker Compose
```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f crypto-trading
```

### 4. Management Commands
```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# Update and restart
git pull origin development
docker-compose up -d --build

# View live logs
docker-compose logs -f crypto-trading

# Check container status
docker-compose ps
```

### 5. Monitoring
```bash
# View recent logs
docker-compose logs --tail=50 crypto-trading

# Check resource usage
docker stats crypto-trading-system

# Access container shell (if needed)
docker-compose exec crypto-trading bash
```

## Fixed Issues ✅

- **Permission Errors**: Fixed by properly setting user permissions in Dockerfile
- **Log File Access**: Added fallback to console-only logging if file permissions fail
- **Container Ownership**: Uses UID 1000 for consistent permissions

## File Structure on Server
```
/opt/trading_alert/
├── docker-compose.yml
├── Dockerfile
├── .env → .env.production
├── data/          # Persistent data (mounted volume)
├── logs/          # Log files (mounted volume)
└── src/           # Application code
```

The system will now run properly in Docker without permission issues! 🎉