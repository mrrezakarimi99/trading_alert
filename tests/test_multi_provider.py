#!/usr/bin/env python3
"""
Multi-Provider Data Service Test
===============================

Test script to verify the multi-provider data architecture is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime

from src.services.data_service import DataService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_multi_provider_service():
    """Test the multi-provider data service."""
    print("🚀 Testing Multi-Provider Data Service")
    print("=" * 50)
    
    # Initialize service
    data_service = DataService()
    
    # Test 1: Check provider health
    print("\n📊 Provider Health Check:")
    health = data_service.check_provider_health()
    for provider, is_healthy in health.items():
        status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
        print(f"  {provider}: {status}")
    
    # Test 2: Get provider statistics
    print("\n📈 Provider Statistics:")
    stats = data_service.get_provider_statistics()
    print(f"  Available providers: {len(stats['providers'])}")
    for provider, provider_stats in stats['providers'].items():
        print(f"  {provider}: {provider_stats.get('successful_requests', 0)} successful, "
              f"{provider_stats.get('failed_requests', 0)} failed")
    
    # Test 3: Fetch current price for Bitcoin
    print("\n💰 Testing Current Price Fetch:")
    test_assets = ['bitcoin', 'ethereum', 'cardano']
    
    for asset in test_assets:
        print(f"  Fetching {asset}...")
        price_data = data_service.fetch_current_price(asset)
        if price_data:
            print(f"    ✅ {asset}: ${price_data.price:,.2f} (Volume: ${price_data.volume:,.0f})")
        else:
            print(f"    ❌ Failed to fetch {asset}")
    
    # Test 4: Bulk price fetching
    print("\n🔄 Testing Bulk Price Fetch:")
    bulk_results = data_service.fetch_multiple_prices(test_assets)
    for asset, price_data in bulk_results.items():
        if price_data:
            print(f"  ✅ {asset}: ${price_data.price:,.2f}")
        else:
            print(f"  ❌ {asset}: Failed")
    
    # Test 5: Historical data (small sample)
    print("\n📈 Testing Historical Data (3 days):")
    historical = data_service.fetch_historical_data('bitcoin', 3)
    if historical:
        print(f"  ✅ Fetched {len(historical)} historical records")
        print(f"  Latest: ${historical[-1].price:,.2f} at {historical[-1].timestamp}")
        print(f"  Oldest: ${historical[0].price:,.2f} at {historical[0].timestamp}")
    else:
        print("  ❌ Failed to fetch historical data")
    
    # Test 6: Final statistics
    print("\n📊 Final Provider Statistics:")
    final_stats = data_service.get_provider_statistics()
    for provider, provider_stats in final_stats['providers'].items():
        success_rate = 0
        successful = provider_stats.get('successful_requests', 0)
        failed = provider_stats.get('failed_requests', 0)
        total = successful + failed
        if total > 0:
            success_rate = (successful / total) * 100
        print(f"  {provider}: {success_rate:.1f}% success rate "
              f"({successful}/{total} requests)")
    
    # Test 7: Active provider
    try:
        active = data_service.get_active_provider()
        print(f"\n🎯 Most Active Provider: {active}")
    except Exception as e:
        print(f"\n🎯 Most Active Provider: Error getting active provider - {e}")
    
    print("\n✅ Multi-Provider Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_multi_provider_service())