#!/bin/bash
# =============================================================================
# CRYPTO TRADING SYSTEM - DOCKER MANAGER
# =============================================================================
# Single script to manage all Docker operations for the crypto trading system
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

show_help() {
    echo "🚀 Crypto Trading System - Docker Manager"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "📦 SETUP COMMANDS:"
    echo "  init          Complete setup (data + training)"
    echo "  build         Build Docker images"
    echo "  setup         First-time complete setup and start"
    echo ""
    echo "🔄 SERVICE COMMANDS:"
    echo "  start         Start trading system"
    echo "  stop          Stop all services"
    echo "  restart       Restart trading system"
    echo "  logs          Show live logs"
    echo ""
    echo "📊 DATA & TRAINING:"
    echo "  fetch         Fetch historical data only"
    echo "  train         Train ML models only"
    echo ""
    echo "🔍 MONITORING:"
    echo "  status        Show system status"
    echo "  ps            Show running containers"
    echo ""
    echo "🧹 MAINTENANCE:"
    echo "  clean         Stop and remove containers"
    echo "  reset         Complete system reset (removes all data!)"
    echo "  update        Update and restart system"
    echo ""
    echo "Examples:"
    echo "  $0 setup      # First time setup"
    echo "  $0 start      # Start trading"
    echo "  $0 logs       # View logs"
    echo "  $0 status     # Check status"
}

check_dependencies() {
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker is not installed!"
        exit 1
    fi
    
    if ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose is not available!"
        exit 1
    fi
}

build_images() {
    log "Building Docker images..."
    docker compose build
    success "Images built successfully!"
}

init_system() {
    log "🔧 Initializing crypto trading system..."
    check_dependencies
    build_images
    
    log "📊 Fetching historical data..."
    docker compose up data-fetcher
    
    log "🧠 Training ML models..."
    docker compose up trainer
    
    success "System initialization completed!"
    log "💡 Use '$0 start' to begin trading"
}

setup_complete() {
    log "🚀 Running complete setup and starting system..."
    init_system
    
    log "▶️  Starting trading system..."
    docker compose up -d crypto-trading watchtower
    
    success "🎉 System is running!"
    log "📱 Use '$0 logs' to monitor activity"
    log "📊 Use '$0 status' to check system health"
}

start_system() {
    log "▶️  Starting crypto trading system..."
    check_dependencies
    docker compose up -d crypto-trading watchtower
    success "Trading system started!"
    log "💡 Use '$0 logs' to view logs"
}

stop_system() {
    log "⏹️  Stopping all services..."
    docker compose down
    success "All services stopped!"
}

restart_system() {
    log "🔄 Restarting trading system..."
    stop_system
    sleep 2
    start_system
}

show_logs() {
    log "📋 Showing logs (Ctrl+C to exit)..."
    docker compose logs -f
}

fetch_data() {
    log "📊 Fetching historical data..."
    check_dependencies
    build_images
    docker compose up data-fetcher
    success "Data fetching completed!"
}

train_models() {
    log "🧠 Training ML models..."
    check_dependencies
    build_images
    docker compose up trainer
    success "Model training completed!"
}

show_status() {
    log "📊 System Status:"
    echo ""
    
    # Show container status
    echo "🐳 Container Status:"
    docker compose ps 2>/dev/null || echo "No containers running"
    echo ""
    
    # Try to get system status from trading container
    if docker compose ps 2>/dev/null | grep -q "crypto-trading-system.*Up"; then
        echo "🎯 Trading System Status:"
        docker compose exec crypto-trading python main.py --status 2>/dev/null || echo "Could not retrieve trading status"
    else
        warning "Trading system is not running"
        log "💡 Use '$0 start' to start the system"
    fi
}

show_ps() {
    log "🐳 Running containers:"
    docker compose ps
}

clean_system() {
    log "🧹 Cleaning up containers..."
    docker compose down --remove-orphans
    docker system prune -f
    success "System cleaned!"
}

reset_system() {
    warning "🚨 This will delete ALL data and models!"
    read -p "Are you sure? Type 'yes' to confirm: " -r
    if [[ $REPLY == "yes" ]]; then
        log "🗑️  Performing complete system reset..."
        docker compose down -v --remove-orphans
        docker system prune -af
        success "🔄 System completely reset!"
        log "💡 Use '$0 setup' to reinitialize"
    else
        log "Reset cancelled"
    fi
}

update_system() {
    log "🔄 Updating system..."
    stop_system
    build_images
    start_system
    success "System updated and restarted!"
}

# Main command handler
case "${1:-help}" in
    init)          init_system ;;
    build)         build_images ;;
    setup)         setup_complete ;;
    start)         start_system ;;
    stop)          stop_system ;;
    restart)       restart_system ;;
    logs)          show_logs ;;
    fetch)         fetch_data ;;
    train)         train_models ;;
    status)        show_status ;;
    ps)            show_ps ;;
    clean)         clean_system ;;
    reset)         reset_system ;;
    update)        update_system ;;
    help|--help|-h) show_help ;;
    *)
        error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac