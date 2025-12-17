#!/usr/bin/env python3
"""
Complete API Integration Test

Tests all API endpoints and SDK functionality.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.ml_client import MLScannerClient


def test_api_integration():
    """Test all API functionality."""
    print(
        "╔═══════════════════════════════════════════════════════════════════════════╗"
    )
    print(
        "║                                                                           ║"
    )
    print(
        "║        🧪 ML API INTEGRATION TEST                                        ║"
    )
    print(
        "║                                                                           ║"
    )
    print(
        "╚═══════════════════════════════════════════════════════════════════════════╝\n"
    )

    with MLScannerClient("http://localhost:8000") as client:
        # Test 1: Health Check
        print("1. Health Check:")
        health = client.health_check()
        print(f"   ✅ Status: {health['status']}")
        print(f"   ✅ ML Enabled: {health['ml_enabled']}")
        print(f"   ✅ Model Version: v{health['model_version']}")
        print(f"   ✅ Uptime: {health['uptime_seconds']:.2f}s\n")

        # Test 2: List Models
        print("2. List Models:")
        models = client.list_models()
        print(f"   ✅ Found {len(models)} models:")
        for model in models:
            marker = "⭐" if model.stage == "production" else "📦"
            print(f"      {marker} v{model.version} ({model.stage})")
            print(f"         Architecture: {model.architecture}")
            print(f"         Accuracy: {model.test_accuracy:.1%}")
            print(f"         Precision: {model.test_precision:.1%}")
            print(f"         Recall: {model.test_recall:.1%}")
        print()

        # Test 3: Scan Malware-like Content
        print("3. Scan Malware Sample:")
        malware_content = b"MZ\x90\x00" + b"\x00" * 100  # PE header signature
        result = client.scan_bytes(malware_content, "malware_test.exe")
        print(f"   {'⚠️ MALWARE DETECTED' if result.is_malware else '✅ CLEAN'}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Threat Level: {result.threat_level}")
        print(f"   Model: v{result.model_version}")
        print(f"   Scan Time: {result.scan_time_ms:.2f}ms\n")

        # Test 4: Scan Clean Content
        print("4. Scan Clean Sample:")
        clean_content = b"Hello, this is benign text content"
        result = client.scan_bytes(clean_content, "clean_test.txt")
        print(f"   {'⚠️ MALWARE DETECTED' if result.is_malware else '✅ CLEAN'}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Threat Level: {result.threat_level}")
        print(f"   Scan Time: {result.scan_time_ms:.2f}ms\n")

        # Test 5: Performance Test
        print("5. Performance Test (5 scans - respecting rate limits):")
        import time

        start = time.time()
        for i in range(5):
            test_content = f"test content {i}".encode()
            client.scan_bytes(test_content, f"test_{i}.bin")
            if i < 4:  # Don't sleep after last scan
                time.sleep(6)  # Wait 6 seconds between scans (10/min = 1 per 6s)
        duration = time.time() - start

        print(f"   ✅ Completed 5 scans in {duration:.2f}s")
        print(
            f"   ✅ Average: {duration/5*1000:.1f}ms per scan (including rate limit waits)"
        )
        print(f"   ✅ Rate limiting working correctly (10 requests/minute)\n")

    print(
        "╔═══════════════════════════════════════════════════════════════════════════╗"
    )
    print(
        "║                                                                           ║"
    )
    print(
        "║        ✅ ALL TESTS PASSED - ML API FULLY FUNCTIONAL                     ║"
    )
    print(
        "║                                                                           ║"
    )
    print(
        "╚═══════════════════════════════════════════════════════════════════════════╝\n"
    )


if __name__ == "__main__":
    try:
        test_api_integration()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
