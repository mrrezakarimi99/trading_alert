"""Main source package for the cryptocurrency trading system."""

from .services import (
    AssetManagerService,
    DataService,
    ModelService,
    TradingService,
    TelegramService
)

from .models import (
    AssetConfig,
    PriceData,
    Prediction,
    TradingSignal,
    BacktestResult,
    Trade,
    ModelMetrics
)

from .storage import (
    DatabaseService,
    CSVStorageService
)

__all__ = [
    # Services
    'AssetManagerService',
    'DataService',
    'ModelService',
    'TradingService',
    'TelegramService',
    # Models
    'AssetConfig',
    'PriceData',
    'Prediction',
    'TradingSignal',
    'BacktestResult',
    'Trade',
    'ModelMetrics',
    # Storage
    'DatabaseService',
    'CSVStorageService'
]