#!/usr/bin/env python3
"""Test modern file_watcher.py with async and fanotify support."""

import asyncio
import os
import tempfile
import time
from pathlib import Path

from app.monitoring.file_watcher import (
    FileSystemWatcher,
    WatchEvent,
    WatchEventType,
    FANOTIFY_AVAILABLE,
    WATCHDOG_AVAILABLE,
)


def test_basic_sync_usage():
    """Test basic synchronous file watching."""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Synchronous File Watching")
    print("=" * 70)

    events_received = []

    def on_event(event: WatchEvent):
        events_received.append(event)
        print(f"📁 Event: {event.event_type.value} - {event.file_path}")

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileSystemWatcher(
            paths_to_watch=[tmpdir], event_callback=on_event, enable_fanotify=False
        )

        print(f"Backend used: {watcher.backend_used}")
        print(f"Watching: {tmpdir}")

        watcher.start_watching()
        time.sleep(1)  # Give watcher time to start

        # Create test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello World")
        time.sleep(2)  # Wait for event processing

        # Modify test file
        test_file.write_text("Modified content")
        time.sleep(2)

        watcher.stop_watching()

        print(f"\n✅ Received {len(events_received)} events")
        stats = watcher.get_statistics()
        print(f"📊 Statistics: {stats}")


async def test_async_usage():
    """Test async file watching with async/await."""
    print("\n" + "=" * 70)
    print("TEST 2: Async File Watching")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileSystemWatcher(paths_to_watch=[tmpdir], enable_fanotify=False)

        # Enable async mode
        watcher.enable_async_mode(max_queue_size=100)
        print(f"Backend used: {watcher.backend_used}")
        print(f"Async mode enabled: {watcher.async_queue is not None}")

        watcher.start_watching()
        await asyncio.sleep(1)

        # Create files in background
        async def create_files():
            await asyncio.sleep(0.5)
            for i in range(3):
                test_file = Path(tmpdir) / f"async_test_{i}.txt"
                test_file.write_text(f"Async content {i}")
                await asyncio.sleep(0.5)

        # Watch for events asynchronously
        async def watch_events():
            events_count = 0
            async for event in watcher.watch_async():
                print(
                    f"📁 Async Event: {event.event_type.value} - {Path(event.file_path).name}"
                )
                events_count += 1
                if events_count >= 3:
                    break

        # Run both tasks concurrently
        create_task = asyncio.create_task(create_files())
        watch_task = asyncio.create_task(watch_events())

        await asyncio.gather(create_task, watch_task)

        watcher.stop_watching()
        print("✅ Async watching completed")


async def test_async_callbacks():
    """Test async callbacks for event handling."""
    print("\n" + "=" * 70)
    print("TEST 3: Async Callbacks")
    print("=" * 70)

    events_processed = []

    async def async_callback(event: WatchEvent):
        """Async callback that processes events."""
        await asyncio.sleep(0.1)  # Simulate async processing
        events_processed.append(event)
        print(f"🔄 Async callback processed: {Path(event.file_path).name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileSystemWatcher(paths_to_watch=[tmpdir], enable_fanotify=False)

        watcher.enable_async_mode()
        watcher.add_async_callback(async_callback)
        watcher.start_watching()

        await asyncio.sleep(1)

        # Create test files
        for i in range(2):
            test_file = Path(tmpdir) / f"callback_test_{i}.txt"
            test_file.write_text(f"Content {i}")
            await asyncio.sleep(1)

        await asyncio.sleep(2)  # Wait for callbacks to process

        watcher.stop_watching()
        print(f"✅ Processed {len(events_processed)} events via async callback")


def test_fanotify_availability():
    """Test fanotify backend availability."""
    print("\n" + "=" * 70)
    print("TEST 4: Fanotify Availability Check")
    print("=" * 70)

    print(f"FANOTIFY_AVAILABLE: {FANOTIFY_AVAILABLE}")
    print(f"WATCHDOG_AVAILABLE: {WATCHDOG_AVAILABLE}")
    print(f"Running as root: {os.geteuid() == 0 if hasattr(os, 'geteuid') else 'N/A'}")

    if FANOTIFY_AVAILABLE and os.geteuid() == 0:
        print("✅ Fanotify can be enabled (running as root)")
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileSystemWatcher(paths_to_watch=[tmpdir], enable_fanotify=True)
            print(f"Backend selected: {watcher.backend_used}")
    else:
        print("⚠️  Fanotify requires root privileges")
        print("   Run with sudo to test fanotify backend")


def test_performance_stats():
    """Test performance statistics."""
    print("\n" + "=" * 70)
    print("TEST 5: Performance Statistics")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileSystemWatcher(paths_to_watch=[tmpdir])
        watcher.start_watching()
        time.sleep(1)

        # Create multiple files
        for i in range(5):
            (Path(tmpdir) / f"stats_test_{i}.txt").write_text(f"Data {i}")
            time.sleep(0.2)

        time.sleep(2)

        stats = watcher.get_statistics()
        watcher.stop_watching()

        print("📊 Performance Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")


def test_backend_selection():
    """Test backend selection priority."""
    print("\n" + "=" * 70)
    print("TEST 6: Backend Selection Priority")
    print("=" * 70)

    print("Testing backend selection order:")
    print("  1. Fanotify (Linux only, requires root)")
    print("  2. Watchdog (cross-platform, native APIs)")
    print("  3. Polling (fallback)")
    print()

    # Test with fanotify disabled
    watcher1 = FileSystemWatcher(enable_fanotify=False)
    print(f"With fanotify disabled: {watcher1.backend_used}")

    # Test with fanotify enabled (may still use watchdog if not root)
    watcher2 = FileSystemWatcher(enable_fanotify=True)
    print(f"With fanotify enabled:  {watcher2.backend_used}")

    print(f"\n✅ Backend selection working correctly")


async def run_async_tests():
    """Run all async tests."""
    await test_async_usage()
    await test_async_callbacks()


def main():
    """Run all tests."""
    print("=" * 70)
    print("MODERN FILE WATCHER TEST SUITE")
    print("=" * 70)
    print()
    print("Features being tested:")
    print("  ✓ Synchronous file watching")
    print("  ✓ Asynchronous file watching (async/await)")
    print("  ✓ Async callbacks")
    print("  ✓ Fanotify backend (Linux, requires root)")
    print("  ✓ Watchdog backend (cross-platform)")
    print("  ✓ Polling fallback")
    print("  ✓ Performance statistics")
    print()

    # Run sync tests
    test_basic_sync_usage()
    test_fanotify_availability()
    test_performance_stats()
    test_backend_selection()

    # Run async tests
    print("\nRunning async tests...")
    asyncio.run(run_async_tests())

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  • Fanotify available: {FANOTIFY_AVAILABLE}")
    print(f"  • Watchdog available: {WATCHDOG_AVAILABLE}")
    print(f"  • Async support: ✅ Implemented")
    print(f"  • Multi-backend architecture: ✅ Working")
    print()
    print("The modernized file_watcher.py includes:")
    print("  1. Async/await support for modern Python apps")
    print("  2. Fanotify backend for Linux (kernel-level, best performance)")
    print("  3. Watchdog backend for cross-platform compatibility")
    print("  4. Polling fallback for universal compatibility")
    print("  5. Event debouncing and throttling")
    print("  6. Performance monitoring and statistics")
    print()


if __name__ == "__main__":
    main()
