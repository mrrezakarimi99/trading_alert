"""
CoinCap Data Provider
====================

Free, reliable cryptocurrency data provider.
API: https://docs.coincap.io/
Rate Limit: 200 requests/minute (no auth required)
"""

import requests
import logging
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from . import BaseDataProvider, DataProviderError, RateLimitError
from ...models import PriceData

logger = logging.getLogger(__name__)


class CoinCapProvider(BaseDataProvider):
    """CoinCap API data provider - free and reliable."""
    
    # Asset ID mapping from our system to CoinCap
    ASSET_MAPPING = {
        'bitcoin': 'bitcoin',
        'ethereum': 'ethereum',
        'cardano': 'cardano',
        'polkadot': 'polkadot',
        'chainlink': 'chainlink',
        'litecoin': 'litecoin',
        'stellar': 'stellar',
        'dogecoin': 'dogecoin'
    }
    
    def __init__(self):
        super().__init__(
            name="CoinCap",
            base_url="https://api.coincap.io/v2",
            rate_limit_delay=0.3  # 200 req/min = ~3.3 req/sec
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'CryptoTradingSystem/2.0'
        })
    
    def _get_coincap_id(self, asset_id: str) -> str:
        """Convert our asset ID to CoinCap asset ID."""
        return self.ASSET_MAPPING.get(asset_id, asset_id)
    
    def fetch_current_price(self, asset_id: str) -> Optional[PriceData]:
        """Fetch current price from CoinCap API."""
        try:
            coincap_id = self._get_coincap_id(asset_id)
            url = f"{self.base_url}/assets/{coincap_id}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                logger.warning(f"No data returned for {asset_id} from CoinCap")
                return None
            
            asset_data = data['data']
            
            price_data = PriceData(
                timestamp=datetime.now(),
                price=float(asset_data['priceUsd']),
                volume=float(asset_data.get('volumeUsd24Hr', 0)),
                market_cap=float(asset_data.get('marketCapUsd', 0))
            )
            
            logger.info(f"[CoinCap] Fetched {asset_id}: ${price_data.price:,.2f}")
            time.sleep(self.rate_limit_delay)
            return price_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[CoinCap] Network error fetching {asset_id}: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"[CoinCap] Data parsing error for {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[CoinCap] Unexpected error fetching {asset_id}: {e}")
            return None
    
    def fetch_historical_data(self, asset_id: str, days: int) -> Optional[List[PriceData]]:
        """Fetch historical data from CoinCap API."""
        try:
            coincap_id = self._get_coincap_id(asset_id)
            
            # CoinCap historical data endpoint
            url = f"{self.base_url}/assets/{coincap_id}/history"
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            params = {
                'interval': 'd1',  # Daily intervals
                'start': int(start_time.timestamp() * 1000),  # milliseconds
                'end': int(end_time.timestamp() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data or not data['data']:
                logger.warning(f"No historical data for {asset_id} from CoinCap")
                return None
            
            price_data_list = []
            for point in data['data']:
                price_data = PriceData(
                    timestamp=datetime.fromtimestamp(point['time'] / 1000),
                    price=float(point['priceUsd']),
                    volume=0  # CoinCap history endpoint doesn't include volume
                )
                price_data_list.append(price_data)
            
            logger.info(f"[CoinCap] Fetched {len(price_data_list)} historical records for {asset_id}")
            time.sleep(self.rate_limit_delay)
            return price_data_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[CoinCap] Network error fetching historical data for {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[CoinCap] Error fetching historical data for {asset_id}: {e}")
            return None
    
    def fetch_multiple_prices(self, asset_ids: List[str]) -> Dict[str, Optional[PriceData]]:
        """Fetch multiple prices efficiently using CoinCap's bulk endpoint."""
        try:
            # Convert to CoinCap IDs
            coincap_ids = [self._get_coincap_id(asset_id) for asset_id in asset_ids]
            ids_param = ','.join(coincap_ids)
            
            url = f"{self.base_url}/assets"
            params = {'ids': ids_param}
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                raise RateLimitError(self.name, "Rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            results = {}
            
            if 'data' in data and data['data']:
                # Create mapping from CoinCap ID back to our asset ID
                reverse_mapping = {v: k for k, v in self.ASSET_MAPPING.items()}
                
                for asset_data in data['data']:
                    coincap_id = asset_data['id']
                    our_asset_id = reverse_mapping.get(coincap_id, coincap_id)
                    
                    if our_asset_id in asset_ids:
                        price_data = PriceData(
                            timestamp=datetime.now(),
                            price=float(asset_data['priceUsd']),
                            volume=float(asset_data.get('volumeUsd24Hr', 0)),
                            market_cap=float(asset_data.get('marketCapUsd', 0))
                        )
                        results[our_asset_id] = price_data
            
            # Fill in None for assets not found
            for asset_id in asset_ids:
                if asset_id not in results:
                    results[asset_id] = None
            
            logger.info(f"[CoinCap] Fetched prices for {len([r for r in results.values() if r])} assets")
            time.sleep(self.rate_limit_delay)
            return results
            
        except Exception as e:
            logger.error(f"[CoinCap] Error fetching multiple prices: {e}")
            # Fallback to individual requests
            return super().fetch_multiple_prices(asset_ids)