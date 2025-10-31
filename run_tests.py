#!/usr/bin/env python3
"""
Test Runner for Multi-Provider Architecture
==========================================

Run all tests for the multi-provider cryptocurrency trading system.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def run_test(test_file):
    """Run a specific test file."""
    test_path = project_root / "tests" / test_file
    if test_path.exists():
        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run([sys.executable, str(test_path)], 
                                  capture_output=False, 
                                  cwd=project_root)
            return result.returncode == 0
        except Exception as e:
            print(f"Error running {test_file}: {e}")
            return False
    else:
        print(f"Test file {test_file} not found")
        return False

def main():
    """Run all tests."""
    print("🚀 Multi-Provider Cryptocurrency Trading System - Test Suite")
    
    tests = [
        "test_multi_provider.py",
        "test_integration.py"
    ]
    
    results = {}
    
    for test in tests:
        success = run_test(test)
        results[test] = "✅ PASSED" if success else "❌ FAILED"
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test, result in results.items():
        print(f"{test}: {result}")
    
    total_tests = len(tests)
    passed_tests = sum(1 for result in results.values() if "PASSED" in result)
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())