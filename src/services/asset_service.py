"""
Asset Manager Service
====================

Manages cryptocurrency asset configurations and portfolio allocation.
"""

import os
import logging
from typing import Dict, List, Optional

from ..models import AssetConfig

logger = logging.getLogger(__name__)


class AssetManagerService:
    """Service for managing cryptocurrency asset configurations."""
    
    SUPPORTED_ASSETS = {
        'bitcoin': {'symbol': 'BTC', 'name': 'Bitcoin'},
        'ethereum': {'symbol': 'ETH', 'name': 'Ethereum'},
        'cardano': {'symbol': 'ADA', 'name': 'Cardano'},
        'polkadot': {'symbol': 'DOT', 'name': 'Polkadot'},
        'chainlink': {'symbol': 'LINK', 'name': 'Chainlink'},
        'litecoin': {'symbol': 'LTC', 'name': 'Litecoin'},
        'stellar': {'symbol': 'XLM', 'name': 'Stellar'},
        'dogecoin': {'symbol': 'DOGE', 'name': 'Dogecoin'},
    }
    
    def __init__(self):
        self.assets: Dict[str, AssetConfig] = {}
        self.primary_asset: Optional[str] = None
        self._load_configuration()
    
    def _load_configuration(self):
        """Load asset configuration from environment variables."""
        try:
            # Load trading assets
            trading_assets = os.getenv('TRADING_ASSETS', 'bitcoin').split(',')
            trading_assets = [asset.strip() for asset in trading_assets]
            
            # Load primary asset
            self.primary_asset = os.getenv('PRIMARY_ASSET', 'bitcoin')
            
            # Create asset configurations
            for asset_id in trading_assets:
                if asset_id not in self.SUPPORTED_ASSETS:
                    logger.warning(f"Unsupported asset: {asset_id}")
                    continue
                
                asset_info = self.SUPPORTED_ASSETS[asset_id]
                asset_upper = asset_id.upper()
                
                self.assets[asset_id] = AssetConfig(
                    id=asset_id,
                    symbol=asset_info['symbol'],
                    name=asset_info['name'],
                    min_confidence=float(os.getenv(f'{asset_upper}_MIN_CONFIDENCE', '75.0')),
                    min_price_change=float(os.getenv(f'{asset_upper}_MIN_PRICE_CHANGE', '0.5')),
                    allocation=float(os.getenv(f'{asset_upper}_ALLOCATION', '1.0' if len(trading_assets) == 1 else '0.0'))
                )
            
            # Normalize allocations
            self._normalize_allocations()
            
            logger.info(f"Loaded {len(self.assets)} assets: {list(self.assets.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load asset configuration: {e}")
            self._create_fallback_config()
    
    def _normalize_allocations(self):
        """Normalize portfolio allocations to sum to 1.0."""
        if not self.assets:
            return
        
        total = sum(asset.allocation for asset in self.assets.values())
        if total == 0:
            # Equal allocation if none specified
            equal_allocation = 1.0 / len(self.assets)
            for asset in self.assets.values():
                asset.allocation = equal_allocation
        elif total != 1.0:
            # Normalize to sum to 1.0
            for asset in self.assets.values():
                asset.allocation /= total
    
    def _create_fallback_config(self):
        """Create fallback Bitcoin configuration."""
        self.assets = {
            'bitcoin': AssetConfig(
                id='bitcoin',
                symbol='BTC',
                name='Bitcoin',
                min_confidence=75.0,
                min_price_change=0.5,
                allocation=1.0
            )
        }
        self.primary_asset = 'bitcoin'
        logger.info("Created fallback Bitcoin configuration")
    
    def get_asset(self, asset_id: str) -> Optional[AssetConfig]:
        """Get asset configuration by ID."""
        return self.assets.get(asset_id)
    
    def get_all_assets(self) -> Dict[str, AssetConfig]:
        """Get all asset configurations."""
        return self.assets.copy()
    
    def get_enabled_assets(self) -> Dict[str, AssetConfig]:
        """Get enabled assets only."""
        return {k: v for k, v in self.assets.items() if v.enabled}
    
    def get_asset_ids(self) -> List[str]:
        """Get list of all asset IDs."""
        return list(self.assets.keys())
    
    def get_enabled_asset_ids(self) -> List[str]:
        """Get list of enabled asset IDs."""
        return [asset_id for asset_id, asset in self.assets.items() if asset.enabled]
    
    def validate_asset(self, asset_id: str) -> bool:
        """Check if asset is supported and enabled."""
        return asset_id in self.assets and self.assets[asset_id].enabled
    
    def calculate_position_size(self, asset_id: str, portfolio_value: float, risk_per_trade: float) -> float:
        """Calculate position size for an asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            return 0.0
        
        # Base position size
        base_position = portfolio_value * risk_per_trade
        
        # Apply asset allocation
        position_size = base_position * asset.allocation
        
        return position_size
    
    def get_portfolio_allocation(self, asset_id: str) -> float:
        """Get portfolio allocation for an asset."""
        asset = self.get_asset(asset_id)
        return asset.allocation if asset else 0.0
    
    def is_supported_asset(self, asset_id: str) -> bool:
        """Check if asset is in supported list."""
        return asset_id in self.SUPPORTED_ASSETS
    
    def get_asset_symbol(self, asset_id: str) -> Optional[str]:
        """Get asset symbol (e.g., BTC for bitcoin)."""
        asset = self.get_asset(asset_id)
        return asset.symbol if asset else None
    
    def get_asset_name(self, asset_id: str) -> Optional[str]:
        """Get asset full name."""
        asset = self.get_asset(asset_id)
        return asset.name if asset else None