from PyQt6.QtCore import QThread, pyqtSignal
from dataclasses import asdict
import sys
import os

# Add the app directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ScanThread(QThread):
    progress_updated = pyqtSignal(int)
    scan_completed = pyqtSignal(dict)
    status_updated = pyqtSignal(str)
    
    def __init__(self, scanner, path, quick_scan=False):
        super().__init__()
        self.scanner = scanner
        self.path = path
        self.quick_scan = quick_scan
        
    def run(self):
        try:
            # Set up progress callback
            self.scanner.set_progress_callback(
                lambda p, s: (self.progress_updated.emit(int(p)), self.status_updated.emit(s))
            )
            # Start scan with appropriate limits
            self.progress_updated.emit(0)
            self.status_updated.emit("Starting scan...")
            
            # For quick scans, limit the number of files to prevent crashes
            if self.quick_scan:
                try:
                    from utils.scan_reports import ScanType
                    result = self.scanner.scan_directory(self.path, scan_type=ScanType.QUICK, max_files=50)
                except ImportError:
                    # Fallback if import fails
                    result = self.scanner.scan_directory(self.path, max_files=50)
                self.status_updated.emit("Quick scan in progress...")
            else:
                # Determine scan type based on path
                try:
                    from utils.scan_reports import ScanType
                    if self.path == os.path.expanduser("~"):
                        scan_type = ScanType.FULL
                    else:
                        scan_type = ScanType.CUSTOM
                    result = self.scanner.scan_directory(self.path, scan_type=scan_type)
                except ImportError:
                    # Fallback if import fails
                    result = self.scanner.scan_directory(self.path)
                self.status_updated.emit("Full scan in progress...")
            # Complete scan
            self.progress_updated.emit(100)
            self.status_updated.emit("Scan completed")
            # Convert result to dict
            try:
                result_dict = asdict(result)
            except TypeError:
                result_dict = {
                    'status': 'completed', 
                    'scanned_files': getattr(result, 'scanned_files', 0),
                    'total_files': getattr(result, 'total_files', 0),
                    'threats_found': getattr(result, 'threats_found', 0),
                    'duration': getattr(result, 'duration', 0),
                    'threats': getattr(result, 'threats', []),
                    'scan_id': getattr(result, 'scan_id', 'unknown'),
                    'success': getattr(result, 'success', True)
                }
            self.scan_completed.emit(result_dict)
        except Exception as e:
            self.progress_updated.emit(0)
            self.status_updated.emit(f"Scan failed: {str(e)}")
            self.scan_completed.emit({'error': str(e), 'status': 'error'})