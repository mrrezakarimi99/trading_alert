#!/bin/bash
# =============================================================================
# SERVICE MANAGER - UNIVERSAL SHELL SCRIPT
# =============================================================================
# File: scripts/service-manager.sh
# Usage: ./scripts/service-manager.sh [start|stop|restart|status|install|uninstall]
# =============================================================================

set -e

# Configuration
SERVICE_NAME="crypto-trading"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
LOG_DIR="$PROJECT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Detect operating system
detect_os() {
    case "$OSTYPE" in
        linux-gnu*) echo "linux" ;;
        darwin*)    echo "macos" ;;
        cygwin*)    echo "windows" ;;
        msys*)      echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

# Check if service is running
is_running() {
    local os=$(detect_os)
    case $os in
        "linux")
            systemctl is-active --quiet $SERVICE_NAME 2>/dev/null
            ;;
        "macos")
            launchctl list | grep -q "com.crypto.trading" 2>/dev/null
            ;;
        *)
            pgrep -f "python.*main.py" > /dev/null 2>&1
            ;;
    esac
}

# Start service
start_service() {
    local os=$(detect_os)
    
    if is_running; then
        log_warn "Service is already running"
        return 0
    fi
    
    log_info "Starting $SERVICE_NAME service..."
    
    case $os in
        "linux")
            sudo systemctl start $SERVICE_NAME
            ;;
        "macos")
            launchctl start com.crypto.trading
            ;;
        *)
            # Direct execution for other systems
            mkdir -p "$LOG_DIR"
            nohup $PYTHON_PATH $MAIN_SCRIPT > "$LOG_DIR/service.log" 2>&1 &
            echo $! > "$PROJECT_DIR/service.pid"
            ;;
    esac
    
    sleep 2
    if is_running; then
        log_info "Service started successfully"
    else
        log_error "Failed to start service"
        exit 1
    fi
}

# Stop service
stop_service() {
    local os=$(detect_os)
    
    if ! is_running; then
        log_warn "Service is not running"
        return 0
    fi
    
    log_info "Stopping $SERVICE_NAME service..."
    
    case $os in
        "linux")
            sudo systemctl stop $SERVICE_NAME
            ;;
        "macos")
            launchctl stop com.crypto.trading
            ;;
        *)
            # Kill by PID file or process name
            if [ -f "$PROJECT_DIR/service.pid" ]; then
                kill $(cat "$PROJECT_DIR/service.pid") 2>/dev/null || true
                rm -f "$PROJECT_DIR/service.pid"
            else
                pkill -f "python.*main.py" || true
            fi
            ;;
    esac
    
    sleep 2
    if ! is_running; then
        log_info "Service stopped successfully"
    else
        log_error "Failed to stop service"
        exit 1
    fi
}

# Restart service
restart_service() {
    log_info "Restarting $SERVICE_NAME service..."
    stop_service
    sleep 2
    start_service
}

# Show service status
show_status() {
    local os=$(detect_os)
    
    log_info "Service status for $SERVICE_NAME:"
    
    if is_running; then
        echo -e "${GREEN}● $SERVICE_NAME is running${NC}"
    else
        echo -e "${RED}● $SERVICE_NAME is stopped${NC}"
    fi
    
    case $os in
        "linux")
            sudo systemctl status $SERVICE_NAME --no-pager -l
            ;;
        "macos")
            launchctl list | grep crypto.trading || echo "Service not found in launchctl"
            ;;
        *)
            if [ -f "$PROJECT_DIR/service.pid" ]; then
                echo "PID file: $(cat "$PROJECT_DIR/service.pid")"
            fi
            pgrep -f "python.*main.py" | head -5
            ;;
    esac
}

# Install service
install_service() {
    local os=$(detect_os)
    
    log_info "Installing $SERVICE_NAME service for $os..."
    
    case $os in
        "linux")
            # Copy systemd service file
            sudo cp "$PROJECT_DIR/services/crypto-trading.service" /etc/systemd/system/
            # Update paths in service file
            sudo sed -i "s|/opt/crypto-trading|$PROJECT_DIR|g" /etc/systemd/system/crypto-trading.service
            sudo sed -i "s|User=ubuntu|User=$USER|g" /etc/systemd/system/crypto-trading.service
            sudo sed -i "s|Group=ubuntu|Group=$USER|g" /etc/systemd/system/crypto-trading.service
            
            sudo systemctl daemon-reload
            sudo systemctl enable crypto-trading.service
            log_info "Systemd service installed and enabled"
            ;;
        "macos")
            # Copy launchd plist
            cp "$PROJECT_DIR/services/com.crypto.trading.plist" ~/Library/LaunchAgents/
            # Update paths in plist file
            sed -i '' "s|/Users/USERNAME|$HOME|g" ~/Library/LaunchAgents/com.crypto.trading.plist
            
            launchctl load ~/Library/LaunchAgents/com.crypto.trading.plist
            log_info "Launchd service installed and loaded"
            ;;
        *)
            log_warn "Automatic service installation not supported for $os"
            log_info "Please manually configure the service using your system's service manager"
            ;;
    esac
}

# Uninstall service
uninstall_service() {
    local os=$(detect_os)
    
    log_info "Uninstalling $SERVICE_NAME service..."
    
    # Stop service first
    stop_service 2>/dev/null || true
    
    case $os in
        "linux")
            sudo systemctl disable crypto-trading.service 2>/dev/null || true
            sudo rm -f /etc/systemd/system/crypto-trading.service
            sudo systemctl daemon-reload
            log_info "Systemd service uninstalled"
            ;;
        "macos")
            launchctl unload ~/Library/LaunchAgents/com.crypto.trading.plist 2>/dev/null || true
            rm -f ~/Library/LaunchAgents/com.crypto.trading.plist
            log_info "Launchd service uninstalled"
            ;;
        *)
            rm -f "$PROJECT_DIR/service.pid"
            log_info "Service files cleaned up"
            ;;
    esac
}

# Show logs
show_logs() {
    local os=$(detect_os)
    
    log_info "Showing logs for $SERVICE_NAME:"
    
    case $os in
        "linux")
            sudo journalctl -u $SERVICE_NAME -f --no-pager
            ;;
        "macos")
            tail -f ~/Library/Logs/crypto-trading.log 2>/dev/null || tail -f "$LOG_DIR/service.log"
            ;;
        *)
            tail -f "$LOG_DIR/service.log"
            ;;
    esac
}

# Main script logic
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|install|uninstall|logs}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the crypto trading service"
        echo "  stop      - Stop the crypto trading service"
        echo "  restart   - Restart the crypto trading service"
        echo "  status    - Show service status"
        echo "  install   - Install service for auto-start"
        echo "  uninstall - Remove service"
        echo "  logs      - Show service logs (follow mode)"
        exit 1
        ;;
esac