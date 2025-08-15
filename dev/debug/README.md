# # Debug and Test Scripts

This directory contains debug and test scripts that were moved from the root directory during repository cleanup.

## Authentication Scripts

- `test_authentication_methods.py` - Test various authentication methods
- `test_auth_fix.py` - Authentication fix validation
- `test_direct_authentication.py` - Direct authentication testing
- `test_direct_auth_final.py` - Final authentication implementation test
- `test_improved_auth.py` - Improved authentication mechanism test
- `test_wrapper_auth_fix.py` - Wrapper authentication fix test

## GUI Testing Scripts

- `test_gui_pkexec.py` - GUI pkexec integration test
- `test_gui_scan.py` - GUI scanning functionality test
- `test_gui_scan_simple.py` - Simplified GUI scan test

## System Component Scripts

- `test_firewall.py` - Firewall functionality test
- `test_firewall_gui.py` - Firewall GUI integration test
- `test_pkexec.py` - pkexec system test
- `test_without_config.py` - Test without configuration
- `test_threats_card.py` - Threats card component test

## Debug Scripts

- `debug_firewall.py` - Firewall debugging
- `debug_pkexec_gui.py` - pkexec GUI debugging
- `debug_rkhunter.py` - RKHunter integration debugging
- `debug_sudo_command.py` - sudo command debugging

## Usage

These scripts are for development and debugging purposes only. They are not part of the main application.

```bash
# Run a specific debug script
python dev/debug-scripts/debug_[component].py

# Run a specific test script
python dev/debug-scripts/test_[feature].py
```

**Note**: These scripts may require specific system permissions or configurations to run properly.
