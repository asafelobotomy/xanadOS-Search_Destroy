#!/usr/bin/env python3
"""
Example: ML API Client Usage

Demonstrates using the MLScannerClient SDK to interact with the API.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.ml_client import MLScannerClient


def sync_example():
    """Synchronous client usage example."""
    print("\n" + "=" * 75)
    print("SYNCHRONOUS CLIENT EXAMPLE")
    print("=" * 75 + "\n")

    # Create client
    with MLScannerClient(base_url="http://localhost:8000") as client:

        # 1. Health check
        print("1. Health Check:")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   ML Enabled: {health['ml_enabled']}")
        print(f"   Model Version: {health.get('model_version', 'N/A')}")
        print()

        # 2. List models
        print("2. Available Models:")
        models = client.list_models()
        for model in models:
            print(f"   • {model.version} ({model.stage})")
            print(f"     Architecture: {model.architecture}")
            print(f"     Accuracy: {model.test_accuracy:.1%}")
        print()

        # 3. Scan test files
        print("3. Scanning Test Files:")

        # Scan benign samples
        benign_samples = list(Path("data/organized/test/benign").glob("*"))[:2]
        if benign_samples:
            print("\n   Benign Files:")
            for sample in benign_samples:
                try:
                    result = client.scan_file(sample)
                    print(f"   • {sample.name[:32]}...")
                    print(f"     Result: {'MALWARE' if result.is_malware else 'CLEAN'}")
                    print(f"     Confidence: {result.confidence:.1%}")
                    print(f"     Threat Level: {result.threat_level}")
                    print(f"     Scan Time: {result.scan_time_ms:.1f}ms")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

        # Scan malware samples
        malware_samples = list(Path("data/organized/test/malware").glob("*"))[:2]
        if malware_samples:
            print("\n   Malware Files:")
            for sample in malware_samples:
                try:
                    result = client.scan_file(sample)
                    print(f"   • {sample.name[:32]}...")
                    print(
                        f"     Result: {'MALWARE ⚠️' if result.is_malware else 'CLEAN'}"
                    )
                    print(f"     Confidence: {result.confidence:.1%}")
                    print(f"     Threat Level: {result.threat_level}")
                    print(f"     Scan Time: {result.scan_time_ms:.1f}ms")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

        print()


async def async_example():
    """Asynchronous client usage example."""
    print("\n" + "=" * 75)
    print("ASYNCHRONOUS CLIENT EXAMPLE")
    print("=" * 75 + "\n")

    # Create async client
    async with MLScannerClient(base_url="http://localhost:8000") as client:

        # 1. Health check
        print("1. Async Health Check:")
        health = await client.health_check_async()
        print(f"   Status: {health['status']}")
        print()

        # 2. Scan directory (concurrent)
        print("2. Async Directory Scan (concurrent):")

        test_dir = Path("data/organized/test/benign")
        if test_dir.exists():
            import time

            start = time.time()

            results = await client.scan_directory_async(test_dir, max_files=5)

            duration = time.time() - start

            print(f"   Scanned {len(results)} files in {duration:.2f}s")
            print(f"   Average: {duration/max(1, len(results)):.2f}s per file")

            malware_count = sum(1 for r in results if r.is_malware)
            print(f"   Malware detected: {malware_count}")
            print()


def main():
    """Run examples."""
    print(
        """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║        ML API Client Demo                                                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

This demo requires the ML API server to be running.

Start the server with:
    python examples/ml_api_server.py

Then run this client demo in another terminal.
    """
    )

    # Check if server is running
    try:
        client = MLScannerClient()
        client.health_check()
        client.close()
    except Exception as e:
        print(f"\n❌ Cannot connect to API server: {e}")
        print("\nPlease start the server first:")
        print("    python examples/ml_api_server.py\n")
        return

    # Run sync example
    try:
        sync_example()
    except Exception as e:
        print(f"\n❌ Sync example failed: {e}\n")

    # Run async example
    try:
        asyncio.run(async_example())
    except Exception as e:
        print(f"\n❌ Async example failed: {e}\n")

    print("\n" + "=" * 75)
    print("✅ Demo Complete!")
    print("=" * 75 + "\n")

    print("Next steps:")
    print("  • View API docs: http://localhost:8000/api/ml/docs")
    print("  • Try custom scans with your own files")
    print("  • Integrate SDK into your applications\n")


if __name__ == "__main__":
    main()
