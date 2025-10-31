# Docker Multi-Service Deployment Guide

This document explains how to deploy the Crypto Trading System using the new multi-service Docker architecture.

## 🏗️ Architecture Overview

The system is now split into separate services:

1. **`data-fetcher`** - Fetches historical data from crypto APIs
2. **`trainer`** - Trains ML models using the fetched data  
3. **`crypto-trading`** - Main trading system (requires trained models)
4. **`init-pipeline`** - Runs complete initialization pipeline
5. **`watchtower`** - Auto-updates containers

## 🚀 Quick Start

### Method 1: Use the Deploy Script (Recommended)

```bash
# Make script executable
chmod +x deploy.sh

# Complete setup (data + training + trading)
./deploy.sh full

# Or step by step:
./deploy.sh init    # Initialize (data + training)
./deploy.sh trade   # Start trading
```

### Method 2: Manual Docker Compose

```bash
# Complete initialization
docker-compose up init-pipeline

# Start trading system
docker-compose up -d crypto-trading watchtower
```

### Method 3: Step by Step

```bash
# Step 1: Fetch historical data
docker-compose up data-fetcher

# Step 2: Train ML models  
docker-compose up trainer

# Step 3: Start trading
docker-compose up -d crypto-trading watchtower
```

## 📋 Available Commands

### Deploy Script Commands

```bash
./deploy.sh init      # Run initialization pipeline
./deploy.sh fetch     # Fetch data only
./deploy.sh train     # Train models only  
./deploy.sh trade     # Start trading only
./deploy.sh full      # Complete deployment
./deploy.sh status    # Show system status
./deploy.sh logs      # View logs
./deploy.sh stop      # Stop all services
./deploy.sh clean     # Clean everything (removes data!)
```

### Docker Compose Commands

```bash
# Individual services
docker-compose up data-fetcher          # Fetch data
docker-compose up trainer               # Train models
docker-compose up -d crypto-trading     # Start trading
docker-compose up init-pipeline         # Complete init

# Management
docker-compose ps                       # Show status
docker-compose logs -f [service]        # View logs
docker-compose down                     # Stop all
docker-compose down -v                  # Stop and remove data
```

## 🔧 Service Dependencies

```
data-fetcher (no dependencies)
    ↓
trainer (requires data)
    ↓  
crypto-trading (requires trained models)
```

## 📁 Data Persistence

All data is stored in Docker volumes:

- **`data_volume`**: Contains CSV files, database, and trained models
- **Local logs**: Mounted to `./logs/` directory

## 🔍 Troubleshooting

### Models Missing Error

```
ERROR - Missing models for: ['bitcoin']  
INFO - Run training first: python main.py --train
```

**Solution:**
```bash
# Run training
./deploy.sh train
# Or
docker-compose up trainer
```

### Insufficient Data Error

```
WARNING - Insufficient data for training bitcoin
```

**Solution:**
```bash
# Fetch more data
./deploy.sh fetch
# Or
docker-compose up data-fetcher
```

### Service Won't Start

**Check service status:**
```bash
./deploy.sh status
docker-compose ps
```

**Check logs:**
```bash
./deploy.sh logs
docker-compose logs -f [service-name]
```

## 📊 Monitoring

### View System Status
```bash
./deploy.sh status
```

### View Logs
```bash
# All services
./deploy.sh logs

# Specific service
docker-compose logs -f crypto-trading
docker-compose logs -f trainer
```

### Health Checks

The trading service includes health checks:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds  
- **Start Period**: 90 seconds (allows time for model loading)

## 🔒 Security

- All services run as non-root user (UID 1000)
- Environment variables loaded from `.env` file
- Resource limits applied to trading service
- Log rotation configured

## 🚦 Production Deployment

### First Time Setup

1. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Run complete deployment:**
   ```bash
   ./deploy.sh full
   ```

3. **Monitor system:**
   ```bash
   ./deploy.sh status
   ./deploy.sh logs
   ```

### Regular Operations

```bash
# Check status
./deploy.sh status

# View logs
./deploy.sh logs

# Restart if needed
./deploy.sh stop
./deploy.sh trade

# Update models (weekly/monthly)
./deploy.sh train
```

### Backup Important Data

```bash
# Backup trained models
docker run --rm -v crypto_data_volume:/data -v $(pwd):/backup alpine tar czf /backup/models-backup.tar.gz -C /data/src/ml_models .

# Backup database
docker run --rm -v crypto_data_volume:/data -v $(pwd):/backup alpine tar czf /backup/db-backup.tar.gz -C /data/database .
```

## 🆘 Emergency Procedures

### Complete System Reset

```bash
⚠️  WARNING: This removes all data and models!
./deploy.sh clean
```

### Partial Reset (Keep Data)

```bash
# Stop services but keep data
./deploy.sh stop

# Restart
./deploy.sh trade
```

### Force Rebuild

```bash
docker-compose down
docker-compose build --no-cache
./deploy.sh full
```

## 📈 Performance Tips

1. **Resource Allocation**: Adjust memory/CPU limits in docker-compose.yml
2. **Data Retention**: Clean old CSV files periodically  
3. **Model Updates**: Retrain models weekly/monthly
4. **Log Management**: Log rotation is configured, but monitor disk usage

## 🔄 Updates

The system includes Watchtower for automatic updates:

- **Check Interval**: Every hour
- **Auto-cleanup**: Enabled
- **Target**: Only the trading container

To disable auto-updates, remove the watchtower service from docker-compose.yml.