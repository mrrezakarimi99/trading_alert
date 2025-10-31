"""
Database storage service for cryptocurrency trading data.
Handles SQLite database operations for historical data, trades, and predictions.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd

from ..models.models import PriceData, TradingSignal, Trade, Prediction, BacktestResult

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQLite database service for storing trading data."""
    
    def __init__(self, db_path: str = "data/database/trading.db"):
        """Initialize database service."""
        self.db_path = Path(db_path)
        
        # Try to create directory, with better error handling
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error(f"Permission denied creating database directory: {e}")
            # Try alternative location in user's home directory
            import os
            alt_path = Path.home() / ".crypto_trading" / "database"
            alt_path.mkdir(parents=True, exist_ok=True)
            self.db_path = alt_path / "trading.db"
            logger.info(f"Using alternative database location: {self.db_path}")
        except Exception as e:
            logger.error(f"Error creating database directory: {e}")
            raise
            
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Price data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        price REAL NOT NULL,
                        volume REAL,
                        market_cap REAL,
                        price_change_24h REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(asset_id, timestamp)
                    )
                """)
                
                # Trading signals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trading_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        asset_symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        price REAL NOT NULL,
                        reason TEXT,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        price REAL NOT NULL,
                        total_value REAL NOT NULL,
                        fee REAL DEFAULT 0,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Predictions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        predicted_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        price_change REAL NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp DATETIME NOT NULL,
                        actual_price REAL,
                        accuracy REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Backtest results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        start_date DATETIME NOT NULL,
                        end_date DATETIME NOT NULL,
                        initial_balance REAL NOT NULL,
                        final_balance REAL NOT NULL,
                        total_return REAL NOT NULL,
                        win_rate REAL NOT NULL,
                        total_trades INTEGER NOT NULL,
                        max_drawdown REAL NOT NULL,
                        sharpe_ratio REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_data_asset_time ON price_data(asset_id, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_asset_time ON trading_signals(asset_id, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_asset_time ON trades(asset_id, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_asset_time ON predictions(asset_id, timestamp)")
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_price_data(self, asset_id: str, price_data: List[PriceData]) -> bool:
        """Save price data to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for data in price_data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO price_data 
                        (asset_id, timestamp, price, volume)
                        VALUES (?, ?, ?, ?)
                    """, (asset_id, data.timestamp, data.price, data.volume))
                
                conn.commit()
                logger.info(f"Saved {len(price_data)} price records for {asset_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save price data: {e}")
            return False
    
    def get_price_data(self, asset_id: str, days: int = 30) -> List[PriceData]:
        """Get price data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT timestamp, price, volume
                    FROM price_data
                    WHERE asset_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (asset_id, days))
                
                rows = cursor.fetchall()
                price_data = []
                
                for row in rows:
                    price_data.append(PriceData(
                        timestamp=datetime.fromisoformat(row[0]),
                        price=row[1],
                        volume=row[2] or 0
                    ))
                
                return price_data
                
        except Exception as e:
            logger.error(f"Failed to get price data: {e}")
            return []
    
    def save_trading_signal(self, signal: TradingSignal) -> bool:
        """Save trading signal to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO trading_signals 
                    (asset_id, asset_symbol, action, confidence, price, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal.asset_id, signal.asset_symbol, signal.action,
                    signal.confidence, signal.price, signal.reason, signal.timestamp
                ))
                
                conn.commit()
                logger.info(f"Saved trading signal: {signal.action} for {signal.asset_symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save trading signal: {e}")
            return False
    
    def save_prediction(self, prediction: Prediction) -> bool:
        """Save prediction to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO predictions 
                    (asset_id, predicted_price, current_price, price_change, confidence, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    prediction.asset_id, prediction.predicted_price, prediction.current_price,
                    prediction.price_change, prediction.confidence, prediction.timestamp
                ))
                
                conn.commit()
                logger.info(f"Saved prediction for {prediction.asset_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            return False
    
    def save_trade(self, trade: Trade) -> bool:
        """Save trade to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO trades 
                    (asset_id, action, quantity, price, total_value, fee, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.asset_id, trade.action, trade.quantity,
                    trade.price, trade.total_value, trade.fee, trade.timestamp
                ))
                
                conn.commit()
                logger.info(f"Saved trade: {trade.action} {trade.quantity} {trade.asset_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
            return False
    
    def get_trading_history(self, asset_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get trading history from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if asset_id:
                    cursor.execute("""
                        SELECT asset_id, action, quantity, price, total_value, timestamp
                        FROM trades
                        WHERE asset_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (asset_id, days))
                else:
                    cursor.execute("""
                        SELECT asset_id, action, quantity, price, total_value, timestamp
                        FROM trades
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (days,))
                
                rows = cursor.fetchall()
                return [
                    {
                        'asset_id': row[0],
                        'action': row[1],
                        'quantity': row[2],
                        'price': row[3],
                        'total_value': row[4],
                        'timestamp': row[5]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get trading history: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                tables = ['price_data', 'trading_signals', 'trades', 'predictions', 'backtest_results']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}