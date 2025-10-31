#!/bin/bash
# =============================================================================
# DOCKER ENTRYPOINT SCRIPT
# =============================================================================
# This script handles service startup with proper dependency checking
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

# Change to app directory
cd /app

# Get service mode
SERVICE_MODE=${SERVICE_MODE:-trade}
log "Starting in $SERVICE_MODE mode..."

# Run service check first
log "Running service dependency check..."
if python /app/scripts/service-check.py; then
    success "Service dependencies satisfied"
else
    error "Service dependencies not met"
    exit 1
fi

# Execute the main command
log "Executing: $@"
exec "$@"