#!/bin/bash
# =============================================================================
# SETUP VERIFICATION SCRIPT
# =============================================================================
# File: scripts/verify-setup.sh
# Usage: ./scripts/verify-setup.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log_info() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC}  $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_check() { echo -e "${BLUE}🔍${NC} $1"; }

echo "🚀 Cryptocurrency Trading System - Setup Verification"
echo "======================================================"

# Check Python environment
log_check "Checking Python environment..."
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_VERSION=$($PROJECT_DIR/.venv/bin/python --version)
    log_info "Python virtual environment found: $PYTHON_VERSION"
else
    log_error "Python virtual environment not found"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# Check requirements
log_check "Checking Python dependencies..."
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    if $PROJECT_DIR/.venv/bin/python -c "import requests, pandas, numpy, tensorflow" 2>/dev/null; then
        log_info "All required Python packages are installed"
    else
        log_warn "Some Python packages may be missing"
        echo "Run: source .venv/bin/activate && pip install -r requirements.txt"
    fi
else
    log_error "requirements.txt not found"
fi

# Check configuration file
log_check "Checking configuration..."
if [ -f "$PROJECT_DIR/.env" ]; then
    log_info ".env configuration file found"
    
    # Check critical environment variables
    if grep -q "TELEGRAM_BOT_TOKEN=" "$PROJECT_DIR/.env"; then
        log_info "Telegram configuration present"
    else
        log_warn "Telegram configuration may be incomplete"
    fi
    
    if grep -q "TRADING_ASSETS=" "$PROJECT_DIR/.env"; then
        ASSETS=$(grep "TRADING_ASSETS=" "$PROJECT_DIR/.env" | cut -d'=' -f2)
        log_info "Trading assets configured: $ASSETS"
    fi
else
    log_error ".env configuration file not found"
    echo "Copy .env.example to .env and configure your settings"
fi

# Check directories
log_check "Checking directory structure..."
for dir in "data/csv" "data/database" "logs" "src" "tests"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        log_info "Directory exists: $dir"
    else
        log_warn "Directory missing: $dir"
        mkdir -p "$PROJECT_DIR/$dir"
        log_info "Created directory: $dir"
    fi
done

# Check service files
log_check "Checking service files..."
for file in "services/crypto-trading.service" "services/com.crypto.trading.plist" "scripts/service-manager.sh"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        log_info "Service file exists: $file"
    else
        log_error "Service file missing: $file"
    fi
done

# Check executable permissions
log_check "Checking script permissions..."
for script in "scripts/service-manager.sh" "scripts/deploy.sh"; do
    if [ -x "$PROJECT_DIR/$script" ]; then
        log_info "Script is executable: $script"
    else
        log_warn "Script not executable: $script"
        chmod +x "$PROJECT_DIR/$script"
        log_info "Made script executable: $script"
    fi
done

# Check Git configuration
log_check "Checking Git configuration..."
if [ -f "$PROJECT_DIR/.gitignore" ]; then
    log_info ".gitignore file configured"
else
    log_warn ".gitignore file missing"
fi

if [ -f "$PROJECT_DIR/.gitattributes" ]; then
    log_info ".gitattributes file configured for large files"
else
    log_warn ".gitattributes file missing"
fi

# Test basic functionality
log_check "Testing basic functionality..."
if $PROJECT_DIR/.venv/bin/python -c "
import sys
sys.path.append('$PROJECT_DIR')
try:
    from src.services.data_service import DataService
    from src.services.telegram_service import TelegramService
    print('✅ Core modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    log_info "Core modules test passed"
else
    log_error "Core modules test failed"
fi

# Operating system specific checks
OS=$(uname -s)
log_check "Checking OS-specific configurations for $OS..."

case $OS in
    "Linux")
        if command -v systemctl &> /dev/null; then
            log_info "systemd available for service management"
        else
            log_warn "systemd not available"
        fi
        ;;
    "Darwin")
        if command -v launchctl &> /dev/null; then
            log_info "launchd available for service management"
        else
            log_warn "launchd not available"
        fi
        ;;
    *)
        log_info "Generic service management will be used"
        ;;
esac

# Docker check
log_check "Checking Docker availability..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    log_info "Docker available: $DOCKER_VERSION"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        log_info "Docker Compose available: $COMPOSE_VERSION"
    else
        log_warn "Docker Compose not available"
    fi
else
    log_warn "Docker not available (optional for containerized deployment)"
fi

echo ""
echo "📊 Setup Verification Summary"
echo "=============================="

# Final recommendations
echo "🔧 Next Steps:"
echo "1. Configure your .env file with proper API keys and settings"
echo "2. Test the system: $PROJECT_DIR/.venv/bin/python main.py --status"
echo "3. Install as service: ./scripts/service-manager.sh install"
echo "4. Start trading: ./scripts/service-manager.sh start"
echo ""
echo "📚 Documentation:"
echo "- Service deployment: SERVICE_DEPLOYMENT.md"
echo "- General setup: README.md"
echo ""
echo "✅ Verification completed!"