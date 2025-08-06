from PyQt6.QtCore import QThread, pyqtSignal
from dataclasses import asdict

class ScanThread(QThread):
    progress_updated = pyqtSignal(int)
    scan_completed = pyqtSignal(dict)
    status_updated = pyqtSignal(str)
    
    def __init__(self, scanner, path):
        super().__init__()
        self.scanner = scanner
        self.path = path
        
    def run(self):
        try:
            # Set up progress callback
            self.scanner.set_progress_callback(
                lambda p, s: (self.progress_updated.emit(int(p)), self.status_updated.emit(s))
            )
            # Start scan
            self.progress_updated.emit(0)
            self.status_updated.emit("Starting scan...")
            result = self.scanner.scan_directory(self.path)
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