#!/usr/bin/env python3
"""
Enhanced file scanner with quarantine management and scheduling for S&D - Search & Destroy
"""
import os
import shutil
import hashlib
import threading
import time
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from .clamav_wrapper import ClamAVWrapper, ScanFileResult, ScanResult


class QuarantineAction(Enum):
    """Actions that can be taken on quarantined files."""
    RESTORE = "restore"
    DELETE = "delete"
    SUBMIT_SAMPLE = "submit_sample"


@dataclass
class QuarantinedFile:
    """Information about a quarantined file."""
    original_path: str
    quarantine_path: str
    threat_name: str
    threat_type: str
    quarantine_date: datetime
    file_hash: str
    file_size: int
    scan_id: str


class QuarantineManager:
    """Manages quarantined files and actions."""
    
    def __init__(self):
        from ..utils.config import setup_logging, load_config
        self.logger = setup_logging()
        self.config = load_config()
        self.quarantine_dir = Path(self.config['paths']['quarantine_dir'])
        self.quarantine_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.quarantine_files_dir = self.quarantine_dir / 'files'
        self.quarantine_metadata_dir = self.quarantine_dir / 'metadata'
        
        for directory in [self.quarantine_files_dir, self.quarantine_metadata_dir]:
            directory.mkdir(exist_ok=True)
    
    def quarantine_file(self, file_path: str, threat_name: str, threat_type: str, scan_id: str) -> bool:
        """Move a file to quarantine."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.error("File to quarantine not found: %s", file_path)
                return False
            
            # Generate unique quarantine filename
            file_hash = self._calculate_file_hash(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_filename = f"{timestamp}_{file_hash}_{source_path.name}"
            quarantine_path = self.quarantine_files_dir / quarantine_filename
            
            # Move file to quarantine
            shutil.move(str(source_path), str(quarantine_path))
            
            # Create metadata
            metadata = QuarantinedFile(
                original_path=str(source_path),
                quarantine_path=str(quarantine_path),
                threat_name=threat_name,
                threat_type=threat_type,
                quarantine_date=datetime.now(),
                file_hash=file_hash,
                file_size=quarantine_path.stat().st_size,
                scan_id=scan_id
            )
            
            # Save metadata
            metadata_file = self.quarantine_metadata_dir / f"{quarantine_filename}.json"
            import json
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2, default=str)
            
            self.logger.info("File quarantined: %s -> %s", file_path, quarantine_path)
            return True
            
        except (OSError, IOError, shutil.Error) as e:
            self.logger.error("Failed to quarantine file %s: %s", file_path, e)
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (OSError, IOError):
            return "unknown"
    
    def list_quarantined_files(self) -> List[QuarantinedFile]:
        """List all quarantined files."""
        quarantined_files = []
        
        for metadata_file in self.quarantine_metadata_dir.glob("*.json"):
            try:
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert datetime string back to datetime object
                data['quarantine_date'] = datetime.fromisoformat(data['quarantine_date'])
                quarantined_files.append(QuarantinedFile(**data))
                
            except (json.JSONDecodeError, IOError, TypeError, ValueError) as e:
                self.logger.warning("Failed to load quarantine metadata %s: %s", metadata_file, e)
                continue
        
        return sorted(quarantined_files, key=lambda x: x.quarantine_date, reverse=True)
    
    def restore_file(self, quarantine_path: str, original_path: Optional[str] = None) -> bool:
        """Restore a file from quarantine."""
        try:
            quarantine_file = Path(quarantine_path)
            if not quarantine_file.exists():
                self.logger.error("Quarantined file not found: %s", quarantine_path)
                return False
            
            # Find metadata
            metadata_file = self.quarantine_metadata_dir / f"{quarantine_file.name}.json"
            if not metadata_file.exists():
                self.logger.error("Quarantine metadata not found: %s", metadata_file)
                return False
            
            # Load metadata
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Determine restore path
            restore_path = Path(original_path) if original_path else Path(metadata['original_path'])
            
            # Ensure destination directory exists
            restore_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore file
            shutil.move(str(quarantine_file), str(restore_path))
            
            # Remove metadata
            metadata_file.unlink()
            
            self.logger.info("File restored: %s -> %s", quarantine_path, restore_path)
            return True
            
        except (OSError, IOError, shutil.Error, json.JSONDecodeError) as e:
            self.logger.error("Failed to restore file %s: %s", quarantine_path, e)
            return False
    
    def delete_quarantined_file(self, quarantine_path: str) -> bool:
        """Permanently delete a quarantined file."""
        try:
            quarantine_file = Path(quarantine_path)
            if quarantine_file.exists():
                quarantine_file.unlink()
            
            # Remove metadata
            metadata_file = self.quarantine_metadata_dir / f"{quarantine_file.name}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            self.logger.info("Quarantined file deleted: %s", quarantine_path)
            return True
            
        except (OSError, IOError) as e:
            self.logger.error("Failed to delete quarantined file %s: %s", quarantine_path, e)
            return False
    
    def cleanup_old_quarantine(self, days_to_keep: int = 30) -> None:
        """Clean up old quarantined files."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for quarantined_file in self.list_quarantined_files():
            if quarantined_file.quarantine_date < cutoff_date:
                if self.delete_quarantined_file(quarantined_file.quarantine_path):
                    deleted_count += 1
        
        if deleted_count > 0:
            self.logger.info("Cleaned up %d old quarantined files", deleted_count)


class FileScanner:
    """Enhanced file scanner with quarantine management and scheduling."""
    
    def __init__(self, clamav_wrapper: Optional[ClamAVWrapper] = None):
        from ..utils.config import setup_logging, load_config
        from ..utils.scan_reports import ScanReportManager
        from ..security import PathValidator, FileSizeMonitor
        
        self.logger = setup_logging()
        self.config = load_config()
        self.clamav_wrapper = clamav_wrapper or ClamAVWrapper()
        self.quarantine_manager = QuarantineManager()
        self.scan_report_manager = ScanReportManager()
        
        # Security components
        self.path_validator = PathValidator()
        self.size_monitor = FileSizeMonitor()
        
        # Threading and progress tracking
        self._scan_progress = 0.0
        self._scan_running = False
        self._scan_cancelled = False
        self._current_scan_id = None
        self._total_files_to_scan = 0
        self._files_completed = 0
        
        # Callbacks
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.result_callback: Optional[Callable[[ScanFileResult], None]] = None
        
        # Scheduled scanning
        self._scheduler_thread = None
        self._scheduler_running = False
        
        # Initialize scheduled scans if enabled
        if self.config.get('security_settings', {}).get('scheduled_scanning', False):
            self.start_scheduler()
    
    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """Set callback for scan progress updates."""
        self.progress_callback = callback
    
    def set_result_callback(self, callback: Callable[[ScanFileResult], None]) -> None:
        """Set callback for individual scan results."""
        self.result_callback = callback
    
    def update_virus_definitions(self) -> bool:
        """Update virus definitions using the ClamAV wrapper.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.logger.info("Updating virus definitions...")
        
        # Call the update method in the ClamAV wrapper
        return self.clamav_wrapper.update_virus_definitions()
    
    def scan_file(self, file_path: str, scan_id: Optional[str] = None, **kwargs) -> ScanFileResult:
        """Scan a single file with security validation."""
        from ..security import SecurityValidationError
        
        if not scan_id:
            scan_id = self.scan_report_manager.generate_scan_id()
        
        self.logger.info("Scanning file: %s", file_path)
        
        # Security validation before scanning
        try:
            is_valid, error_msg = self.path_validator.validate_file_for_scan(file_path)
            if not is_valid:
                self.logger.warning("Security validation failed for %s: %s", file_path, error_msg)
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.ERROR,
                    error_message=f"Security validation failed: {error_msg}"
                )
            
            # Check file size limits
            if not self.size_monitor.check_can_process_file(file_path):
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.ERROR,
                    error_message="File size exceeds limits or scan quota reached"
                )
                
        except SecurityValidationError as e:
            self.logger.error("Security validation error for %s: %s", file_path, e)
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message=f"Security validation error: {e}"
            )
        
        # Only report file-level progress if this is a single file scan
        # For multi-file scans, progress is reported by scan_files method
        if hasattr(self, '_total_files_to_scan') and self._total_files_to_scan > 1:
            # Multi-file scan - don't report individual file progress
            pass
        else:
            # Single file scan - report individual progress
            if self.progress_callback:
                self.progress_callback(0.0, f"Scanning {Path(file_path).name}")
        
        # Perform scan
        result = self.clamav_wrapper.scan_file(file_path, **kwargs)
        
        # Record processed file for size monitoring
        self.size_monitor.record_processed_file(file_path)
        
        # Handle infected files
        if result.result == ScanResult.INFECTED:
            self._handle_infected_file(result, scan_id)
        
        # Only report completion for single file scans
        if not hasattr(self, '_total_files_to_scan') or self._total_files_to_scan <= 1:
            if self.progress_callback:
                self.progress_callback(100.0, f"Completed {Path(file_path).name}")
        
        # Notify result
        if self.result_callback:
            self.result_callback(result)
        
        return result
    
    def validate_scan_directory(self, directory_path: str) -> dict:
        """Validate a directory before scanning with comprehensive security checks."""
        from ..security import validate_scan_request
        
        self.logger.info("Validating scan directory: %s", directory_path)
        
        # Use the comprehensive validation function
        validation_result = validate_scan_request(directory_path)
        
        if not validation_result['valid']:
            self.logger.warning("Directory validation failed: %s", validation_result['errors'])
        else:
            self.logger.info("Directory validation passed. Estimated %d files, %d bytes", 
                           validation_result['estimated_files'], 
                           validation_result['estimated_size'])
            
            # Log warnings if any
            for warning in validation_result['warnings']:
                self.logger.warning("Validation warning: %s", warning)
        
        return validation_result
    
    def scan_files(self, file_paths: List[str], scan_type=None,
                   max_workers: int = 4, **kwargs):
        """Scan multiple files with progress tracking and enhanced reporting."""
        from ..utils.scan_reports import ScanResult as ReportScanResult, ThreatInfo, ThreatLevel, ScanType
        
        if scan_type is None:
            scan_type = ScanType.CUSTOM
        """Scan multiple files with threading support."""
        scan_id = self.scan_report_manager.generate_scan_id()
        self._current_scan_id = scan_id
        self._scan_running = True
        self._scan_cancelled = False
        
        # Set total files for progress calculation
        self._total_files_to_scan = len(file_paths)
        self._files_completed = 0
        
        start_time = datetime.now()
        
        # Initialize scan result
        scan_result = ReportScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            start_time=start_time.isoformat(),
            end_time="",
            duration=0.0,
            scanned_paths=[],
            total_files=len(file_paths),
            scanned_files=0,
            threats_found=0,
            threats=[],
            errors=[],
            scan_settings=kwargs,
            engine_version="",
            signature_version="",
            success=False
        )
        
        # Get engine version
        engine_version, sig_version = self.clamav_wrapper.get_engine_version()
        scan_result.engine_version = engine_version
        scan_result.signature_version = sig_version
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all scan tasks
                future_to_path = {
                    executor.submit(self.scan_file, file_path, scan_id, **kwargs): file_path
                    for file_path in file_paths
                }
                
                completed = 0
                for future in as_completed(future_to_path):
                    if self._scan_cancelled:
                        break
                    
                    file_path = future_to_path[future]
                    completed += 1
                    
                    try:
                        file_result = future.result()
                        scan_result.scanned_files += 1
                        
                        if file_result.result == ScanResult.INFECTED:
                            scan_result.threats_found += 1
                            threat_info = ThreatInfo(
                                file_path=file_result.file_path,
                                threat_name=file_result.threat_name,
                                threat_type=file_result.threat_type,
                                threat_level=ThreatLevel.INFECTED,
                                action_taken="detected",
                                timestamp=datetime.now().isoformat(),
                                file_size=file_result.file_size,
                                file_hash=""  # Would calculate if needed
                            )
                            scan_result.threats.append(threat_info)
                        
                        elif file_result.result == ScanResult.ERROR:
                            scan_result.errors.append(f"{file_path}: {file_result.error_message}")
                    
                    except Exception as e:
                        scan_result.errors.append(f"{file_path}: {str(e)}")
                        self.logger.error("Error scanning %s: %s", file_path, e)
                    
                    # Update overall progress with better status message
                    progress = (completed / len(file_paths)) * 100
                    self._scan_progress = progress
                    files_remaining = len(file_paths) - completed
                    
                    if self.progress_callback:
                        # Show current file being scanned and overall progress
                        current_file = Path(file_path).name
                        status_msg = f"Scanning: {current_file} | Completed: {completed} | Remaining: {files_remaining}"
                        self.progress_callback(progress, status_msg)
            
            # Finalize scan result
            end_time = datetime.now()
            scan_result.end_time = end_time.isoformat()
            scan_result.duration = (end_time - start_time).total_seconds()
            scan_result.scanned_paths = file_paths
            scan_result.success = not self._scan_cancelled
            
            # Clean up temporary attributes
            if hasattr(self, '_total_files_to_scan'):
                delattr(self, '_total_files_to_scan')
            if hasattr(self, '_files_completed'):
                delattr(self, '_files_completed')
            
            # Save scan report
            self.scan_report_manager.save_scan_result(scan_result)
            
            self.logger.info(
                "Scan completed: %s - %d files scanned, %d threats found",
                scan_id, scan_result.scanned_files, scan_result.threats_found
            )
            
        except Exception as e:
            scan_result.errors.append(f"Scan error: {str(e)}")
            scan_result.success = False
            self.logger.error("Scan failed: %s", e)
        
        finally:
            self._scan_running = False
            self._current_scan_id = None
        
        return scan_result
    
    def scan_directory(self, directory_path: str, scan_type=None,
                      include_hidden: bool = False, **kwargs):
        """Scan all files in a directory with security validation."""
        from ..utils.scan_reports import ScanResult as ReportScanResult, ScanType
        
        if scan_type is None:
            scan_type = ScanType.CUSTOM
        """Scan a directory recursively."""
        directory_obj = Path(directory_path)
        
        if not directory_obj.exists() or not directory_obj.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Collect all files
        file_paths = []
        for file_path in directory_obj.rglob('*'):
            if file_path.is_file():
                # Skip hidden files unless requested
                if not include_hidden and any(part.startswith('.') for part in file_path.parts):
                    continue
                file_paths.append(str(file_path))
        
        self.logger.info("Found %d files in directory: %s", len(file_paths), directory_path)
        
        return self.scan_files(file_paths, scan_type, **kwargs)
    
    def _handle_infected_file(self, result: ScanFileResult, scan_id: str) -> None:
        """Handle an infected file according to configuration."""
        auto_quarantine = self.config.get('security_settings', {}).get('auto_quarantine_threats', False)
        
        if auto_quarantine:
            success = self.quarantine_manager.quarantine_file(
                result.file_path,
                result.threat_name,
                result.threat_type,
                scan_id
            )
            
            if success:
                self.logger.warning(
                    "Infected file quarantined: %s (%s)",
                    result.file_path, result.threat_name
                )
            else:
                self.logger.error(
                    "Failed to quarantine infected file: %s (%s)",
                    result.file_path, result.threat_name
                )
    
    def cancel_scan(self) -> None:
        """Cancel the current scan."""
        if self._scan_running:
            self._scan_cancelled = True
            self.logger.info("Scan cancellation requested")
    
    def get_scan_progress(self) -> float:
        """Get current scan progress (0-100)."""
        return self._scan_progress
    
    def is_scanning(self) -> bool:
        """Check if a scan is currently running."""
        return self._scan_running
    
    def start_scheduler(self) -> None:
        """Start the scheduled scan scheduler."""
        if self._scheduler_running:
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Scan scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the scheduled scan scheduler."""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join()
        self.logger.info("Scan scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        # Setup scheduled scans based on configuration
        schedule_config = self.config.get('advanced_settings', {})
        update_frequency = schedule_config.get('update_frequency', 'daily')
        update_time = schedule_config.get('update_time', '02:00')
        definition_update = schedule_config.get('auto_update_definitions', True)
        
        # Schedule virus definition updates
        if definition_update:
            # Update definitions daily at 1 AM
            schedule.every().day.at("01:00").do(self.update_virus_definitions)
            self.logger.info("Scheduled daily virus definition updates at 01:00")
        
        # Schedule system scans
        if update_frequency == 'daily':
            schedule.every().day.at(update_time).do(self._scheduled_scan)
            self.logger.info(f"Scheduled daily scans at {update_time}")
        elif update_frequency == 'weekly':
            schedule.every().sunday.at(update_time).do(self._scheduled_scan)
            self.logger.info(f"Scheduled weekly scans on Sunday at {update_time}")
        elif update_frequency == 'monthly':
            # Schedule first Sunday of each month (monthly approximation)
            schedule.every(4).weeks.at(update_time).do(self._scheduled_scan)
            self.logger.info(f"Scheduled monthly scans every 4 weeks at {update_time}")
        
        while self._scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _scheduled_scan(self) -> None:
        """Perform a scheduled scan."""
        if self._scan_running:
            self.logger.info("Skipping scheduled scan - another scan is running")
            return
        
        self.logger.info("Starting scheduled scan")
        
        # Get scan paths from configuration or use defaults
        scan_paths = self.config.get('advanced_settings', {}).get('scheduled_scan_paths', [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            "/tmp"
        ])
        
        # Filter existing paths
        existing_paths = [path for path in scan_paths if Path(path).exists()]
        
        if existing_paths:
            try:
                from ..utils.scan_reports import ScanType
                for path in existing_paths:
                    self.scan_directory(path, ScanType.SCHEDULED)
            except Exception as e:
                self.logger.error("Scheduled scan failed: %s", e)