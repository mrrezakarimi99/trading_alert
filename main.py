#!/usr/bin/env python3
"""
Cryptocurrency Trading System
============================

Professional multi-asset cryptocurrency trading and prediction system using LSTM neural networks.
Built with SOLID principles and clean architecture.

Author: AI Assistant
Version: 2.0.0
"""

import os
import sys
import argparse
import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import warnings

# Suppress warnings and configure TensorFlow for CPU-only
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'false'

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")

# Configure logging
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging handlers with error handling
handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler, fall back to console only if permission denied
try:
    file_handler = logging.FileHandler('logs/trading_system.log')
    handlers.append(file_handler)
except PermissionError:
    print("⚠️  Warning: Cannot write to log file, using console logging only")
except Exception as e:
    print(f"⚠️  Warning: Log file error ({e}), using console logging only")

# Configure logging
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Import services from new structure
from src.models import PriceData, Prediction, TradingSignal, BacktestResult
from src.services import AssetManagerService, DataService, ModelService, TradingService, TelegramService
from src.storage import DatabaseService, CSVStorageService


class CryptoTradingSystem:
    """Main cryptocurrency trading system orchestrator."""
    
    def __init__(self):
                # Initialize services with dependency injection
        self.asset_manager = AssetManagerService()
        self.data_service = DataService()
        self.model_service = ModelService(models_dir="src/ml_models")
        self.trading_service = TradingService()
        self.telegram_service = TelegramService()
        
        # Initialize storage services
        self.db_service = DatabaseService()
        self.csv_service = CSVStorageService()
        
        # Configuration
        self.portfolio_size = float(os.getenv('PORTFOLIO_SIZE', '10000.0'))
        self.max_risk_per_trade = float(os.getenv('MAX_RISK_PER_TRADE', '0.02'))
        self.fetch_interval = int(os.getenv('FETCH_INTERVAL', '300'))  # 5 minutes
        self.signal_cooldown = int(os.getenv('SIGNAL_COOLDOWN', '60'))  # 1 hour
        
        # Setup directories
        self._setup_directories()
        
        logger.info("🚀 Crypto Trading System initialized")
        logger.info(f"Portfolio Size: ${self.portfolio_size:,.2f}")
        logger.info(f"Risk per Trade: {self.max_risk_per_trade*100:.1f}%")
        logger.info(f"Assets: {', '.join(self.asset_manager.get_asset_ids())}")
    
    def _setup_directories(self):
        """Setup required directories."""
        directories = ["src/ml_models", "logs", "data/csv", "data/database"]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def fetch_data(self, asset_id: Optional[str] = None, days: int = 30) -> bool:
        """Fetch historical data for training."""
        logger.info(f"📈 Fetching {days} days of historical data...")
        
        assets = [asset_id] if asset_id and self.asset_manager.validate_asset(asset_id) else self.asset_manager.get_asset_ids()
        
        success_count = 0
        for asset_id in assets:
            logger.info(f"Fetching data for {asset_id}...")
            
            data = await asyncio.to_thread(self.data_service.fetch_historical_data, asset_id, days)
            if data:
                logger.info(f"✅ Fetched {len(data)} records for {asset_id}")
                
                # Save to database
                db_success = self.db_service.save_price_data(asset_id, data)
                if db_success:
                    logger.info(f"💾 Saved {len(data)} records to database for {asset_id}")
                
                # Save to CSV
                csv_success = self.csv_service.save_price_data_csv(asset_id, data)
                if csv_success:
                    logger.info(f"📄 Saved {len(data)} records to CSV for {asset_id}")
                
                success_count += 1
            else:
                logger.warning(f"❌ Failed to fetch data for {asset_id}")
        
        logger.info(f"✅ Data fetching completed: {success_count}/{len(assets)} assets")
        return success_count > 0
    
    async def train_models(self, asset_id: Optional[str] = None, days: int = 365) -> bool:
        """Train ML models for assets."""
        logger.info(f"🧠 Training models with {days} days of data...")
        
        assets = [asset_id] if asset_id and self.asset_manager.validate_asset(asset_id) else self.asset_manager.get_asset_ids()
        
        success_count = 0
        for asset_id in assets:
            logger.info(f"Training model for {asset_id}...")
            
            # Fetch training data
            data = await asyncio.to_thread(self.data_service.fetch_historical_data, asset_id, days)
            if not data or len(data) < 100:
                logger.warning(f"Insufficient data for training {asset_id}")
                continue
            
            # Train model
            if self.model_service.train_model(asset_id, data):
                metrics = self.model_service.get_model_metrics(asset_id)
                if metrics:
                    logger.info(f"✅ Model trained for {asset_id} - Accuracy: {metrics.accuracy:.2f}%")
                    success_count += 1
                    
                    # Send training completion alert
                    if self.telegram_service.is_enabled():
                        message = f"🧠 Model Training Complete!\n\n"
                        message += f"Asset: {asset_id.upper()}\n"
                        message += f"Accuracy: {metrics.accuracy:.2f}%\n"
                        message += f"RMSE: {getattr(metrics, 'rmse', 'N/A')}\n"
                        message += f"Training Data: {len(data)} records\n"
                        message += f"Status: Ready for trading 🚀"
                        try:
                            await self.telegram_service.send_message(message)
                            logger.info(f"📱 Sent training completion alert for {asset_id}")
                        except Exception as e:
                            logger.error(f"Failed to send training alert: {e}")
                else:
                    logger.warning(f"Model trained for {asset_id} but no metrics available")
            else:
                logger.error(f"❌ Failed to train model for {asset_id}")
                
                # Send training failure alert
                if self.telegram_service.is_enabled():
                    message = f"❌ Model Training Failed!\n\n"
                    message += f"Asset: {asset_id.upper()}\n"
                    message += f"Data Points: {len(data)}\n"
                    message += f"Please check logs for details."
                    try:
                        await self.telegram_service.send_message(message)
                    except Exception as e:
                        logger.error(f"Failed to send training failure alert: {e}")
        
        logger.info(f"✅ Model training completed: {success_count}/{len(assets)} assets")
        return success_count > 0
    
    async def validate_models(self, asset_id: Optional[str] = None, days: int = 30) -> bool:
        """Validate ML models performance."""
        logger.info("🔍 Starting model validation...")
        
        assets = [asset_id] if asset_id and self.asset_manager.validate_asset(asset_id) else self.asset_manager.get_asset_ids()
        
        validation_results = {}
        for asset_id in assets:
            if not self.model_service.model_exists(asset_id):
                logger.warning(f"No model found for {asset_id}")
                continue
            
            # Get test data
            test_data = await asyncio.to_thread(self.data_service.fetch_historical_data, asset_id, days)
            if not test_data:
                logger.warning(f"No test data available for {asset_id}")
                continue
            
            # Validate model
            results = self.model_service.validate_model(asset_id, test_data)
            if results:
                validation_results[asset_id] = results
                logger.info(f"✅ {asset_id} - Accuracy: {results['accuracy']:.2f}%, RMSE: {results['rmse']:.2f}")
            else:
                logger.error(f"❌ Validation failed for {asset_id}")
        
        logger.info(f"✅ Model validation completed: {len(validation_results)} models validated")
        return len(validation_results) > 0
    
    async def run_backtest(self, asset_id: Optional[str] = None, days: int = 90) -> bool:
        """Run backtesting analysis."""
        logger.info(f"📊 Starting backtesting for {days} days...")
        
        assets = [asset_id] if asset_id and self.asset_manager.validate_asset(asset_id) else self.asset_manager.get_asset_ids()
        
        backtest_results = {}
        for asset_id in assets:
            asset_config = self.asset_manager.get_asset(asset_id)
            if not asset_config:
                continue
            
            logger.info(f"Backtesting {asset_id}...")
            
            # Get historical data
            historical_data = await asyncio.to_thread(self.data_service.fetch_historical_data, asset_id, days)
            if not historical_data or len(historical_data) < 60:
                logger.warning(f"Insufficient data for backtesting {asset_id}")
                continue
            
            # Try to auto-train model if none exists and we have enough data
            if len(historical_data) >= 100:
                await asyncio.to_thread(self.model_service.auto_train_model_if_needed, asset_id, historical_data)
            
            # Generate predictions for backtest period
            predictions = []
            for i in range(60, len(historical_data)):
                recent_prices = [data.price for data in historical_data[i-60:i]]
                prediction = self.model_service.predict_price(asset_id, recent_prices)
                if prediction:
                    predictions.append(prediction)
            
            if not predictions:
                logger.warning(f"No predictions generated for {asset_id}")
                continue
            
            # Run backtest
            backtest_data = historical_data[60:]  # Match predictions
            result = self.trading_service.backtest_strategy(asset_config, backtest_data, predictions)
            
            if result.total_trades > 0:
                backtest_results[asset_id] = result
                logger.info(f"✅ {asset_id} - Return: {result.total_return:.2f}%, Trades: {result.total_trades}, Win Rate: {result.win_rate:.1f}%")
                
                # Send backtest results via Telegram
                if self.telegram_service.is_enabled():
                    await self.telegram_service.send_backtest_results(asset_config.symbol, result)
            else:
                logger.warning(f"No trades generated in backtest for {asset_id}")
        
        logger.info(f"✅ Backtesting completed: {len(backtest_results)} assets analyzed")
        return len(backtest_results) > 0
    
    async def run_live_trading(self, asset_id: Optional[str] = None) -> bool:
        """Run live trading system."""
        logger.info("🚀 Starting live trading system...")
        
        if asset_id:
            if not self.asset_manager.validate_asset(asset_id):
                logger.error(f"Invalid asset: {asset_id}")
                return False
            assets = [asset_id]
            logger.info(f"Trading single asset: {asset_id}")
        else:
            assets = self.asset_manager.get_asset_ids()
            logger.info(f"Trading multiple assets: {assets}")
        
        # Verify models exist
        missing_models = []
        for asset_id in assets:
            if not self.model_service.model_exists(asset_id):
                missing_models.append(asset_id)
        
        if missing_models:
            logger.error(f"Missing models for: {missing_models}")
            logger.info("Run training first: python main.py --train")
            return False
        
        # Send startup notification
        status_message = f"""
🚀 <b>Trading System Started</b>

<b>Assets:</b> {', '.join([self.asset_manager.get_asset_symbol(a) for a in assets])}
<b>Portfolio:</b> ${self.portfolio_size:,.2f}
<b>Risk per Trade:</b> {self.max_risk_per_trade*100:.1f}%
<b>Fetch Interval:</b> {self.fetch_interval//60} minutes
        """.strip()
        
        await self.telegram_service.send_message(status_message)
        
        try:
            while True:
                logger.info("🔄 Running trading cycle...")
                
                for asset_id in assets:
                    await self._process_asset(asset_id)
                
                logger.info(f"� Waiting {self.fetch_interval} seconds...")
                await asyncio.sleep(self.fetch_interval)
                
        except KeyboardInterrupt:
            logger.info("👋 Trading system stopped by user")
            await self.telegram_service.send_message("🛑 Trading system stopped by user")
            return True
        except Exception as e:
            logger.error(f"Trading system error: {e}")
            await self.telegram_service.send_error_alert("System Error", str(e))
            return False
    
    async def _process_asset(self, asset_id: str):
        """Process a single asset for trading signals."""
        try:
            asset_config = self.asset_manager.get_asset(asset_id)
            if not asset_config:
                return
            
            # Get current price
            current_price = await asyncio.to_thread(self.data_service.fetch_current_price, asset_id)
            if not current_price:
                logger.warning(f"Could not fetch current price for {asset_id}")
                return
            
            # Get recent historical data for prediction (configurable)
            history_days = int(os.getenv('PREDICTION_HISTORY_DAYS', '30'))  # Default 30 days for prediction
            historical_data = await asyncio.to_thread(self.data_service.fetch_historical_data, asset_id, history_days)
            if not historical_data or len(historical_data) < 20:  # Minimum 20 data points
                logger.warning(f"Insufficient historical data for {asset_id}: {len(historical_data) if historical_data else 0} points")
                return
            
            # Make prediction using available historical data
            prediction_window = min(60, len(historical_data))  # Use up to 60 recent prices
            recent_prices = [data.price for data in historical_data[-prediction_window:]]
            prediction = self.model_service.predict_price(asset_id, recent_prices)
            if not prediction:
                logger.warning(f"Could not generate prediction for {asset_id}")
                return
            
            # Generate trading signal
            signal = self.trading_service.generate_signal(asset_config, prediction, current_price)
            if not signal:
                return
            
            # Check if signal should be sent
            if not self.trading_service.should_send_signal(asset_id, signal, self.signal_cooldown):
                return
            
            # Save trading signal to database
            try:
                await asyncio.to_thread(self.database_service.save_trading_signal, signal)
                logger.debug(f"💾 Saved trading signal to database: {signal.action} for {asset_id}")
            except Exception as e:
                logger.error(f"Failed to save trading signal to database: {e}")
            
            # Save prediction to database
            try:
                await asyncio.to_thread(self.database_service.save_prediction, prediction)
                logger.debug(f"💾 Saved prediction to database for {asset_id}")
            except Exception as e:
                logger.error(f"Failed to save prediction to database: {e}")
            
            # Send signal if actionable
            if signal.action in ['BUY', 'SELL']:
                logger.info(f"🎯 {signal.action} signal for {asset_id}: {signal.reason}")
                await self.telegram_service.send_trading_signal(signal, prediction, current_price.price)
            else:
                logger.debug(f"HOLD signal for {asset_id}: {signal.reason}")
        
        except Exception as e:
            logger.error(f"Error processing {asset_id}: {e}")
    
    async def get_system_status(self) -> Dict:
        """Get current system status."""
        assets = self.asset_manager.get_asset_ids()
        model_status = {}
        data_status = {}
        
        for asset_id in assets:
            model_status[asset_id] = self.model_service.model_exists(asset_id)
            
            # Test data availability
            try:
                current_price = await asyncio.to_thread(self.data_service.fetch_current_price, asset_id)
                data_status[asset_id] = current_price is not None
            except:
                data_status[asset_id] = False
        
        return {
            'assets': len(assets),
            'models_available': sum(model_status.values()),
            'data_available': sum(data_status.values()),
            'telegram_enabled': self.telegram_service.is_enabled(),
            'model_status': model_status,
            'data_status': data_status
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cryptocurrency Trading System v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Start live trading
  python main.py --asset bitcoin       # Trade specific asset
  python main.py --fetch-data          # Fetch historical data
  python main.py --train               # Train ML models
  python main.py --backtest            # Run backtesting
  python main.py --validate            # Validate models
  python main.py --status              # Show system status
        """
    )
    
    parser.add_argument("--asset", help="Specific asset (bitcoin, ethereum, etc.)")
    parser.add_argument("--fetch-data", action="store_true", help="Fetch historical data")
    parser.add_argument("--train", action="store_true", help="Train ML models")
    parser.add_argument("--backtest", action="store_true", help="Run backtesting")
    parser.add_argument("--validate", action="store_true", help="Validate models")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--days", type=int, default=30, help="Days for data/backtesting")
    
    args = parser.parse_args()
    
    print("🚀 Cryptocurrency Trading System v2.0")
    print("=" * 60)
    
    # Create trading system
    trading_system = CryptoTradingSystem()
    
    # Execute requested operation
    try:
        if args.fetch_data:
            success = await trading_system.fetch_data(args.asset, args.days)
        elif args.train:
            success = await trading_system.train_models(args.asset, args.days)
        elif args.backtest:
            success = await trading_system.run_backtest(args.asset, args.days)
        elif args.validate:
            success = await trading_system.validate_models(args.asset, args.days)
        elif args.status:
            status = await trading_system.get_system_status()
            print(f"\n📊 System Status:")
            print(f"Assets: {status['assets']}")
            print(f"Models Available: {status['models_available']}/{status['assets']}")
            print(f"Data Available: {status['data_available']}/{status['assets']}")
            print(f"Telegram: {'✅ Enabled' if status['telegram_enabled'] else '❌ Disabled'}")
            success = True
        else:
            success = await trading_system.run_live_trading(args.asset)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())