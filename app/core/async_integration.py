#!/usr/bin/env python3
"""
Async Integration Module for xanadOS Search & Destroy
Demonstrates integration of async file watcher, threat detector, and scanner engine.
"""

import asyncio
import logging
import types
from typing import Any

from app.core.async_file_watcher import AsyncFileSystemWatcher
from app.core.async_scanner_engine import (
    AsyncScannerEngine,
    ScanConfiguration,
    ScanType,
    create_full_scan_config,
    create_quick_scan_config,
)
from app.core.async_threat_detector import AsyncThreatDetector


async def _create_test_file_async(file_path: str, content: str) -> None:
    """Create a test file asynchronously."""
    import aiofiles
    async with aiofiles.open(file_path, 'w') as f:
        await f.write(content)


async def _cleanup_directory_async(directory_path: str) -> None:
    """Clean up a directory and all its contents asynchronously."""
    import aiofiles.os
    from pathlib import Path

    try:
        path = Path(directory_path)
        if path.exists():
            # Remove all files first
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    await aiofiles.os.unlink(file_path)

            # Remove directories (bottom-up)
            for dir_path in reversed(list(path.rglob('*'))):
                if dir_path.is_dir():
                    await aiofiles.os.rmdir(dir_path)

            # Remove the root directory
            await aiofiles.os.rmdir(directory_path)
    except OSError as e:
        # Log but don't raise - cleanup is best effort
        logging.getLogger(__name__).warning("Error during async cleanup: %s", e)


class AsyncXanadOSCore:
    """
    Integrated async core for xanadOS Search & Destroy.

    Coordinates async file monitoring, threat detection, and scanning operations.
    """

    def __init__(self) -> None:
        """Initialize the async core system."""
        self.logger = logging.getLogger(__name__)

        # Initialize async components
        self.threat_detector = AsyncThreatDetector(
            max_workers=20,
            enable_heuristics=True,
            enable_behavioral=True
        )

        self.file_watcher = AsyncFileSystemWatcher(
            paths_to_watch=[],
            event_callback=None,
            max_workers=10,
            poll_interval=1.0
        )

        self.scanner_engine = AsyncScannerEngine(
            threat_detector=self.threat_detector,
            file_watcher=self.file_watcher,
            max_concurrent_scans=3,
            default_max_workers=30
        )

        self.is_initialized = False
        self.logger.info("Async xanadOS core initialized")

    async def __aenter__(self) -> "AsyncXanadOSCore":
        """Async context manager entry."""
        if not self.is_initialized:
            await self.initialize_async()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        """Async context manager exit with cleanup."""
        await self.shutdown_async()

    async def shutdown_async(self) -> None:
        """Shutdown all async components gracefully."""
        try:
            self.logger.info("Starting async xanadOS core shutdown...")

            # Disable real-time protection first
            if hasattr(self, 'real_time_enabled') and getattr(self, 'real_time_enabled', False):
                await self.disable_real_time_protection_async()

            # Clean up components in reverse order
            if hasattr(self.scanner_engine, 'cleanup_async'):
                await self.scanner_engine.cleanup_async()

            if hasattr(self.threat_detector, 'cleanup_async'):
                await self.threat_detector.cleanup_async()

            if hasattr(self.file_watcher, 'cleanup_async'):
                await self.file_watcher.cleanup_async()

            self.is_initialized = False

            self.logger.info("Async xanadOS core shutdown completed")

        except (RuntimeError, OSError, asyncio.CancelledError) as e:
            self.logger.error("Error during shutdown: %s", e)

    async def initialize_async(self) -> None:
        """Initialize all async components."""
        try:
            # Components initialize themselves asynchronously
            # Just wait a moment for initialization to complete
            await asyncio.sleep(0.5)

            self.is_initialized = True
            self.logger.info("Async core initialization completed")

        except (RuntimeError, OSError, ImportError) as e:
            self.logger.error("Error initializing async core: %s", e)
            raise

    async def start_full_system_scan_async(self, target_paths: list[str]) -> str:
        """Start a comprehensive full system scan."""
        if not self.is_initialized:
            await self.initialize_async()

        config = create_full_scan_config(target_paths)
        scan_id = await self.scanner_engine.start_scan_async(config)

        self.logger.info("Started full system scan %s", scan_id)
        return scan_id

    async def start_quick_scan_async(self, target_paths: list[str]) -> str:
        """Start a quick scan of executable files."""
        if not self.is_initialized:
            await self.initialize_async()

        config = create_quick_scan_config(target_paths)
        scan_id = await self.scanner_engine.start_scan_async(config)

        self.logger.info("Started quick scan %s", scan_id)
        return scan_id

    async def enable_real_time_protection_async(self, watch_paths: list[str]) -> bool:
        """Enable real-time file monitoring and threat detection."""
        if not self.is_initialized:
            await self.initialize_async()

        try:
            # Configure real-time scanning
            config = ScanConfiguration(
                scan_type=ScanType.REAL_TIME,
                target_paths=watch_paths,
                max_concurrent_files=10,
                enable_heuristics=True,
                enable_behavioral=True
            )

            success = await self.scanner_engine.start_real_time_scanning_async(
                watch_paths, config
            )

            if success:
                self.logger.info("Real-time protection enabled for %d paths", len(watch_paths))
            else:
                self.logger.error("Failed to enable real-time protection")

            return success

        except (RuntimeError, OSError) as e:
            self.logger.error("Error enabling real-time protection: %s", e)
            return False

    async def disable_real_time_protection_async(self) -> bool:
        """Disable real-time file monitoring."""
        try:
            success = await self.scanner_engine.stop_real_time_scanning_async()

            if success:
                self.logger.info("Real-time protection disabled")
            else:
                self.logger.error("Failed to disable real-time protection")

            return success

        except (RuntimeError, OSError) as e:
            self.logger.error("Error disabling real-time protection: %s", e)
            return False

    async def get_system_status_async(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get statistics from all components
            threat_stats = await self.threat_detector.get_statistics_async()
            engine_stats = await self.scanner_engine.get_engine_statistics_async()
            watcher_stats = await self.file_watcher.get_statistics_async()

            return {
                "initialized": self.is_initialized,
                "threat_detector": threat_stats,
                "scanner_engine": engine_stats,
                "file_watcher": watcher_stats,
                "real_time_protection": engine_stats.get("real_time_enabled", False),
                "active_scans": engine_stats.get("active_scans", 0),
            }

        except (RuntimeError, OSError) as e:
            self.logger.error("Error getting system status: %s", e)
            return {"error": str(e)}

    async def scan_single_file_async(self, file_path: str) -> dict[str, Any]:
        """Scan a single file for threats."""
        if not self.is_initialized:
            await self.initialize_async()

        try:
            result = await self.threat_detector.scan_file_async(file_path)

            return {
                "file_path": result.file_path,
                "is_threat": result.is_threat,
                "threat_detection": (
                    {
                        "threat_name": result.threat_detection.threat_name,
                        "threat_type": result.threat_detection.threat_type.value,
                        "threat_level": result.threat_detection.threat_level.value,
                        "confidence_score": result.threat_detection.confidence_score,
                        "file_hash": result.threat_detection.file_hash,
                    }
                    if result.threat_detection else None
                ),
                "scan_duration_ms": result.scan_duration_ms,
                "error": result.error,
            }

        except OSError as e:
            self.logger.error("Error scanning file %s: %s", file_path, e)
            return {
                "file_path": file_path,
                "is_threat": False,
                "error": str(e)
            }

    async def update_threat_signatures_async(self, signatures: dict[str, str]) -> bool:
        """Update threat signatures in the detector."""
        try:
            await self.threat_detector.update_signatures_async(signatures)
            self.logger.info("Updated %d threat signatures", len(signatures))
            return True

        except (OSError, ValueError, RuntimeError) as e:
            self.logger.error("Error updating signatures: %s", e)
            return False


# Example usage and demonstration functions
async def demonstrate_async_capabilities() -> None:
    """Demonstrate the async capabilities of the modernized system."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize the async core
    xanados_core = AsyncXanadOSCore()
    await xanados_core.initialize_async()

    try:
        # Demo 1: System status
        logger.info("=== Demo 1: System Status ===")
        status = await xanados_core.get_system_status_async()
        logger.info("System Status: %s", status)

        # Demo 2: Single file scan
        logger.info("=== Demo 2: Single File Scan ===")

        # Create a test file asynchronously
        import tempfile
        import os
        import aiofiles.os

        # Create a temporary file using standard library then write async
        import os
        temp_fd, test_file = tempfile.mkstemp(suffix='.txt')
        os.close(temp_fd)  # Close the file descriptor
        try:
            async with aiofiles.open(test_file, 'w') as tf:
                await tf.write("This is a test file for xanadOS scanning")

            scan_result = await xanados_core.scan_single_file_async(test_file)
            logger.info("Single file scan result: %s", scan_result)
        finally:
            await aiofiles.os.unlink(test_file)

        # Demo 3: Quick scan
        logger.info("=== Demo 3: Quick Scan ===")
        scan_id = await xanados_core.start_quick_scan_async(["/tmp"])
        logger.info("Started quick scan: %s", scan_id)

        # Wait for scan to complete
        await asyncio.sleep(2)

        progress = await xanados_core.scanner_engine.get_scan_progress_async(scan_id)
        stats = await xanados_core.scanner_engine.get_scan_statistics_async(scan_id)
        logger.info("Scan progress: %s", progress)
        logger.info("Scan statistics: %s", stats)

        # Demo 4: Real-time protection
        logger.info("=== Demo 4: Real-time Protection ===")
        success = await xanados_core.enable_real_time_protection_async(["/tmp"])
        logger.info("Real-time protection enabled: %s", success)

        # Let it run for a moment
        await asyncio.sleep(1)

        await xanados_core.disable_real_time_protection_async()

        # Demo 5: Final status
        logger.info("=== Demo 5: Final Status ===")
        final_status = await xanados_core.get_system_status_async()
        logger.info("Final system status: %s", final_status)

    finally:
        # Cleanup
        await xanados_core.shutdown_async()


async def performance_benchmark() -> None:
    """Benchmark the performance of async operations."""
    import time

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    xanados_core = AsyncXanadOSCore()
    await xanados_core.initialize_async()

    try:
        # Benchmark concurrent file scanning
        logger.info("=== Performance Benchmark ===")

        # Create test files asynchronously
        import tempfile
        import aiofiles

        test_files = []
        test_dir = tempfile.mkdtemp()

        try:
            # Create 100 test files asynchronously
            create_tasks = []
            for i in range(100):
                test_file = f"{test_dir}/test_file_{i}.txt"
                create_tasks.append(_create_test_file_async(test_file, f"Test content for file {i}"))
                test_files.append(test_file)

            await asyncio.gather(*create_tasks)

            # Benchmark async scanning
            start_time = time.time()

            tasks = [
                xanados_core.scan_single_file_async(file_path)
                for file_path in test_files
            ]

            results = await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time

            logger.info("Scanned %d files in %.2f seconds", len(test_files), duration)
            logger.info("Average: %.2f files/second", len(test_files) / duration)
            logger.info("Threats detected: %d", sum(1 for r in results if r.get('is_threat')))

        finally:
            # Cleanup test files asynchronously
            await _cleanup_directory_async(test_dir)

    finally:
        await xanados_core.shutdown_async()


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_async_capabilities())

    # Run performance benchmark
    # asyncio.run(performance_benchmark())
