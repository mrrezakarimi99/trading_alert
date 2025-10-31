#!/usr/bin/env python3
"""
Service Manager - Ensures proper service startup order
"""
import os
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_models_exist():
    """Check if trained models exist."""
    models_dir = Path("/app/src/ml_models")
    if not models_dir.exists():
        return False
    
    # Check for any .h5 model files
    model_files = list(models_dir.glob("*.h5"))
    return len(model_files) > 0

def check_data_exists():
    """Check if historical data exists."""
    csv_dir = Path("/app/data/csv")
    db_dir = Path("/app/data/database")
    
    # Check for CSV files
    csv_exists = csv_dir.exists() and any(csv_dir.glob("*.csv"))
    
    # Check for database
    db_exists = db_dir.exists() and any(db_dir.glob("*.db"))
    
    return csv_exists or db_exists

def wait_for_models(timeout=300):
    """Wait for models to be available."""
    logger.info("Waiting for trained models...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if check_models_exist():
            logger.info("✅ Models found!")
            return True
        
        logger.info("⏳ Models not ready, waiting...")
        time.sleep(10)
    
    logger.error("❌ Timeout waiting for models")
    return False

def wait_for_data(timeout=180):
    """Wait for data to be available."""
    logger.info("Waiting for historical data...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if check_data_exists():
            logger.info("✅ Data found!")
            return True
        
        logger.info("⏳ Data not ready, waiting...")
        time.sleep(10)
    
    logger.error("❌ Timeout waiting for data")
    return False

def main():
    service_mode = os.getenv('SERVICE_MODE', 'trade')
    
    logger.info(f"🚀 Starting service in {service_mode} mode")
    
    if service_mode == 'fetch':
        logger.info("📊 Data fetching mode - no dependencies needed")
        return True
    
    elif service_mode == 'train':
        logger.info("🧠 Training mode - checking for data...")
        if not wait_for_data():
            logger.error("Cannot start training without data")
            return False
        logger.info("✅ Training dependencies satisfied")
        return True
    
    elif service_mode == 'trade':
        logger.info("💹 Trading mode - checking for models...")
        if not wait_for_models():
            logger.error("Cannot start trading without trained models")
            logger.info("💡 Run data fetching and training first:")
            logger.info("   docker-compose up data-fetcher")
            logger.info("   docker-compose up trainer")
            return False
        logger.info("✅ Trading dependencies satisfied")
        return True
    
    elif service_mode == 'init':
        logger.info("🔧 Initialization mode - checking system status...")
        return True
    
    else:
        logger.info(f"Unknown service mode: {service_mode}")
        return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)