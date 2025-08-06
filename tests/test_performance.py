#!/usr/bin/env python3
"""
Integration tests for Phase 2 performance optimization
Tests async scanning, memory optimization, database performance, and UI responsiveness
"""
import unittest
import tempfile
import os
import time
import asyncio
from pathlib import Path
import sqlite3
import threading
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

class TestAsyncScanner(unittest.TestCase):
    """Test async file scanner functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create test files
        for i in range(5):
            test_file = Path(self.temp_dir) / f"test_file_{i}.txt"
            test_file.write_text(f"Test content {i}")
            self.test_files.append(str(test_file))
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_async_scanner_import(self):
        """Test async scanner can be imported."""
        try:
            from performance.async_scanner import AsyncFileScanner
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import AsyncFileScanner: {e}")
    
    def test_async_scanner_initialization(self):
        """Test async scanner can be initialized."""
        from performance.async_scanner import AsyncFileScanner
        
        scanner = AsyncFileScanner(max_workers=2)
        self.assertEqual(scanner.max_workers, 2)
        self.assertIsNotNone(scanner.executor)
    
    @patch('scanner.file_scanner.FileScanner.scan_file')
    def test_async_file_scanning(self, mock_scan):
        """Test async file scanning functionality."""
        from performance.async_scanner import AsyncFileScanner
        
        # Mock scan results
        mock_scan.return_value = ("CLEAN", None)
        
        scanner = AsyncFileScanner(max_workers=2)
        
        # Run async scan in event loop
        async def run_test():
            results = await scanner.scan_files_async(self.test_files[:2])
            return results
        
        # Execute async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_test())
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
        finally:
            loop.close()
            scanner.cleanup()

class TestMemoryOptimizer(unittest.TestCase):
    """Test memory optimizer functionality."""
    
    def test_memory_optimizer_import(self):
        """Test memory optimizer can be imported."""
        try:
            from performance.memory_optimizer import MemoryOptimizer
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import MemoryOptimizer: {e}")
    
    def test_memory_optimizer_initialization(self):
        """Test memory optimizer can be initialized."""
        from performance.memory_optimizer import MemoryOptimizer
        
        optimizer = MemoryOptimizer()
        self.assertIsNotNone(optimizer.pools)
        self.assertIsNotNone(optimizer.cache_refs)
    
    def test_memory_monitoring(self):
        """Test memory usage monitoring."""
        from performance.memory_optimizer import MemoryOptimizer
        
        optimizer = MemoryOptimizer()
        memory_info = optimizer.get_memory_stats()
        
        self.assertIsNotNone(memory_info)
        self.assertIsInstance(memory_info.used_percent, float)
        self.assertIsInstance(memory_info.used_mb, float)
    
    def test_garbage_collection(self):
        """Test garbage collection functionality."""
        from performance.memory_optimizer import MemoryOptimizer
        
        optimizer = MemoryOptimizer()
        
        # Force memory optimization
        optimizer.optimize_memory(aggressive=True)
        # Should not raise any exceptions

class TestDatabaseOptimizer(unittest.TestCase):
    """Test database optimizer functionality."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.db_path)
        except:
            pass
    
    def test_database_optimizer_import(self):
        """Test database optimizer can be imported."""
        try:
            from performance.database_optimizer import DatabaseConnectionPool
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import DatabaseConnectionPool: {e}")
    
    def test_connection_pool_initialization(self):
        """Test connection pool can be initialized."""
        from performance.database_optimizer import DatabaseConnectionPool
        
        pool = DatabaseConnectionPool(self.db_path, max_connections=2)
        self.assertEqual(pool.max_connections, 2)
        self.assertEqual(pool.database_path, self.db_path)
        pool.close_all()
    
    def test_connection_pool_usage(self):
        """Test connection pool provides working connections."""
        from performance.database_optimizer import DatabaseConnectionPool
        
        pool = DatabaseConnectionPool(self.db_path, max_connections=2)
        
        try:
            with pool.get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)
        finally:
            pool.close_all()
    
    def test_scan_results_db(self):
        """Test scan results database functionality."""
        from performance.database_optimizer import ScanResultsDB
        
        db = ScanResultsDB(self.db_path)
        
        try:
            # Create a scan session
            session_id = db.create_scan_session("test_scan")
            self.assertIsInstance(session_id, int)
            self.assertGreater(session_id, 0)
            
            # Add scan results
            db.add_scan_result(session_id, "/test/file.txt", 1024, "CLEAN")
            db.add_scan_result(session_id, "/test/malware.exe", 2048, "INFECTED", "TestVirus")
            
            # Finish scan session
            db.finish_scan_session(session_id, 2, 1, 0)
            
            # Verify session was recorded
            sessions = db.get_recent_sessions(limit=1)
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]['id'], session_id)
            
        finally:
            db.close()

class TestUIResponsiveness(unittest.TestCase):
    """Test UI responsiveness functionality."""
    
    def test_ui_responsiveness_import(self):
        """Test UI responsiveness can be imported."""
        try:
            from performance.ui_responsiveness import ResponsiveUI
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import ResponsiveUI: {e}")
    
    @patch('performance.ui_responsiveness.QTimer')
    def test_responsive_ui_initialization(self, mock_timer):
        """Test responsive UI can be initialized."""
        from performance.ui_responsiveness import ResponsiveUI
        
        # Mock QTimer to avoid Qt dependency
        mock_timer_instance = Mock()
        mock_timer.return_value = mock_timer_instance
        
        ui = ResponsiveUI()
        # Should not crash during initialization
        self.assertIsNotNone(ui)
    
    def test_scan_progress_manager(self):
        """Test scan progress manager functionality."""
        from performance.ui_responsiveness import ScanProgressManager
        
        # Skip test if PyQt6 is globally mocked (affects inheritance)
        import sys
        from unittest.mock import Mock
        if isinstance(sys.modules.get('PyQt6'), Mock):
            self.skipTest("PyQt6 is globally mocked, skipping inheritance-dependent test")
        
        progress = ScanProgressManager()
        
        # Start scan
        progress.start_scan(100)
        self.assertEqual(progress.total_files, 100)
        self.assertEqual(progress.scanned_files, 0)
        
        # Update progress
        progress.update_progress(scanned=10, infected=1)
        self.assertEqual(progress.scanned_files, 10)
        self.assertEqual(progress.infected_files, 1)
        
        # Finish scan
        progress.finish_scan()
        # Should not raise any exceptions
    
    @patch('performance.ui_responsiveness.QApplication.setOverrideCursor')
    @patch('performance.ui_responsiveness.QApplication.restoreOverrideCursor')
    def test_loading_indicator(self, mock_restore_cursor, mock_set_cursor):
        """Test loading indicator functionality."""
        from performance.ui_responsiveness import LoadingIndicator
        
        # Skip test if PyQt6 is globally mocked (affects inheritance)
        import sys
        from unittest.mock import Mock
        if isinstance(sys.modules.get('PyQt6'), Mock):
            self.skipTest("PyQt6 is globally mocked, skipping inheritance-dependent test")
        
        indicator = LoadingIndicator()
        
        # Test loading state
        self.assertFalse(indicator.is_loading())
        
        indicator.start_loading("test_op", "Testing...")
        self.assertTrue(indicator.is_loading())
        self.assertTrue(indicator.is_loading("test_op"))
        
        # Verify QApplication methods were called
        mock_set_cursor.assert_called_once()
        
        indicator.stop_loading("test_op")
        self.assertFalse(indicator.is_loading())
        
        # Verify cursor was restored
        mock_restore_cursor.assert_called_once()

class TestPerformanceIntegration(unittest.TestCase):
    """Test integration of all performance components."""
    
    def test_performance_module_import(self):
        """Test performance module can be imported completely."""
        try:
            import performance
            from performance import (
                AsyncFileScanner, MemoryOptimizer, ScanResultsDB,
                ResponsiveUI, ScanProgressManager
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import performance module: {e}")
    
    def test_global_functions(self):
        """Test global utility functions."""
        try:
            from performance.database_optimizer import get_scan_db
            from performance.ui_responsiveness import (
                initialize_responsive_ui, get_responsive_ui
            )
            
            # These should not raise exceptions when called
            self.assertIsNotNone(get_scan_db)
            self.assertIsNotNone(initialize_responsive_ui)
            self.assertIsNotNone(get_responsive_ui)
            
        except Exception as e:
            self.fail(f"Global functions failed: {e}")
    
    def test_thread_safety(self):
        """Test thread safety of performance components."""
        from performance.memory_optimizer import MemoryOptimizer
        
        optimizer = MemoryOptimizer()
        results = []
        
        def worker():
            for _ in range(10):
                memory_info = optimizer.get_memory_stats()
                results.append(memory_info.used_percent)
                time.sleep(0.01)
        
        # Run multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have results from all threads
        self.assertEqual(len(results), 30)
        for result in results:
            self.assertIsInstance(result, float)
            self.assertGreaterEqual(result, 0)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
