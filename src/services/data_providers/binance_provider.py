"""
Binance Public API Data Provider
================================

Free, highly reliable cryptocurrency data from Binance.
No authentication required for public market data.
Rate Limit: 1200 requests/minute (very generous)
"""

import requests
import logging
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from . import BaseDataProvider, DataProviderError, RateLimitError
from ...models import PriceData

logger = logging.getLogger(__name__)


class BinanceProvider(BaseDataProvider):
    """Binance public API data provider - free and very reliable."""
    
    # Symbol mapping from our system to Binance trading pairs
    SYMBOL_MAPPING = {
        'bitcoin': 'BTCUSDT',
        'ethereum': 'ETHUSDT', 
        'cardano': 'ADAUSDT',
        'polkadot': 'DOTUSDT',
        'chainlink': 'LINKUSDT',
        'litecoin': 'LTCUSDT',
        'stellar': 'XLMUSDT',
        'dogecoin': 'DOGEUSDT'
    }
    
    def __init__(self):
        super().__init__(
            name="Binance",
            base_url="https://api.binance.com/api/v3",
            rate_limit_delay=0.05  # 1200 req/min = 20 req/sec
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'CryptoTradingSystem/2.0'
        })
    
    def _get_binance_symbol(self, asset_id: str) -> str:
        """Convert our asset ID to Binance symbol."""
        return self.SYMBOL_MAPPING.get(asset_id, f"{asset_id.upper()}USDT")
    
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """Fetch current price from Binance API."""
        try:
            symbol = self._get_binance_symbol(asset_id)
            
            # Get 24hr ticker statistics (includes price, volume, change)
            url = f"{self.base_url}/ticker/24hr"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            price_data = PriceData(
                timestamp=datetime.now(),
                price=float(data['lastPrice']),
                volume=float(data['volume']),  # Base asset volume
                price_change_24h=float(data['priceChangePercent'])
            )
            
            logger.info(f"[Binance] Fetched {asset_id}: ${price_data.price:,.2f}")
            time.sleep(self.rate_limit_delay)
            return price_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Binance] Network error fetching {asset_id}: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"[Binance] Data parsing error for {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Binance] Unexpected error fetching {asset_id}: {e}")
            return None
    
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """Fetch historical kline/candlestick data from Binance."""
        try:
            symbol = self._get_binance_symbol(asset_id)
            
            # Binance klines endpoint
            url = f"{self.base_url}/klines"
            
            # Determine interval based on days requested
            if days <= 7:
                interval = '1h'  # Hourly for short periods
                limit = days * 24
            else:
                interval = '1d'  # Daily for longer periods
                limit = min(days, 1000)  # Binance limit is 1000
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"No historical data for {asset_id} from Binance")
                return None
            
            price_data_list = []
            for kline in data:
                # Binance kline format: [timestamp, open, high, low, close, volume, ...]
                price_data = PriceData(
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),  # Convert from ms
                    price=float(kline[4]),  # Close price
                    volume=float(kline[5])  # Volume
                )
                price_data_list.append(price_data)
            
            logger.info(f"[Binance] Fetched {len(price_data_list)} historical records for {asset_id}")
            time.sleep(self.rate_limit_delay)
            return price_data_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Binance] Network error fetching historical data for {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Binance] Error fetching historical data for {asset_id}: {e}")
            return None
    
    def fetch_multiple_prices(self, asset_ids: List[str]) -> Dict[str, Optional[PriceData]]:
        """Fetch multiple prices using Binance's ticker/price endpoint."""
        try:
            # Get all symbols for the assets
            symbols = [self._get_binance_symbol(asset_id) for asset_id in asset_ids]
            
            # Binance allows fetching all tickers at once
            url = f"{self.base_url}/ticker/24hr"
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            # Create mapping from symbol to asset_id
            symbol_to_asset = {self._get_binance_symbol(asset_id): asset_id for asset_id in asset_ids}
            
            results = {}
            
            # Find our symbols in the response
            for ticker in data:
                symbol = ticker['symbol']
                if symbol in symbol_to_asset:
                    asset_id = symbol_to_asset[symbol]
                    price_data = PriceData(
                        timestamp=datetime.now(),
                        price=float(ticker['lastPrice']),
                        volume=float(ticker['volume']),
                        price_change_24h=float(ticker['priceChangePercent'])
                    )
                    results[asset_id] = price_data
            
            # Fill in None for assets not found
            for asset_id in asset_ids:
                if asset_id not in results:
                    results[asset_id] = None
            
            logger.info(f"[Binance] Fetched prices for {len([r for r in results.values() if r])} assets")
            time.sleep(self.rate_limit_delay)
            return results
            
        except Exception as e:
            logger.error(f"[Binance] Error fetching multiple prices: {e}")
            # Fallback to individual requests
            return super().fetch_multiple_prices(asset_ids)