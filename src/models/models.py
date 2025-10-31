"""
Domain Models
=============

Data structures and domain models for the cryptocurrency trading system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class AssetConfig:
    """Configuration for a cryptocurrency asset."""
    id: str
    symbol: str
    name: str
    min_confidence: float
    min_price_change: float
    allocation: float
    enabled: bool = True


@dataclass
class PriceData:
    """Cryptocurrency price data point."""
    timestamp: datetime
    price: float
    volume: float
    market_cap: Optional[float] = None
    price_change_24h: Optional[float] = None


@dataclass
class Prediction:
    """ML model prediction result."""
    asset_id: str
    predicted_price: float
    current_price: float
    price_change: float
    confidence: float
    timestamp: datetime


@dataclass
class TradingSignal:
    """Trading signal generated from predictions."""
    asset_id: str
    asset_symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    price: float
    reason: str
    timestamp: datetime


@dataclass
class Trade:
    """Individual trade record."""
    asset_id: str
    action: str  # BUY, SELL, SHORT, COVER, CLOSE
    price: float
    quantity: float
    timestamp: datetime
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None


@dataclass
class ModelMetrics:
    """ML model performance metrics."""
    asset_id: str
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    accuracy: float  # Percentage accuracy
    training_loss: float
    validation_loss: float
    trained_at: datetime


@dataclass
class BacktestResult:
    """Backtesting result summary."""
    asset_id: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_return: float
    total_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Trade]