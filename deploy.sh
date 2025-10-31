#!/bin/bash
# =============================================================================
# DOCKER DEPLOYMENT SCRIPT
# =============================================================================
# Easy deployment script for the crypto trading system
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

show_help() {
    echo "Crypto Trading System - Docker Deployment"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  init          Run complete initialization (data + training + validation)"
    echo "  fetch         Fetch historical data only"
    echo "  train         Train models only (requires data)"
    echo "  trade         Start trading system only (requires trained models)"
    echo "  full          Run complete pipeline and start trading"
    echo "  status        Show system status"
    echo "  logs          Show logs"
    echo "  stop          Stop all services"
    echo "  clean         Stop and remove all containers and volumes"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init       # Initialize system (first time setup)"
    echo "  $0 trade      # Start trading (if models exist)"
    echo "  $0 full       # Complete setup and start trading"
    echo "  $0 logs       # View logs"
}

init_system() {
    log "Initializing crypto trading system..."
    docker-compose build
    docker-compose up init-pipeline
    success "System initialization completed!"
}

fetch_data() {
    log "Fetching historical data..."
    docker-compose build
    docker-compose up data-fetcher
    success "Data fetching completed!"
}

train_models() {
    log "Training ML models..."
    docker-compose build
    docker-compose up trainer
    success "Model training completed!"
}

start_trading() {
    log "Starting trading system..."
    docker-compose up -d crypto-trading watchtower
    success "Trading system started!"
    log "Use '$0 logs' to view logs"
}

full_deployment() {
    log "Running complete deployment pipeline..."
    docker-compose build
    
    # Run initialization
    log "Step 1: Running initialization..."
    docker-compose up init-pipeline
    
    # Start trading
    log "Step 2: Starting trading system..."
    docker-compose up -d crypto-trading watchtower
    
    success "Complete deployment finished!"
    log "Use '$0 logs' to view logs"
}

show_status() {
    log "System Status:"
    echo ""
    docker-compose ps
    echo ""
    
    # Try to show system status if trading container is running
    if docker-compose ps | grep -q "crypto-trading-system.*Up"; then
        log "Getting system status from trading container..."
        docker-compose exec crypto-trading python main.py --status || true
    fi
}

show_logs() {
    log "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

stop_system() {
    log "Stopping all services..."
    docker-compose down
    success "All services stopped!"
}

clean_system() {
    log "Cleaning up system (this will remove all data!)..."
    read -p "Are you sure? This will delete all data and models! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        success "System cleaned!"
    else
        log "Cleanup cancelled."
    fi
}

# Main script logic
case "${1:-help}" in
    init)
        init_system
        ;;
    fetch)
        fetch_data
        ;;
    train)
        train_models
        ;;
    trade)
        start_trading
        ;;
    full)
        full_deployment
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    stop)
        stop_system
        ;;
    clean)
        clean_system
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac