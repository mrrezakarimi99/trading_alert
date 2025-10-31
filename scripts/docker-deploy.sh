#!/bin/bash
# =============================================================================
# DOCKER DEPLOYMENT SCRIPT WITH PERMISSION FIX
# =============================================================================
# File: scripts/docker-deploy.sh
# Usage: ./scripts/docker-deploy.sh [up|down|restart|logs|build]
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get current user ID and group ID
export UID=$(id -u)
export GID=$(id -g)

log_info "Using UID:GID = $UID:$GID for Docker containers"

# Ensure directories exist and are properly initialized
setup_directories() {
    log_info "Setting up directories..."
    
    cd "$PROJECT_DIR"
    
    # Run initialization script
    if [ -f "scripts/docker-init.sh" ]; then
        chmod +x scripts/docker-init.sh
        ./scripts/docker-init.sh
    else
        # Fallback: create directories manually
        mkdir -p data/csv data/database logs
        chmod 755 data data/csv data/database logs
    fi
    
    log_info "Directories initialized"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    cd "$PROJECT_DIR"
    docker build -t crypto-trading:latest .
    log_info "Docker image built successfully"
}

# Start services
start_services() {
    log_info "Starting Docker services..."
    cd "$PROJECT_DIR"
    
    setup_directories
    
    docker-compose up -d
    log_info "Services started successfully"
    
    # Show status
    sleep 3
    docker-compose ps
}

# Stop services
stop_services() {
    log_info "Stopping Docker services..."
    cd "$PROJECT_DIR"
    docker-compose down
    log_info "Services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting Docker services..."
    stop_services
    sleep 2
    start_services
}

# Show logs
show_logs() {
    log_info "Showing Docker logs..."
    cd "$PROJECT_DIR"
    docker-compose logs -f crypto-trading
}

# Clean up everything
cleanup() {
    log_info "Cleaning up Docker environment..."
    cd "$PROJECT_DIR"
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove images
    docker rmi crypto-trading:latest 2>/dev/null || true
    
    # Clean up Docker system
    docker system prune -f
    
    log_info "Cleanup completed"
}

# Show status
show_status() {
    log_info "Docker service status:"
    cd "$PROJECT_DIR"
    
    echo ""
    echo "=== Container Status ==="
    docker-compose ps
    
    echo ""
    echo "=== Resource Usage ==="
    docker stats --no-stream crypto-trading-system 2>/dev/null || echo "Container not running"
    
    echo ""
    echo "=== Recent Logs ==="
    docker-compose logs --tail=10 crypto-trading 2>/dev/null || echo "No logs available"
}

# Main command handling
case "${1:-up}" in
    up|start)
        start_services
        ;;
    down|stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    build)
        build_image
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {up|down|restart|logs|build|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  up       - Start the crypto trading services"
        echo "  down     - Stop the crypto trading services"
        echo "  restart  - Restart the crypto trading services"
        echo "  logs     - Show live logs"
        echo "  build    - Build Docker image"
        echo "  status   - Show service status and stats"
        echo "  cleanup  - Clean up all Docker resources"
        exit 1
        ;;
esac