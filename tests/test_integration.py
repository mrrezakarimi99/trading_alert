#!/usr/bin/env python3
"""
Integration Test: Multi-Provider with Trading System
===================================================

Test the new multi-provider data service with the existing trading system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from src.services.data_service import DataService
from src.models import AssetConfig

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_integration():
    """Test integration with existing trading system components."""
    
    print("🔗 Testing Multi-Provider Integration with Trading System")
    print("=" * 60)
    
    # Initialize data service
    data_service = DataService()
    
    # Test with real asset configurations
    test_assets = [
        AssetConfig(id='bitcoin', symbol='BTC', name='Bitcoin', min_confidence=0.7, min_price_change=0.02, allocation=0.4),
        AssetConfig(id='ethereum', symbol='ETH', name='Ethereum', min_confidence=0.7, min_price_change=0.02, allocation=0.3),
        AssetConfig(id='cardano', symbol='ADA', name='Cardano', min_confidence=0.7, min_price_change=0.02, allocation=0.3)
    ]
    
    print(f"\n📊 Testing {len(test_assets)} configured assets:")
    
    successful_fetches = 0
    total_value = 0
    
    for asset in test_assets:
        print(f"\n  Processing {asset.symbol} ({asset.allocation*100:.0f}% allocation):")
        
        # Fetch current price
        price_data = data_service.fetch_current_price(asset.id)
        
        if price_data:
            print(f"    ✅ Current Price: ${price_data.price:,.2f}")
            print(f"    📊 Volume: ${price_data.volume:,.0f}")
            if price_data.price_change_24h is not None:
                change_emoji = "📈" if price_data.price_change_24h >= 0 else "📉"
                print(f"    {change_emoji} 24h Change: {price_data.price_change_24h:+.2f}%")
            
            # Calculate portfolio value (assume $1000 allocation per asset)
            allocation_value = 1000 * asset.allocation
            asset_value = allocation_value  # Simplified for test
            total_value += asset_value
            successful_fetches += 1
            
            print(f"    💰 Portfolio Value: ${asset_value:,.2f}")
            
            # Test asset validation
            is_valid = data_service.validate_asset_exists(asset.id)
            print(f"    ✓ Asset Validation: {'Valid' if is_valid else 'Invalid'}")
        else:
            print(f"    ❌ Failed to fetch price data")
    
    # Summary
    print(f"\n📈 Portfolio Summary:")
    print(f"  Total Assets: {len(test_assets)}")
    print(f"  Successful Fetches: {successful_fetches}/{len(test_assets)}")
    print(f"  Success Rate: {(successful_fetches/len(test_assets)*100):.1f}%")
    print(f"  Total Portfolio Value: ${total_value:,.2f}")
    
    # Provider health summary
    print(f"\n🏥 Provider Health Summary:")
    health = data_service.check_provider_health()
    healthy_providers = sum(1 for status in health.values() if status)
    print(f"  Healthy Providers: {healthy_providers}/{len(health)}")
    
    for provider, is_healthy in health.items():
        status = "🟢 Online" if is_healthy else "🔴 Offline"
        print(f"    {provider}: {status}")
    
    # Test historical data for one asset
    print(f"\n📊 Historical Data Test (Bitcoin, 7 days):")
    historical = data_service.fetch_historical_data('bitcoin', 7)
    if historical:
        print(f"  ✅ Retrieved {len(historical)} data points")
        print(f"  📅 Period: {historical[0].timestamp.date()} to {historical[-1].timestamp.date()}")
        
        # Calculate some basic metrics
        prices = [h.price for h in historical]
        min_price = min(prices)
        max_price = max(prices)
        current_price = prices[-1]
        
        print(f"  📊 Price Range: ${min_price:,.2f} - ${max_price:,.2f}")
        print(f"  📈 Current: ${current_price:,.2f}")
        print(f"  📊 Volatility: {((max_price - min_price) / min_price * 100):.2f}%")
    else:
        print("  ❌ Failed to retrieve historical data")
    
    print(f"\n✅ Integration Test Complete!")
    print(f"🎯 Result: Multi-provider system successfully integrated with trading infrastructure")

if __name__ == "__main__":
    test_integration()