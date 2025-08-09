import os
import sys
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal

# Add the app directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ScanThread(QThread):
    progress_updated = pyqtSignal(int)
    scan_completed = pyqtSignal(dict)
    status_updated = pyqtSignal(str)

    def __init__(self, scanner, path, quick_scan=False, scan_options=None):
        super().__init__()
        self.scanner = scanner
        self.path = path
        self.quick_scan = quick_scan
        self.scan_options = scan_options or {}
        self._cancelled = False

    def stop_scan(self):
        """Safely stop the scan using Qt6 proper interruption"""
        self._cancelled = True
        # Use Qt6 proper thread interruption instead of manual flags
        self.requestInterruption()
        if hasattr(self.scanner, 'cancel_scan'):
            self.scanner.cancel_scan()

    def run(self):
        try:
            # Pass thread reference to scanner for Qt6 interruption checks
            if hasattr(self.scanner, '_current_thread'):
                self.scanner._current_thread = self
                
            # Reset scanner state to clear any leftover cancellation flags
            if hasattr(self.scanner, 'reset_scan_state'):
                self.scanner.reset_scan_state()
                
            # Set up progress callback with proper thread safety
            def safe_progress_callback(progress, status):
                # Check Qt6 interruption request
                if self.isInterruptionRequested() or self._cancelled:
                    return
                try:
                    self.progress_updated.emit(int(progress))
                    self.status_updated.emit(str(status))
                except Exception as e:
                    print(f"Progress callback error: {e}")
            
            # Set up progress callback
            self.scanner.set_progress_callback(safe_progress_callback)
            
            # Check for Qt6 interruption or early cancellation
            if self.isInterruptionRequested() or self._cancelled:
                self.status_updated.emit("Scan cancelled before start")
                self.scan_completed.emit({
                    "status": "cancelled",
                    "message": "Scan was cancelled before starting"
                })
                return
            
            # Start scan with appropriate limits
            self.progress_updated.emit(0)
            self.status_updated.emit("Initializing scan...")

            # Enhanced scan parameters for stability
            max_files = 50 if self.quick_scan else 1000  # Reduced limits to prevent crashes
            max_workers = 2 if self.quick_scan else 3     # Reduced threading to prevent overload
            
            # Check interruption before starting intensive work
            if self.isInterruptionRequested() or self._cancelled:
                return

            # For quick scans, limit the scope and resources
            if self.quick_scan:
                try:
                    from utils.scan_reports import ScanType
                    
                    self.status_updated.emit("Quick scan starting...")
                    result = self.scanner.scan_directory(
                        self.path, 
                        scan_type=ScanType.QUICK, 
                        max_files=max_files,
                        max_workers=max_workers,
                        timeout=300  # 5 minute timeout for quick scans
                    )
                except ImportError:
                    # Fallback if import fails
                    result = self.scanner.scan_directory(
                        self.path, 
                        max_files=max_files,
                        max_workers=max_workers
                    )
                self.status_updated.emit("Quick scan in progress...")
            else:
                # Full scan with enhanced stability measures
                try:
                    from utils.scan_reports import ScanType
                    
                    # Determine scan type based on path
                    if self.path == os.path.expanduser("~") or self.path == "/":
                        scan_type = ScanType.FULL
                        max_files = 2000  # Increased limit for full scans but still safe
                        max_workers = 4   # Slightly more workers for full scans
                    else:
                        scan_type = ScanType.CUSTOM
                    
                    self.status_updated.emit("Full scan starting...")
                    
                    # Check for Qt6 interruption before starting intensive work
                    if self.isInterruptionRequested() or self._cancelled:
                        return
                    
                    result = self.scanner.scan_directory(
                        self.path, 
                        scan_type=scan_type,
                        max_files=max_files,
                        max_workers=max_workers,
                        timeout=1800,  # 30 minute timeout for full scans
                        include_hidden=False,  # Skip hidden files for performance
                        memory_limit_mb=512    # Limit memory usage
                    )
                except ImportError:
                    # Fallback if import fails
                    result = self.scanner.scan_directory(
                        self.path,
                        max_files=max_files,
                        max_workers=max_workers
                    )
                except Exception as scan_error:
                    self.status_updated.emit(f"Scan error: {str(scan_error)}")
                    self.scan_completed.emit({
                        "error": str(scan_error), 
                        "status": "error",
                        "scan_type": "full"
                    })
                    return
                    
                self.status_updated.emit("Full scan in progress...")

            # Check for Qt6 interruption before processing results
            if self.isInterruptionRequested() or self._cancelled:
                self.status_updated.emit("Scan cancelled by user")
                self.scan_completed.emit({
                    "status": "cancelled",
                    "message": "Scan was cancelled by user"
                })
                return

            # Complete scan safely
            self.progress_updated.emit(100)
            self.status_updated.emit("Processing results...")
            
            # Force garbage collection to free memory
            import gc
            gc.collect()
            
            # Convert result to dict with error handling
            try:
                if hasattr(result, '__dict__'):
                    result_dict = asdict(result)
                else:
                    # Manual conversion for non-dataclass results
                    result_dict = {
                        "status": "completed",
                        "scanned_files": getattr(result, "scanned_files", 0),
                        "total_files": getattr(result, "total_files", 0),
                        "threats_found": getattr(result, "threats_found", 0),
                        "duration": getattr(result, "duration", 0),
                        "threats": getattr(result, "threats", []),
                        "scan_id": getattr(result, "scan_id", "unknown"),
                        "success": getattr(result, "success", True),
                        "scan_type": "quick" if self.quick_scan else "full"
                    }
            except (TypeError, AttributeError) as e:
                print(f"Result conversion error: {e}")
                result_dict = {
                    "status": "completed_with_errors",
                    "scanned_files": getattr(result, "scanned_files", 0),
                    "total_files": getattr(result, "total_files", 0),
                    "threats_found": getattr(result, "threats_found", 0),
                    "duration": getattr(result, "duration", 0),
                    "threats": getattr(result, "threats", []),
                    "scan_id": getattr(result, "scan_id", "unknown"),
                    "success": True,  # Consider it successful if we got this far
                    "scan_type": "quick" if self.quick_scan else "full",
                    "conversion_error": str(e)
                }
            
            # Final check before emitting - don't emit if interrupted or cancelled
            if not (self.isInterruptionRequested() or self._cancelled):
                self.status_updated.emit("Scan completed successfully")
                self.scan_completed.emit(result_dict)
            else:
                self.status_updated.emit("Scan cancelled during processing")
                self.scan_completed.emit({
                    "status": "cancelled",
                    "message": "Scan was cancelled during result processing"
                })
            
        except Exception as e:
            print(f"Scan thread error: {e}")
            import traceback
            traceback.print_exc()
            
            # Clean up and report error
            self.progress_updated.emit(0)
            self.status_updated.emit(f"Scan failed: {str(e)}")
            self.scan_completed.emit({
                "error": str(e), 
                "status": "error",
                "scan_type": "quick" if self.quick_scan else "full",
                "traceback": traceback.format_exc()
            })
        finally:
            # Ensure cleanup
            self._cancelled = True
            try:
                if hasattr(self.scanner, 'cleanup'):
                    self.scanner.cleanup()
            except:
                pass
