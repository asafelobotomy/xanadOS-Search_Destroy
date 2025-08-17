"""
Integration patch for non-invasive status monitoring
Replaces elevated privilege status checks with activity-based caching
"""

# ==============================================================================
# STEP 1: Update RKHunter Optimizer to use non-invasive methods
# ==============================================================================

# In app/core/rkhunter_optimizer.py, replace get_current_status() method:

def get_current_status_non_invasive(self) -> RKHunterStatus:
    """Get RKHunter status using non-invasive methods (PATCHED VERSION)"""
    from .rkhunter_monitor_non_invasive import get_rkhunter_status_non_invasive
    
    try:
        # Use non-invasive monitor instead of elevated commands
        ni_status = get_rkhunter_status_non_invasive()
        
        # Convert to original RKHunterStatus format for compatibility
        return RKHunterStatus(
            version=ni_status.version,
            config_file=self.config_path,
            database_version="Available" if ni_status.database_exists else "Not Available",
            last_update=None,  # Would require parsing logs for exact time
            last_scan=ni_status.last_scan_attempt,
            baseline_exists=ni_status.database_exists,
            mirror_status="OK" if ni_status.available else "Not Available",
            performance_metrics={},
            issues_found=ni_status.issues_found
        )
        
    except Exception as e:
        logger.error(f"Error getting RKHunter status (non-invasive): {e}")
        return RKHunterStatus(
            version="Error",
            config_file=self.config_path,
            database_version="Error",
            last_update=None,
            last_scan=None,
            baseline_exists=False,
            mirror_status="Error",
            performance_metrics={},
            issues_found=[f"Status check failed: {str(e)}"]
        )

# ==============================================================================
# STEP 2: Update GUI components to use cached status checking
# ==============================================================================

# In app/gui/settings_pages.py, update RKHunterOptimizationWorker:

def run_non_invasive(self):
    """Run RKHunter optimization with non-invasive status checking"""
    if not self.optimizer:
        self.error_occurred.emit("RKHunter optimizer not available")
        return
        
    try:
        self.progress_updated.emit("Initializing RKHunter optimizer...")
        
        # Use non-invasive status checking instead of elevated commands
        self.progress_updated.emit("Checking current RKHunter status (non-invasive)...")
        
        # Import non-invasive monitor
        from core.rkhunter_monitor_non_invasive import get_rkhunter_status_non_invasive, record_rkhunter_activity
        
        # Record user activity for cache management
        record_rkhunter_activity("optimization_started", "User initiated RKHunter optimization")
        
        # Get status using non-invasive method
        ni_status = get_rkhunter_status_non_invasive()
        
        # Convert to original format for compatibility
        status = self.optimizer.get_current_status_non_invasive()
        self.status_updated.emit(status)
        
        # Only proceed with optimization if RKHunter is available
        if ni_status.available:
            # Run optimization (this may still require elevated privileges for actual changes)
            self.progress_updated.emit("Applying configuration optimizations...")
            report = self.optimizer.optimize_configuration(self.config)
            
            # Record completion
            record_rkhunter_activity("optimization_completed", "Optimization finished successfully")
            
            self.progress_updated.emit("Optimization complete")
            self.optimization_complete.emit(report)
        else:
            self.error_occurred.emit("RKHunter is not installed or accessible")
            
    except Exception as e:
        logger.error(f"Error in RKHunter optimization (non-invasive): {e}")
        self.error_occurred.emit(str(e))

# ==============================================================================
# STEP 3: Update main window timer functions
# ==============================================================================

# In app/gui/main_window.py, update status checking timers:

def update_system_status_non_invasive(self):
    """Update all system status displays using non-invasive methods"""
    try:
        from core.non_invasive_monitor import get_system_status
        
        # Get comprehensive system status without sudo requirements
        status = get_system_status()
        
        # Update virus definitions display
        if hasattr(self, 'last_update_label'):
            if status.virus_definitions_age >= 0:
                if status.virus_definitions_age == 0:
                    self.last_update_label.setText("Status: Up to date")
                elif status.virus_definitions_age <= 3:
                    self.last_update_label.setText(f"Status: {status.virus_definitions_age} days old (good)")
                elif status.virus_definitions_age <= 7:
                    self.last_update_label.setText(f"Status: {status.virus_definitions_age} days old (update recommended)")
                else:
                    self.last_update_label.setText(f"Status: {status.virus_definitions_age} days old (update needed)")
            else:
                self.last_update_label.setText("Status: Unknown")
        
        # Update security services status
        if hasattr(self, 'security_services_label'):
            active_services = [name for name, state in status.system_services.items() if state == "active"]
            if active_services:
                self.security_services_label.setText(f"Active: {', '.join(active_services)}")
            else:
                self.security_services_label.setText("No security services active")
        
        print("✅ System status updated using non-invasive methods")
        
    except Exception as e:
        print(f"⚠️ Error updating system status: {e}")

# ==============================================================================
# STEP 4: Replace automatic status checking timers
# ==============================================================================

# Replace these timer calls in main_window.py __init__:

# OLD (potentially problematic):
# QTimer.singleShot(100, self.update_definition_status)

# NEW (non-invasive):
QTimer.singleShot(100, self.update_system_status_non_invasive)

# ==============================================================================
# STEP 5: Add non-invasive imports to core/__init__.py
# ==============================================================================

# Add these imports to app/core/__init__.py:

from .non_invasive_monitor import (
    NonInvasiveSystemMonitor,
    SystemStatus,
    get_system_status,
    record_activity,
    system_monitor
)

from .rkhunter_monitor_non_invasive import (
    RKHunterMonitorNonInvasive,
    RKHunterStatusNonInvasive,
    get_rkhunter_status_non_invasive,
    record_rkhunter_activity,
    rkhunter_monitor
)

# ==============================================================================
# STEP 6: Update __all__ exports
# ==============================================================================

# Add to the __all__ list in app/core/__init__.py:

__all__ = [
    # ... existing exports ...
    "NonInvasiveSystemMonitor",
    "SystemStatus",
    "get_system_status",
    "record_activity",
    "system_monitor",
    "RKHunterMonitorNonInvasive", 
    "RKHunterStatusNonInvasive",
    "get_rkhunter_status_non_invasive",
    "record_rkhunter_activity",
    "rkhunter_monitor",
]

# ==============================================================================
# IMPLEMENTATION NOTES
# ==============================================================================

"""
CRITICAL SUCCESS CRITERIA:
1. ✅ Application runs 60+ seconds without authentication prompts
2. ✅ Status displays work using non-invasive methods  
3. ✅ Only user-initiated actions trigger authentication
4. ✅ Automatic timers never cause privilege escalation
5. ✅ Firewall detection uses proven non-invasive approach (ALREADY IMPLEMENTED)

IMPLEMENTATION PRIORITY:
1. 🔴 HIGH: Replace automatic status checking in GUI timers
2. 🟡 MEDIUM: Update RKHunter optimization worker to use non-invasive checking
3. 🔵 LOW: Enhance log parsing for more detailed status information

TESTING STRATEGY:
- Run app for 60+ seconds and verify no authentication prompts
- Test all status displays work correctly
- Verify user-triggered operations still work properly
- Test cache persistence across app sessions
"""
