"""
CoinGecko Data Provider (Refactored)
===================================

Original CoinGecko provider refactored to fit the new provider pattern.
"""

import requests
import logging
import time
from typing import List, Optional, Dict
from datetime import datetime

from . import BaseDataProvider, DataProviderError, RateLimitError, AuthenticationError
from ...models import PriceData

logger = logging.getLogger(__name__)


class CoinGeckoProvider(BaseDataProvider):
    """CoinGecko API data provider (refactored for new architecture)."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="CoinGecko",
            base_url="https://api.coingecko.com/api/v3",
            rate_limit_delay=2.0  # Conservative rate limiting
        )
        self.api_key = api_key
        self.session = requests.Session()
        self.max_retries = 3
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'CryptoTradingSystem/2.0'
        }
        
        if api_key:
            headers['X-CG-API-KEY'] = api_key
            self.rate_limit_delay = 0.5  # Faster with API key
        
        self.session.headers.update(headers)
    
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """Fetch current price from CoinGecko API."""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': asset_id,
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true',
                'include_24hr_change': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 401:
                raise AuthenticationError(self.name, "API key invalid or unauthorized")
            elif response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            if asset_id not in data:
                return None
            
            asset_data = data[asset_id]
            
            price_data = PriceData(
                timestamp=datetime.now(),
                price=asset_data['usd'],
                volume=asset_data.get('usd_24h_vol', 0),
                market_cap=asset_data.get('usd_market_cap'),
                price_change_24h=asset_data.get('usd_24h_change', 0.0)
            )
            
            time.sleep(self.rate_limit_delay)
            return price_data
            
        except (AuthenticationError, RateLimitError):
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"[CoinGecko] Network error fetching {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[CoinGecko] Error fetching {asset_id}: {e}")
            return None
    
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """Fetch historical data from CoinGecko API."""
        try:
            url = f"{self.base_url}/coins/{asset_id}/market_chart"
            
            # Handle different day ranges for CoinGecko API
            if days <= 30:
                interval = 'hourly'
            elif days <= 90:
                interval = 'daily'
            else:
                interval = 'daily'
                logger.warning(f"Requesting {days} days - free API may limit this to ~365 days max")
            
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': interval
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                raise AuthenticationError(self.name, "API key invalid or unauthorized")
            elif response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            if 'prices' not in data or not data['prices']:
                return None
            
            price_data_list = []
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            
            for i, price_point in enumerate(prices):
                timestamp = datetime.fromtimestamp(price_point[0] / 1000)
                price = price_point[1]
                volume = volumes[i][1] if i < len(volumes) else 0
                
                price_data = PriceData(
                    timestamp=timestamp,
                    price=price,
                    volume=volume
                )
                price_data_list.append(price_data)
            
            time.sleep(self.rate_limit_delay)
            return price_data_list
            
        except (AuthenticationError, RateLimitError):
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"[CoinGecko] Network error fetching historical data for {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[CoinGecko] Error fetching historical data for {asset_id}: {e}")
            return None