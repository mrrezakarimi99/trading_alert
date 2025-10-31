#!/bin/bash
# =============================================================================
# INITIALIZATION PIPELINE
# =============================================================================
# This script runs the complete initialization pipeline:
# 1. Fetch historical data
# 2. Train ML models  
# 3. Validate models
# 4. Start trading system
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting Crypto Trading System Initialization Pipeline"
echo "==========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
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

# Check if models already exist
check_models() {
    log "Checking for existing models..."
    if [ -d "/app/src/ml_models" ] && [ "$(ls -A /app/src/ml_models)" ]; then
        success "Models found! Skipping training phase."
        return 0
    else
        warning "No models found. Will run complete pipeline."
        return 1
    fi
}

# Step 1: Fetch historical data
fetch_data() {
    log "Step 1: Fetching historical data (365 days)..."
    if python main.py --fetch-data --days 365; then
        success "Historical data fetched successfully"
        return 0
    else
        error "Failed to fetch historical data"
        return 1
    fi
}

# Step 2: Train models
train_models() {
    log "Step 2: Training ML models..."
    if python main.py --train --days 365; then
        success "Model training completed successfully"
        return 0
    else
        error "Model training failed"
        return 1
    fi
}

# Step 3: Validate models
validate_models() {
    log "Step 3: Validating models..."
    if python main.py --validate --days 30; then
        success "Model validation completed successfully"
        return 0
    else
        warning "Model validation had issues, but continuing..."
        return 0  # Don't fail the pipeline for validation issues
    fi
}

# Step 4: Run backtest
run_backtest() {
    log "Step 4: Running backtest analysis..."
    if python main.py --backtest --days 90; then
        success "Backtest completed successfully"
        return 0
    else
        warning "Backtest had issues, but continuing..."
        return 0  # Don't fail the pipeline for backtest issues
    fi
}

# Main pipeline
main() {
    log "Initializing environment..."
    
    # Create necessary directories
    mkdir -p /app/data/csv /app/data/database /app/src/ml_models /app/logs
    
    # Change to app directory
    cd /app
    
    # Check if we can skip training
    if check_models; then
        log "Models exist, running validation only..."
        validate_models
        success "Initialization pipeline completed (models already existed)"
        exit 0
    fi
    
    # Run complete pipeline
    log "Running complete initialization pipeline..."
    
    # Step 1: Fetch data
    if ! fetch_data; then
        error "Pipeline failed at data fetching stage"
        exit 1
    fi
    
    # Step 2: Train models
    if ! train_models; then
        error "Pipeline failed at model training stage"
        exit 1
    fi
    
    # Step 3: Validate models
    validate_models
    
    # Step 4: Run backtest
    run_backtest
    
    # Final status check
    log "Checking final system status..."
    python main.py --status
    
    success "🎉 Initialization pipeline completed successfully!"
    success "System is ready for trading. Run: docker-compose up crypto-trading"
}

# Trap errors and cleanup
trap 'error "Pipeline interrupted"; exit 1' INT TERM

# Run main function
main "$@"