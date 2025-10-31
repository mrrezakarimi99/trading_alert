#!/bin/bash
# =============================================================================
# DOCKER INIT SCRIPT - ENSURE DIRECTORIES EXIST
# =============================================================================
# File: scripts/docker-init.sh
# Usage: ./scripts/docker-init.sh
# =============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔧 Initializing Docker environment..."

cd "$PROJECT_DIR"

# Create required directories on host
echo "📁 Creating directories..."
mkdir -p data/csv
mkdir -p data/database
mkdir -p logs

# Set permissions (this won't affect container, just ensures they exist)
echo "🔒 Setting basic permissions..."
chmod 755 data
chmod 755 data/csv
chmod 755 data/database
chmod 755 logs

echo "✅ Docker environment initialized!"
echo ""
echo "📋 Next steps:"
echo "1. Ensure your .env file is configured"
echo "2. Run: docker-compose up -d"
echo "3. Monitor: docker-compose logs -f crypto-trading"