"""
Multi-Provider Data Service
==========================

Composite data service that uses multiple providers with fallback.
Implements Strategy Pattern and Chain of Responsibility.
"""

import logging
from typing import List, Optional, Dict, Type
from datetime import datetime

from . import DataProvider, DataProviderError, RateLimitError, AuthenticationError
from .coincap_provider import CoinCapProvider
from .binance_provider import BinanceProvider
from ...models import PriceData

logger = logging.getLogger(__name__)


class MultiProviderDataService:
    """
    Multi-provider data service with automatic fallback.
    
    Uses multiple data providers in order of preference:
    1. CoinCap (free, reliable)
    2. Binance (free, very reliable)
    3. CoinGecko (fallback, might have rate limits)
    """
    
    def __init__(self, enable_coingecko: bool = True):
        """Initialize with available providers."""
        self.providers: List[DataProvider] = []
        self.provider_stats = {}
        
        # Initialize providers in order of preference
        # self._add_provider(CoinCapProvider())
        self._add_provider(BinanceProvider())
        
        # Optionally add CoinGecko as fallback
        if enable_coingecko:
            try:
                from .coingecko_provider import CoinGeckoProvider
                self._add_provider(CoinGeckoProvider())
            except ImportError:
                logger.warning("CoinGecko provider not available")
        
        logger.info(f"Initialized with {len(self.providers)} data providers: {[p.name for p in self.providers]}")
    
    def _add_provider(self, provider: DataProvider):
        """Add a provider and initialize its stats."""
        self.providers.append(provider)
        self.provider_stats[provider.name] = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'last_success': None,
            'last_failure': None
        }
    
    def _update_stats(self, provider_name: str, success: bool):
        """Update provider statistics."""
        stats = self.provider_stats.get(provider_name, {})
        stats['requests'] = stats.get('requests', 0) + 1
        
        if success:
            stats['successes'] = stats.get('successes', 0) + 1
            stats['last_success'] = datetime.now()
        else:
            stats['failures'] = stats.get('failures', 0) + 1
            stats['last_failure'] = datetime.now()
    
    def get_provider_stats(self) -> Dict[str, Dict]:
        """Get statistics for all providers."""
        return self.provider_stats.copy()
    
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """
        Fetch current price using first available provider.
        Tries providers in order until one succeeds.
        """
        last_error = None
        
        for provider in self.providers:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue
            
            try:
                logger.debug(f"Trying {provider.name} for {asset_id}")
                result = provider.fetch_current_price(asset_id)
                
                if result:
                    self._update_stats(provider.name, True)
                    logger.info(f"✅ {provider.name} provided price for {asset_id}: ${result.price:,.2f}")
                    return result
                else:
                    self._update_stats(provider.name, False)
                    logger.warning(f"❌ {provider.name} returned no data for {asset_id}")
                    
            except (RateLimitError, AuthenticationError) as e:
                self._update_stats(provider.name, False)
                logger.warning(f"❌ {provider.name} failed: {e}")
                last_error = e
                continue
                
            except Exception as e:
                self._update_stats(provider.name, False)
                logger.error(f"❌ {provider.name} error: {e}")
                last_error = e
                continue
        
        logger.error(f"All providers failed for {asset_id}. Last error: {last_error}")
        return None
    
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """
        Fetch historical data using first available provider.
        Tries providers in order until one succeeds.
        """
        last_error = None
        
        for provider in self.providers:
            if not provider.is_available:
                continue
            
            try:
                logger.debug(f"Trying {provider.name} for {asset_id} historical data ({days} days)")
                result = provider.fetch_historical_data(asset_id, days)
                
                if result and len(result) > 0:
                    self._update_stats(provider.name, True)
                    logger.info(f"✅ {provider.name} provided {len(result)} historical records for {asset_id}")
                    return result
                else:
                    self._update_stats(provider.name, False)
                    logger.warning(f"❌ {provider.name} returned no historical data for {asset_id}")
                    
            except (RateLimitError, AuthenticationError) as e:
                self._update_stats(provider.name, False)
                logger.warning(f"❌ {provider.name} failed: {e}")
                last_error = e
                continue
                
            except Exception as e:
                self._update_stats(provider.name, False)
                logger.error(f"❌ {provider.name} error: {e}")
                last_error = e
                continue
        
        logger.error(f"All providers failed for {asset_id} historical data. Last error: {last_error}")
        return None
    
    def fetch_multiple_prices(self, asset_ids: List[str]) -> Dict[str, Optional[PriceData]]:
        """
        Fetch multiple prices using the most efficient provider.
        Falls back to individual requests if bulk fails.
        """
        results = {}
        remaining_assets = asset_ids.copy()
        
        for provider in self.providers:
            if not provider.is_available or not remaining_assets:
                continue
            
            try:
                logger.debug(f"Trying {provider.name} for multiple prices: {remaining_assets}")
                provider_results = provider.fetch_multiple_prices(remaining_assets)
                
                # Collect successful results
                successful_assets = []
                for asset_id, price_data in provider_results.items():
                    if price_data:
                        results[asset_id] = price_data
                        successful_assets.append(asset_id)
                
                # Remove successful assets from remaining list
                remaining_assets = [a for a in remaining_assets if a not in successful_assets]
                
                if successful_assets:
                    self._update_stats(provider.name, True)
                    logger.info(f"✅ {provider.name} provided prices for {len(successful_assets)} assets")
                
                if not remaining_assets:
                    break  # All assets fetched successfully
                    
            except Exception as e:
                self._update_stats(provider.name, False)
                logger.error(f"❌ {provider.name} error for multiple prices: {e}")
                continue
        
        # Fill in None for any remaining assets
        for asset_id in remaining_assets:
            results[asset_id] = None
            logger.warning(f"Failed to fetch price for {asset_id} from all providers")
        
        return results
    
    def get_best_provider(self) -> Optional[DataProvider]:
        """Get the provider with the highest success rate."""
        best_provider = None
        best_success_rate = 0
        
        for provider in self.providers:
            if not provider.is_available:
                continue
                
            stats = self.provider_stats.get(provider.name, {})
            total_requests = stats.get('requests', 0)
            successes = stats.get('successes', 0)
            
            if total_requests > 0:
                success_rate = successes / total_requests
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_provider = provider
        
        return best_provider
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all providers."""
        health_status = {}
        
        for provider in self.providers:
            try:
                # Try a quick test with Bitcoin
                result = provider.fetch_current_price('bitcoin')
                health_status[provider.name] = result is not None
            except Exception:
                health_status[provider.name] = False
        
        return health_status