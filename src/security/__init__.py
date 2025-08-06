#!/usr/bin/env python3
"""
Security module for S&D - Search & Destroy
Provides input validation, privilege management, and security utilities
"""

from .input_validation import (
    PathValidator,
    InputSanitizer, 
    FileSizeMonitor,
    SecurityValidationError,
    validate_scan_request,
    MAX_FILE_SIZE,
    MAX_ARCHIVE_SIZE,
    MAX_SCAN_DEPTH,
    MAX_FILES_PER_SCAN
)

from .privilege_escalation import (
    PrivilegeEscalationManager,
    PrivilegeOperation,
    ElevationRequest,
    SecureElevationError,
    privilege_manager,
    require_elevation
)

from .network_security import (
    SecureNetworkManager,
    NetworkSecurityLevel,
    SecureEndpoint,
    NetworkSecurityError,
    network_security
)

__all__ = [
    # Input validation exports
    'PathValidator',
    'InputSanitizer',
    'FileSizeMonitor', 
    'SecurityValidationError',
    'validate_scan_request',
    'MAX_FILE_SIZE',
    'MAX_ARCHIVE_SIZE',
    'MAX_SCAN_DEPTH',
    'MAX_FILES_PER_SCAN',
    
    # Privilege escalation exports
    'PrivilegeEscalationManager',
    'PrivilegeOperation',
    'ElevationRequest',
    'SecureElevationError',
    'privilege_manager',
    'require_elevation',
    
    # Network security exports
    'SecureNetworkManager',
    'NetworkSecurityLevel',
    'SecureEndpoint',
    'NetworkSecurityError',
    'network_security'
]
