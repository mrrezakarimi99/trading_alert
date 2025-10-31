"""
Data Provider Protocol and Interfaces
=====================================

Defines the contract that all data providers must implement.
Enables Strategy Pattern for swappable data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Protocol
from datetime import datetime

from ...models import PriceData


class DataProvider(Protocol):
    """Protocol for all data providers."""
    
    @property
    def name(self) -> str:
        """Provider name for identification."""
        ...
    
    @property
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        ...
    
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """Fetch current price for an asset."""
        ...
    
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """Fetch historical price data."""
        ...
    
    def fetch_multiple_prices(self, asset_ids: List[str]) -> Dict[str, Optional[PriceData]]:
        """Fetch current prices for multiple assets."""
        ...


class BaseDataProvider(ABC):
    """Base class for all data providers with common functionality."""
    
    def __init__(self, name: str, base_url: str, rate_limit_delay: float = 1.0):
        self._name = name
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay
        self._available = True
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def _set_availability(self, available: bool):
        """Set provider availability status."""
        self._available = available
    
    @abstractmethod
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """Fetch current price for an asset."""
        pass
    
    @abstractmethod
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """Fetch historical price data."""
        pass
    
    def fetch_multiple_prices(self, asset_ids: List[str]) -> Dict[str, Optional[PriceData]]:
        """Default implementation for multiple price fetching."""
        results = {}
        for asset_id in asset_ids:
            results[asset_id] = self.fetch_current_price(asset_id)
        return results


class WebSocketDataProvider(Protocol):
    """Protocol for WebSocket-based real-time data providers."""
    
    async def connect(self) -> bool:
        """Connect to WebSocket."""
        ...
    
    async def disconnect(self) -> bool:
        """Disconnect from WebSocket."""
        ...
    
    async def subscribe_to_asset(self, asset_id: str) -> bool:
        """Subscribe to real-time updates for an asset."""
        ...
    
    async def get_real_time_data(self, asset_id: str) -> Optional[PriceData]:
        """Get latest real-time data."""
        ...


class DataProviderError(Exception):
    """Base exception for data provider errors."""
    
    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        self.message = message
        super().__init__(f"[{provider_name}] {message}")


class RateLimitError(DataProviderError):
    """Raised when provider rate limit is exceeded."""
    pass


class AuthenticationError(DataProviderError):
    """Raised when provider authentication fails."""
    pass


class DataUnavailableError(DataProviderError):
    """Raised when requested data is not available."""
    pass