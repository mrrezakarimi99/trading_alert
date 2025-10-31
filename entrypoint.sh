#!/bin/bash
# =============================================================================
# DOCKER ENTRYPOINT - Simple Service Starter
# =============================================================================

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Change to app directory
cd /app

# Get service mode
SERVICE_MODE=${SERVICE_MODE:-trade}
log "Starting in $SERVICE_MODE mode..."

# Initialize directories
mkdir -p data/csv data/database src/ml_models logs /tmp/matplotlib

# Basic dependency check
case $SERVICE_MODE in
    "fetch")
        log "📊 Data fetching mode - ready to start"
        ;;
    "train")
        log "🧠 Training mode - checking for data..."
        if [ -d "data/csv" ] && [ "$(ls -A data/csv 2>/dev/null)" ]; then
            success "✅ Data found!"
        elif [ -d "data/database" ] && [ "$(ls -A data/database 2>/dev/null)" ]; then
            success "✅ Database found!"
        else
            log "⚠️  No data found, will fetch during training"
        fi
        ;;
    "trade")
        log "💹 Trading mode - checking for models..."
        if [ -d "src/ml_models" ] && [ "$(ls -A src/ml_models/*.h5 2>/dev/null)" ]; then
            success "✅ Models found!"
        else
            error "❌ No trained models found!"
            log "💡 Run training first: docker-manager.sh train"
            exit 1
        fi
        ;;
esac

success "🚀 Dependencies satisfied - starting service"

# Execute the main command
log "▶️  Executing: $@"
exec "$@"