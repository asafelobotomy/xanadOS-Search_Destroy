#!/usr/bin/env python3
"""Test the specific RKHunter optimization functions that are failing."""

import sys
import os
sys.path.insert(0, '/home/vm/Documents/xanadOS-Search_Destroy')

def test_optimization_directly():
    """Test optimization functions directly."""
    print("🔧 Testing RKHunter Optimization Functions...")

    try:
        from app.core.rkhunter_optimizer import RKHunterOptimizer

        # Initialize optimizer
        optimizer = RKHunterOptimizer()
        print("✅ RKHunter Optimizer initialized")

        # Test the specific optimization that's failing
        print("\n🚀 Running optimization...")
        result = optimizer.optimize_rkhunter()

        print(f"📊 Optimization result: {result}")

        if result:
            print("✅ Optimization completed successfully!")
        else:
            print("❌ Optimization failed")

        # Check what the specific errors were
        status = optimizer.get_optimization_status()
        print(f"\n📋 Current status: {status}")

    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimization_directly()
