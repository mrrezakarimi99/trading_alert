# 🚀 Crypto Trading System

A professional cryptocurrency trading system powered by machine learning that automatically trades Bitcoin and other cryptocurrencies using LSTM neural networks for price prediction.

## ✨ Features

- 🤖 **AI-Powered Trading**: LSTM neural networks for price prediction
- 📊 **Multi-Asset Support**: Bitcoin, Ethereum, and more cryptocurrencies
- 🔒 **Risk Management**: Portfolio-based position sizing and risk controls
- 📱 **Telegram Alerts**: Real-time notifications and trading signals
- 🐳 **Docker Ready**: Easy deployment with Docker
- 📈 **Backtesting**: Historical performance analysis
- 🔄 **Auto-Recovery**: Robust error handling and recovery

## 🏗️ Architecture

```
├── main.py                 # Main trading application
├── docker-manager.sh       # Docker operations manager
├── service-manager.sh      # Service operations manager
├── entrypoint.sh          # Container entrypoint
├── docker-compose.yml     # Multi-service deployment
└── src/                   # Core application
    ├── models/            # Data models
    ├── services/          # Business logic
    └── storage/           # Data persistence
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- `.env` file with your configuration

### 1️⃣ Initial Setup
```bash
# Make scripts executable
chmod +x *.sh

# Complete setup (first time)
./docker-manager.sh setup
```

### 2️⃣ Start Trading
```bash
# Start the trading system
./docker-manager.sh start

# Monitor system
./docker-manager.sh logs
```

## 🛠️ Management Commands

### Docker Operations
```bash
./docker-manager.sh setup      # Complete first-time setup
./docker-manager.sh start      # Start trading system  
./docker-manager.sh stop       # Stop all services
./docker-manager.sh restart    # Restart system
./docker-manager.sh logs       # View live logs
./docker-manager.sh status     # System status
./docker-manager.sh clean      # Clean containers
./docker-manager.sh reset      # Complete reset (removes data!)
```

### Service Operations  
```bash
./service-manager.sh health-check    # Full system health check
./service-manager.sh check-models    # Check trained models
./service-manager.sh check-data      # Check historical data
./service-manager.sh model-info      # Show model information
./service-manager.sh backup-data     # Backup models and data
```

### Individual Operations
```bash
# Data & Training
./docker-manager.sh fetch      # Fetch historical data only
./docker-manager.sh train      # Train ML models only
./docker-manager.sh init       # Data + training (no start)

# Monitoring
./docker-manager.sh ps         # Show containers
./service-manager.sh check-env # Check environment variables
```

## ⚙️ Configuration

### Environment Variables (.env file)
```bash
# Portfolio Settings
PORTFOLIO_SIZE=1000.0           # Total portfolio value
MAX_RISK_PER_TRADE=0.02        # Risk per trade (2%)

# API Keys (Optional but recommended)
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
COINGECKO_API_KEY=your_key

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# System Settings
FETCH_INTERVAL=300             # Data fetch interval (seconds)
LOG_LEVEL=INFO                 # Logging level
```

### Supported Assets
- Bitcoin (BTC)
- Ethereum (ETH) 
- Other major cryptocurrencies

## 📊 Usage Examples

### First Time Setup
```bash
# Complete setup and start trading
./docker-manager.sh setup

# Check everything is working
./service-manager.sh health-check
```

### Daily Operations
```bash
# Check system status
./docker-manager.sh status

# View recent activity
./docker-manager.sh logs

# Monitor model performance
./service-manager.sh model-info
```

### Maintenance
```bash
# Update models weekly
./docker-manager.sh train

# Backup important data
./service-manager.sh backup-data

# System restart
./docker-manager.sh restart
```

## 🔍 Monitoring

### Real-time Monitoring
```bash
# Live logs
./docker-manager.sh logs

# Container status
./docker-manager.sh ps

# System health
./service-manager.sh health-check
```

### Health Indicators
- ✅ **Models**: Trained and ready
- ✅ **Data**: Historical data available  
- ✅ **APIs**: External services accessible
- ✅ **Telegram**: Notifications working

## 🐳 Docker Services

The system runs multiple Docker services:

| Service | Purpose | Command |
|---------|---------|---------|
| `data-fetcher` | Fetch historical data | `docker compose up data-fetcher` |
| `trainer` | Train ML models | `docker compose up trainer` |
| `crypto-trading` | Main trading system | `docker compose up -d crypto-trading` |
| `watchtower` | Auto-updates | Runs automatically |

## 🔧 Troubleshooting

### Common Issues

**"Missing models" error:**
```bash
./docker-manager.sh train    # Train models first
```

**"No data found" error:**
```bash
./docker-manager.sh fetch    # Fetch data first
```

**Container won't start:**
```bash
./docker-manager.sh clean    # Clean and rebuild
./docker-manager.sh build
```

**Check system health:**
```bash
./service-manager.sh health-check
./docker-manager.sh status
```

### Log Locations
- Container logs: `./docker-manager.sh logs`
- Local logs: `./logs/trading_system.log`
- Service status: `./docker-manager.sh status`

## 📁 Project Structure

```
crypto-trading-system/
├── 🐳 Docker Management
│   ├── docker-manager.sh      # Main Docker operations
│   ├── docker-compose.yml     # Service definitions  
│   ├── Dockerfile             # Container image
│   └── entrypoint.sh          # Container startup
├── 🔧 Service Management  
│   └── service-manager.sh     # Service operations
├── 🚀 Application
│   ├── main.py                # Trading application
│   ├── requirements.txt       # Dependencies
│   └── src/                   # Source code
├── 📊 Data & Models
│   ├── data/                  # Historical data
│   └── src/ml_models/         # Trained models
└── 📝 Documentation
    └── README.md              # This file
```

## 🔐 Security

- All services run as non-root user
- Environment variables for sensitive data
- Resource limits to prevent abuse
- Health checks for monitoring

## 📞 Support

**Quick Help:**
```bash
./docker-manager.sh --help      # Docker commands
./service-manager.sh --help     # Service commands
```

**System Status:**
```bash
./service-manager.sh health-check
```

## ⚠️ Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Always conduct your own research and never invest more than you can afford to lose.