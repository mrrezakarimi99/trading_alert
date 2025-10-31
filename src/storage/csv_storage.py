"""
CSV storage service for cryptocurrency trading data.
Provides CSV file operations for historical data backup and analysis.
"""

import csv
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd

from ..models.models import PriceData, TradingSignal, Trade, Prediction, BacktestResult

logger = logging.getLogger(__name__)


class CSVStorageService:
    """CSV storage service for trading data backup and analysis."""
    
    def __init__(self, csv_dir: str = "data/csv"):
        """Initialize CSV storage service."""
        self.csv_dir = Path(csv_dir)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CSV storage initialized at {self.csv_dir}")
    
    def save_price_data_csv(self, asset_id: str, price_data: List[PriceData]) -> bool:
        """Save price data to CSV file."""
        try:
            csv_file = self.csv_dir / f"{asset_id}_price_data.csv"
            
            # Convert to DataFrame for easier handling
            data = []
            for price in price_data:
                data.append({
                    'timestamp': price.timestamp.isoformat(),
                    'price': price.price,
                    'volume': price.volume or 0
                })
            
            df = pd.DataFrame(data)
            
            # If file exists, append new data
            if csv_file.exists():
                existing_df = pd.read_csv(csv_file)
                df = pd.concat([existing_df, df]).drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved {len(price_data)} price records to {csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save price data to CSV: {e}")
            return False
    
    def load_price_data_csv(self, asset_id: str) -> List[PriceData]:
        """Load price data from CSV file."""
        try:
            csv_file = self.csv_dir / f"{asset_id}_price_data.csv"
            
            if not csv_file.exists():
                logger.warning(f"CSV file not found: {csv_file}")
                return []
            
            df = pd.read_csv(csv_file)
            price_data = []
            
            for _, row in df.iterrows():
                price_data.append(PriceData(
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    price=float(row['price']),
                    volume=float(row.get('volume', 0))
                ))
            
            logger.info(f"Loaded {len(price_data)} price records from {csv_file}")
            return price_data
            
        except Exception as e:
            logger.error(f"Failed to load price data from CSV: {e}")
            return []
    
    def save_trading_signals_csv(self, signals: List[TradingSignal]) -> bool:
        """Save trading signals to CSV file."""
        try:
            csv_file = self.csv_dir / "trading_signals.csv"
            
            # Convert to DataFrame
            data = []
            for signal in signals:
                data.append({
                    'timestamp': signal.timestamp.isoformat(),
                    'asset_id': signal.asset_id,
                    'asset_symbol': signal.asset_symbol,
                    'action': signal.action,
                    'confidence': signal.confidence,
                    'price': signal.price,
                    'reason': signal.reason
                })
            
            df = pd.DataFrame(data)
            
            # If file exists, append new data
            if csv_file.exists():
                existing_df = pd.read_csv(csv_file)
                df = pd.concat([existing_df, df]).drop_duplicates().sort_values('timestamp')
            
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved {len(signals)} trading signals to {csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save trading signals to CSV: {e}")
            return False
    
    def save_trades_csv(self, trades: List[Trade]) -> bool:
        """Save trades to CSV file."""
        try:
            csv_file = self.csv_dir / "trades.csv"
            
            # Convert to DataFrame
            data = []
            for trade in trades:
                data.append({
                    'timestamp': trade.timestamp.isoformat(),
                    'asset_id': trade.asset_id,
                    'action': trade.action,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'total_value': trade.total_value,
                    'fee': trade.fee
                })
            
            df = pd.DataFrame(data)
            
            # If file exists, append new data
            if csv_file.exists():
                existing_df = pd.read_csv(csv_file)
                df = pd.concat([existing_df, df]).drop_duplicates().sort_values('timestamp')
            
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved {len(trades)} trades to {csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save trades to CSV: {e}")
            return False
    
    def save_predictions_csv(self, predictions: List[Prediction]) -> bool:
        """Save predictions to CSV file."""
        try:
            csv_file = self.csv_dir / "predictions.csv"
            
            # Convert to DataFrame
            data = []
            for pred in predictions:
                data.append({
                    'timestamp': pred.timestamp.isoformat(),
                    'asset_id': pred.asset_id,
                    'predicted_price': pred.predicted_price,
                    'current_price': pred.current_price,
                    'price_change': pred.price_change,
                    'confidence': pred.confidence
                })
            
            df = pd.DataFrame(data)
            
            # If file exists, append new data
            if csv_file.exists():
                existing_df = pd.read_csv(csv_file)
                df = pd.concat([existing_df, df]).drop_duplicates().sort_values('timestamp')
            
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved {len(predictions)} predictions to {csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save predictions to CSV: {e}")
            return False
    
    def save_backtest_results_csv(self, results: List[BacktestResult]) -> bool:
        """Save backtest results to CSV file."""
        try:
            csv_file = self.csv_dir / "backtest_results.csv"
            
            # Convert to DataFrame
            data = []
            for result in results:
                data.append({
                    'timestamp': datetime.now().isoformat(),
                    'asset_id': result.asset_id,
                    'start_date': result.start_date.isoformat(),
                    'end_date': result.end_date.isoformat(),
                    'initial_balance': result.initial_balance,
                    'final_balance': result.final_balance,
                    'total_return': result.total_return,
                    'win_rate': result.win_rate,
                    'total_trades': result.total_trades,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio
                })
            
            df = pd.DataFrame(data)
            
            # If file exists, append new data
            if csv_file.exists():
                existing_df = pd.read_csv(csv_file)
                df = pd.concat([existing_df, df]).sort_values('timestamp')
            
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved {len(results)} backtest results to {csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save backtest results to CSV: {e}")
            return False
    
    def export_portfolio_performance(self, asset_id: str = None) -> bool:
        """Export portfolio performance data to CSV."""
        try:
            # Combine data from various sources for analysis
            trades_file = self.csv_dir / "trades.csv"
            signals_file = self.csv_dir / "trading_signals.csv"
            
            if not trades_file.exists() or not signals_file.exists():
                logger.warning("Required CSV files not found for portfolio export")
                return False
            
            trades_df = pd.read_csv(trades_file)
            signals_df = pd.read_csv(signals_file)
            
            if asset_id:
                trades_df = trades_df[trades_df['asset_id'] == asset_id]
                signals_df = signals_df[signals_df['asset_id'] == asset_id]
                export_file = self.csv_dir / f"portfolio_performance_{asset_id}.csv"
            else:
                export_file = self.csv_dir / "portfolio_performance_all.csv"
            
            # Create performance summary
            performance_data = []
            
            # Group by asset
            for asset in trades_df['asset_id'].unique():
                asset_trades = trades_df[trades_df['asset_id'] == asset]
                asset_signals = signals_df[signals_df['asset_id'] == asset]
                
                buy_trades = asset_trades[asset_trades['action'] == 'BUY']
                sell_trades = asset_trades[asset_trades['action'] == 'SELL']
                
                performance_data.append({
                    'asset_id': asset,
                    'total_trades': len(asset_trades),
                    'buy_trades': len(buy_trades),
                    'sell_trades': len(sell_trades),
                    'total_signals': len(asset_signals),
                    'buy_signals': len(asset_signals[asset_signals['action'] == 'BUY']),
                    'sell_signals': len(asset_signals[asset_signals['action'] == 'SELL']),
                    'hold_signals': len(asset_signals[asset_signals['action'] == 'HOLD']),
                    'total_volume': asset_trades['total_value'].sum(),
                    'avg_trade_size': asset_trades['total_value'].mean() if len(asset_trades) > 0 else 0,
                    'last_trade_date': asset_trades['timestamp'].max() if len(asset_trades) > 0 else None
                })
            
            performance_df = pd.DataFrame(performance_data)
            performance_df.to_csv(export_file, index=False)
            
            logger.info(f"Exported portfolio performance to {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export portfolio performance: {e}")
            return False
    
    def get_csv_files_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about existing CSV files."""
        try:
            csv_info = {}
            
            for csv_file in self.csv_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    csv_info[csv_file.name] = {
                        'rows': len(df),
                        'columns': list(df.columns),
                        'size_mb': csv_file.stat().st_size / (1024 * 1024),
                        'last_modified': datetime.fromtimestamp(csv_file.stat().st_mtime)
                    }
                except Exception as file_error:
                    logger.warning(f"Could not read {csv_file}: {file_error}")
                    csv_info[csv_file.name] = {'error': str(file_error)}
            
            return csv_info
            
        except Exception as e:
            logger.error(f"Failed to get CSV files info: {e}")
            return {}
    
    def cleanup_old_files(self, days: int = 30) -> bool:
        """Clean up CSV files older than specified days."""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_files = []
            
            for csv_file in self.csv_dir.glob("*.csv"):
                if csv_file.stat().st_mtime < cutoff_date:
                    csv_file.unlink()
                    deleted_files.append(csv_file.name)
            
            if deleted_files:
                logger.info(f"Cleaned up {len(deleted_files)} old CSV files: {deleted_files}")
            else:
                logger.info("No old CSV files to clean up")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old CSV files: {e}")
            return False