#!/usr/bin/env python3
"""
Asynchronous file scanning system for xanadOS Search & Destroy
Provides high-performance scanning with non-blocking operations and worker threads
"""
import asyncio
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional, Callable, AsyncIterator, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import time
import psutil
import threading
from queue import Queue, Empty

from scanner.file_scanner import FileScanner, ScanFileResult
from scanner.clamav_wrapper import ScanResult
from security import PathValidator, FileSizeMonitor
from utils.config import load_config

@dataclass
class ScanProgress:
    """Represents scan progress information."""
    total_files: int = 0
    completed_files: int = 0
    infected_files: int = 0
    errors: int = 0
    current_file: str = ""
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    throughput_fps: float = 0.0  # files per second
    memory_usage_mb: float = 0.0

@dataclass
class ScanBatch:
    """Represents a batch of files to scan."""
    files: List[str]
    batch_id: str
    priority: int = 1  # 1=low, 2=medium, 3=high

class AsyncFileScanner:
    """
    High-performance asynchronous file scanner.
    
    Features:
    - Non-blocking async operations
    - Configurable worker thread pools
    - Memory usage monitoring
    - Batch processing with priorities
    - Real-time progress reporting
    - Automatic load balancing
    """
    
    def __init__(self, max_workers: Optional[int] = None, memory_limit_mb: int = 512):
        """
        Initialize the async scanner.
        
        Args:
            max_workers: Maximum worker threads (auto-detect if None)
            memory_limit_mb: Memory limit in MB before throttling
        """
        self.logger = logging.getLogger(__name__)
        self.config = load_config()
        
        # Auto-detect optimal worker count
        if max_workers is None:
            try:
                cpu_count = psutil.cpu_count(logical=False)
                # Handle case where psutil returns None or Mock object
                if cpu_count is None or not isinstance(cpu_count, int):
                    cpu_count = 2
                max_workers = min(cpu_count * 2, 8)  # Cap at 8 for stability
            except (AttributeError, TypeError):
                # Fallback if psutil is mocked or unavailable
                max_workers = 4
        
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb
        
        # Threading and async components
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = None  # Will be created in event loop
        self.batch_queue = Queue()
        
        # Scanning state
        self.is_scanning = False
        self.scan_cancelled = False
        self.progress = ScanProgress()
        
        # Security components
        self.path_validator = PathValidator()
        self.size_monitor = FileSizeMonitor()
        
        # Progress callbacks
        self.progress_callback: Optional[Callable[[ScanProgress], None]] = None
        self.result_callback: Optional[Callable[[ScanFileResult], None]] = None
        
        # Performance monitoring
        self.scan_start_time = None
        self.files_processed = 0
        self.total_bytes_processed = 0
        
        self.logger.info("AsyncFileScanner initialized with %d workers", max_workers)
    
    async def _setup_async_components(self):
        """Setup async components that require an event loop."""
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_workers)
    
    def _check_memory_usage(self) -> bool:
        """
        Check if memory usage is within limits.
        
        Returns:
            True if memory usage is acceptable, False if throttling needed
        """
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.progress.memory_usage_mb = memory_mb
            
            if memory_mb > self.memory_limit_mb:
                self.logger.warning("Memory usage %.1f MB exceeds limit %d MB", 
                                  memory_mb, self.memory_limit_mb)
                return False
            return True
        except Exception as e:
            self.logger.warning("Memory check failed: %s", e)
            return True  # Continue on error
    
    async def _walk_directory_async(self, directory: str) -> AsyncIterator[str]:
        """
        Asynchronously walk directory tree yielding file paths.
        
        Args:
            directory: Directory path to walk
            
        Yields:
            File paths found in directory
        """
        try:
            directory_path = Path(directory)
            
            # Use os.walk with async wrapper for better performance
            def _walk_sync():
                for root, dirs, files in os.walk(str(directory_path)):
                    if self.scan_cancelled:
                        break
                    for file_name in files:
                        if self.scan_cancelled:
                            break
                        yield str(Path(root) / file_name)
            
            # Process in chunks to avoid blocking
            loop = asyncio.get_event_loop()
            
            async def _chunked_walk():
                file_iterator = _walk_sync()
                chunk_size = 100
                
                while not self.scan_cancelled:
                    chunk = []
                    try:
                        for _ in range(chunk_size):
                            chunk.append(next(file_iterator))
                    except StopIteration:
                        # Yield remaining files
                        for file_path in chunk:
                            yield file_path
                        break
                    
                    # Yield chunk and give control back
                    for file_path in chunk:
                        yield file_path
                    
                    await asyncio.sleep(0.001)  # Allow other tasks to run
            
            async for file_path in _chunked_walk():
                yield file_path
                
        except Exception as e:
            self.logger.error("Error walking directory %s: %s", directory, e)
    
    async def _should_scan_file(self, file_path: str) -> bool:
        """
        Determine if file should be scanned based on security and performance criteria.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file should be scanned, False otherwise
        """
        try:
            # Security validation
            is_valid, error_msg = self.path_validator.validate_file_for_scan(file_path)
            if not is_valid:
                self.logger.debug("File validation failed for %s: %s", file_path, error_msg)
                return False
            
            # Size check
            if not self.size_monitor.check_can_process_file(file_path):
                self.logger.debug("File size check failed for %s", file_path)
                return False
            
            # File type filtering (async file stat)
            try:
                loop = asyncio.get_event_loop()
                stat_result = await loop.run_in_executor(None, os.stat, file_path)
                # Skip very small files (likely not malicious)
                if stat_result.st_size < 10:
                    return False
                    
                # Skip files larger than single file limit
                if stat_result.st_size > 100 * 1024 * 1024:  # 100MB
                    self.logger.debug("Skipping large file: %s (%d bytes)", 
                                    file_path, stat_result.st_size)
                    return False
                    
            except (OSError, PermissionError):
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug("Error checking file %s: %s", file_path, e)
            return False
    
    async def _scan_file_async(self, file_path: str) -> ScanFileResult:
        """
        Scan a single file asynchronously.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            Scan result
        """
        # Ensure semaphore is available
        if self.semaphore is None:
            await self._setup_async_components()
            
        async with self.semaphore:
            # Check memory before proceeding
            if not self._check_memory_usage():
                await asyncio.sleep(0.1)  # Brief pause for memory recovery
            
            loop = asyncio.get_event_loop()
            
            # Run the actual scan in thread pool
            scanner = FileScanner()
            result = await loop.run_in_executor(
                self.executor,
                scanner.scan_file,
                file_path
            )
            
            # Update progress
            self.files_processed += 1
            self.progress.completed_files = self.files_processed
            
            # Calculate throughput
            if self.scan_start_time:
                elapsed = time.time() - self.scan_start_time
                if elapsed > 0:
                    self.progress.throughput_fps = self.files_processed / elapsed
            
            # Update current file
            self.progress.current_file = file_path
            
            # Record file size for monitoring
            try:
                loop = asyncio.get_event_loop()
                stat_result = await loop.run_in_executor(None, os.stat, file_path)
                file_size = stat_result.st_size
                self.total_bytes_processed += file_size
                self.size_monitor.record_processed_file(file_path)
            except OSError:
                pass
            
            # Track infected files
            if result.result == ScanResult.INFECTED:
                self.progress.infected_files += 1
            elif result.result == ScanResult.ERROR:
                self.progress.errors += 1
            
            # Call progress callback
            if self.progress_callback:
                try:
                    self.progress_callback(self.progress)
                except Exception as e:
                    self.logger.warning("Progress callback error: %s", e)
            
            # Call result callback
            if self.result_callback:
                try:
                    self.result_callback(result)
                except Exception as e:
                    self.logger.warning("Result callback error: %s", e)
            
            return result
    
    async def scan_files_async(self, file_paths: List[str]) -> List[ScanFileResult]:
        """
        Scan multiple files asynchronously with parallel processing.
        
        Args:
            file_paths: List of file paths to scan
            
        Returns:
            List of scan results
        """
        await self._setup_async_components()
        
        self.logger.info("Starting async scan of %d files", len(file_paths))
        self.is_scanning = True
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.files_processed = 0
        self.total_bytes_processed = 0
        
        # Initialize progress
        self.progress = ScanProgress(
            total_files=len(file_paths),
            start_time=datetime.now()
        )
        
        try:
            # Filter files that should be scanned
            valid_files = []
            for file_path in file_paths:
                if self.scan_cancelled:
                    break
                if await self._should_scan_file(file_path):
                    valid_files.append(file_path)
            
            self.progress.total_files = len(valid_files)
            self.logger.info("Scanning %d valid files (filtered from %d)", 
                           len(valid_files), len(file_paths))
            
            # Create scan tasks
            tasks = []
            for file_path in valid_files:
                if self.scan_cancelled:
                    break
                task = asyncio.create_task(self._scan_file_async(file_path))
                tasks.append(task)
            
            # Process tasks with progress tracking
            results = []
            
            # Use asyncio.as_completed for real-time results
            for completed_task in asyncio.as_completed(tasks):
                if self.scan_cancelled:
                    # Cancel remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    break
                
                try:
                    result = await completed_task
                    results.append(result)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error("Scan task failed: %s", e)
                    # Create error result
                    error_result = ScanFileResult(
                        file_path="unknown",
                        result=ScanResult.ERROR,
                        error_message=str(e)
                    )
                    results.append(error_result)
            
            elapsed_time = time.time() - self.scan_start_time
            self.logger.info("Async scan completed: %d files in %.2f seconds (%.2f fps)", 
                           len(results), elapsed_time, len(results) / elapsed_time if elapsed_time > 0 else 0)
            
            return results
            
        except Exception as e:
            self.logger.error("Async scan failed: %s", e)
            raise
        finally:
            self.is_scanning = False
    
    async def scan_directory_async(self, directory: str) -> List[ScanFileResult]:
        """
        Scan entire directory asynchronously with optimized file discovery.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            List of scan results
        """
        await self._setup_async_components()
        
        self.logger.info("Starting async directory scan: %s", directory)
        
        # Collect files asynchronously
        file_paths = []
        async for file_path in self._walk_directory_async(directory):
            if self.scan_cancelled:
                break
            file_paths.append(file_path)
            
            # Update progress during file discovery
            if len(file_paths) % 100 == 0:
                self.progress.total_files = len(file_paths)
                if self.progress_callback:
                    try:
                        self.progress_callback(self.progress)
                    except Exception as e:
                        self.logger.warning("Progress callback error: %s", e)
        
        self.logger.info("Found %d files in directory %s", len(file_paths), directory)
        
        # Scan collected files
        return await self.scan_files_async(file_paths)
    
    def cancel_scan(self):
        """Cancel the current scan operation."""
        self.logger.info("Cancelling async scan")
        self.scan_cancelled = True
    
    def set_progress_callback(self, callback: Callable[[ScanProgress], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def set_result_callback(self, callback: Callable[[ScanFileResult], None]):
        """Set callback for individual scan results."""
        self.result_callback = callback
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        elapsed_time = time.time() - self.scan_start_time if self.scan_start_time else 0
        
        return {
            'files_processed': self.files_processed,
            'total_bytes_processed': self.total_bytes_processed,
            'elapsed_time_seconds': elapsed_time,
            'throughput_fps': self.progress.throughput_fps,
            'memory_usage_mb': self.progress.memory_usage_mb,
            'active_workers': self.max_workers,
            'files_per_worker': self.files_processed / self.max_workers if self.max_workers > 0 else 0
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up AsyncFileScanner resources")
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# Global async scanner instance - lazily initialized
_async_scanner = None

def get_async_scanner():
    """Get the global async scanner instance, creating it if needed."""
    global _async_scanner
    if _async_scanner is None:
        _async_scanner = AsyncFileScanner()
    return _async_scanner

# For backward compatibility
async_scanner = get_async_scanner
