"""
Data Service (Multi-Provider Architecture)
==========================================

Service for fetching cryptocurrency price data using multi-provider architecture.
Implements data persistence, caching, and provider fallback mechanisms.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

from ..models import AssetConfig, PriceData
from .data_providers.multi_provider_service import MultiProviderDataService
from .data_providers.coingecko_provider import CoinGeckoProvider
from .data_providers.coincap_provider import CoinCapProvider
from .data_providers.binance_provider import BinanceProvider

logger = logging.getLogger(__name__)


class DataService:
    """Service for fetching and managing cryptocurrency data with multi-provider support."""
    
    def __init__(self):
        # Initialize multi-provider service with fallback chain
        self.providers = self._initialize_providers()
        self.multi_provider = MultiProviderDataService(self.providers)
        
        # Setup data directory
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"DataService initialized with {len(self.providers)} providers")
    
    def _initialize_providers(self) -> List:
        """Initialize data providers in order of preference."""
        providers = []
        api_key = os.getenv('COINGECKO_API_KEY')
        
        # # Primary: CoinCap (free, reliable, 200 req/min)
        # try:
        #     coincap = CoinCapProvider()
        #     providers.append(coincap)
        #     logger.info("✓ CoinCap provider initialized")
        # except Exception as e:
        #     logger.warning(f"✗ Failed to initialize CoinCap provider: {e}")
        
        # Secondary: Binance (free, highly reliable, 1200 req/min)
        try:
            binance = BinanceProvider()
            providers.append(binance)
            logger.info("✓ Binance provider initialized")
        except Exception as e:
            logger.warning(f"✗ Failed to initialize Binance provider: {e}")
        
        # Fallback: CoinGecko (may have rate limits)
        try:
            coingecko = CoinGeckoProvider(api_key)
            providers.append(coingecko)
            logger.info("✓ CoinGecko provider initialized")
        except Exception as e:
            logger.warning(f"✗ Failed to initialize CoinGecko provider: {e}")
        
        if not providers:
            raise ValueError("No data providers could be initialized")
        
        return providers
    
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """Fetch current price for an asset using multi-provider fallback."""
        try:
            price_data = self.multi_provider.fetch_current_price(asset_id)
            if price_data:
                logger.info(f"Fetched current price for {asset_id}: ${price_data.price:,.2f}")
            return price_data
        except Exception as e:
            logger.error(f"Failed to fetch current price for {asset_id}: {e}")
            return None
    
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """Fetch historical price data using multi-provider fallback."""
        try:
            # For single day, just get current price to avoid unnecessary API calls
            if days <= 1:
                current = self.fetch_current_price(asset_id)
                return [current] if current else None
            
            historical_data = self.multi_provider.fetch_historical_data(asset_id, days)
            if historical_data:
                logger.info(f"Fetched {len(historical_data)} historical records for {asset_id}")
            return historical_data
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {asset_id}: {e}")
            return None
    
    def fetch_multiple_prices(self, asset_ids: List[str]) -> Dict[str, Optional[PriceData]]:
        """Fetch current prices for multiple assets using multi-provider bulk fetching."""
        try:
            results = self.multi_provider.fetch_multiple_prices(asset_ids)
            successful_fetches = len([v for v in results.values() if v is not None])
            logger.info(f"Fetched prices for {successful_fetches}/{len(asset_ids)} assets")
            return results
        except Exception as e:
            logger.error(f"Failed to fetch multiple prices: {e}")
            return {}
    
    def validate_asset_exists(self, asset_id: str) -> bool:
        """Check if an asset exists using any available provider."""
        try:
            # Try to fetch current price - if successful, asset exists
            price_data = self.fetch_current_price(asset_id)
            return price_data is not None
        except Exception:
            return False
    
    def get_provider_statistics(self) -> Dict:
        """Get statistics about provider performance and health."""
        return {'providers': self.multi_provider.get_provider_stats()}
    
    def check_provider_health(self) -> Dict[str, bool]:
        """Check health status of all providers."""
        return self.multi_provider.health_check()
    
    def get_active_provider(self) -> Optional[str]:
        """Get the name of the currently active provider."""
        stats = self.get_provider_statistics()
        if stats['providers']:
            # Return the provider with the most recent successful request
            return max(stats['providers'].keys(), 
                      key=lambda p: stats['providers'][p]['successful_requests'])
        return None