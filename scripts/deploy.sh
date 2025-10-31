#!/bin/bash
# =============================================================================
# DEPLOYMENT AUTOMATION SCRIPT
# =============================================================================
# File: scripts/deploy.sh
# Usage: ./scripts/deploy.sh [production|staging|development]
# =============================================================================

set -e

# Configuration
ENVIRONMENT=${1:-development}
PROJECT_NAME="crypto-trading"
GITHUB_REPO="your-username/crypto-trading"  # Update this
DEPLOY_USER="ubuntu"
PYTHON_VERSION="3.9"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Environment-specific configurations
case $ENVIRONMENT in
    production)
        SERVER_HOST="your-production-server.com"
        DEPLOY_PATH="/opt/crypto-trading"
        BRANCH="main"
        ;;
    staging)
        SERVER_HOST="your-staging-server.com"
        DEPLOY_PATH="/opt/crypto-trading-staging"
        BRANCH="develop"
        ;;
    development)
        SERVER_HOST="localhost"
        DEPLOY_PATH="$(pwd)"
        BRANCH="develop"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        echo "Usage: $0 [production|staging|development]"
        exit 1
        ;;
esac

# Deployment functions
setup_environment() {
    log_info "Setting up environment: $ENVIRONMENT"
    
    if [ "$ENVIRONMENT" != "development" ]; then
        log_info "Connecting to server: $SERVER_HOST"
        ssh $DEPLOY_USER@$SERVER_HOST "mkdir -p $DEPLOY_PATH"
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    local install_cmd=""
    if [ "$ENVIRONMENT" != "development" ]; then
        install_cmd="ssh $DEPLOY_USER@$SERVER_HOST"
    fi
    
    $install_cmd bash -c "
        # Update system packages
        sudo apt-get update -y
        sudo apt-get install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev git curl
        
        # Install Docker (optional)
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $DEPLOY_USER
        fi
        
        # Install Docker Compose (optional)
        if ! command -v docker-compose &> /dev/null; then
            sudo curl -L \"https://github.com/docker/compose/releases/download/1.29.2/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    "
}

deploy_code() {
    log_info "Deploying code to $ENVIRONMENT..."
    
    if [ "$ENVIRONMENT" = "development" ]; then
        log_info "Development environment - using local code"
        return 0
    fi
    
    # Clone or update repository
    ssh $DEPLOY_USER@$SERVER_HOST "
        if [ -d '$DEPLOY_PATH/.git' ]; then
            cd $DEPLOY_PATH
            git fetch origin
            git checkout $BRANCH
            git pull origin $BRANCH
        else
            rm -rf $DEPLOY_PATH
            git clone -b $BRANCH https://github.com/$GITHUB_REPO.git $DEPLOY_PATH
        fi
    "
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    local setup_cmd=""
    if [ "$ENVIRONMENT" != "development" ]; then
        setup_cmd="ssh $DEPLOY_USER@$SERVER_HOST"
    fi
    
    $setup_cmd bash -c "
        cd $DEPLOY_PATH
        
        # Create virtual environment
        python$PYTHON_VERSION -m venv .venv
        
        # Activate and install dependencies
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Create necessary directories
        mkdir -p data/csv data/database logs
        
        # Set permissions
        chmod +x scripts/*.sh
    "
}

configure_environment() {
    log_info "Configuring environment variables..."
    
    local env_file="$DEPLOY_PATH/.env.$ENVIRONMENT"
    
    if [ "$ENVIRONMENT" != "development" ]; then
        log_warn "Please ensure $env_file exists on the server with proper configuration"
        ssh $DEPLOY_USER@$SERVER_HOST "
            cd $DEPLOY_PATH
            if [ ! -f .env.$ENVIRONMENT ]; then
                echo 'Creating template .env.$ENVIRONMENT file...'
                cp .env .env.$ENVIRONMENT
                echo 'Please edit .env.$ENVIRONMENT with production values'
            fi
            ln -sf .env.$ENVIRONMENT .env
        "
    else
        log_info "Using existing .env file for development"
    fi
}

install_service() {
    log_info "Installing system service..."
    
    if [ "$ENVIRONMENT" = "development" ]; then
        ./scripts/service-manager.sh install
    else
        ssh $DEPLOY_USER@$SERVER_HOST "
            cd $DEPLOY_PATH
            ./scripts/service-manager.sh install
        "
    fi
}

start_service() {
    log_info "Starting trading service..."
    
    if [ "$ENVIRONMENT" = "development" ]; then
        ./scripts/service-manager.sh start
    else
        ssh $DEPLOY_USER@$SERVER_HOST "
            cd $DEPLOY_PATH
            ./scripts/service-manager.sh start
        "
    fi
}

run_tests() {
    log_info "Running tests..."
    
    local test_cmd=""
    if [ "$ENVIRONMENT" != "development" ]; then
        test_cmd="ssh $DEPLOY_USER@$SERVER_HOST"
    fi
    
    $test_cmd bash -c "
        cd $DEPLOY_PATH
        source .venv/bin/activate
        python -m pytest tests/ -v
    "
}

health_check() {
    log_info "Performing health check..."
    
    sleep 10  # Wait for service to start
    
    if [ "$ENVIRONMENT" = "development" ]; then
        ./scripts/service-manager.sh status
    else
        ssh $DEPLOY_USER@$SERVER_HOST "
            cd $DEPLOY_PATH
            ./scripts/service-manager.sh status
        "
    fi
}

# Main deployment flow
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT"
    
    setup_environment
    
    if [ "$ENVIRONMENT" != "development" ]; then
        install_dependencies
        deploy_code
    fi
    
    setup_python_environment
    configure_environment
    
    # Run tests before deployment
    run_tests
    
    # Install and start service
    install_service
    start_service
    
    # Verify deployment
    health_check
    
    log_info "Deployment completed successfully!"
    log_info "Service management:"
    log_info "  Status: ./scripts/service-manager.sh status"
    log_info "  Logs:   ./scripts/service-manager.sh logs"
    log_info "  Stop:   ./scripts/service-manager.sh stop"
}

# Run main function
main