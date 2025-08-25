# Tests Directory

This directory contains all test scripts and demonstrations for the xanadOS Search & Destroy project.

## Directory Structure

### `/hardening/`

Test scripts for system hardening functionality:

- `test_hardening_*.py` - Various hardening feature tests
- `test_standardized_scoring.py` - Security scoring system tests
- `test_duplicate_fix.py` - Duplicate recommendation fix tests
- `test_live_hardening.py` - Live hardening system tests
- `simple_rkhunter_test.py` - RKHunter integration tests
- `verify_unified_auth.py` - Authentication system tests

### `/ui/`

User interface and GUI-related tests:

- `test_button_overlap.py` - Button layout overlap tests
- `test_overlap_fix.py` - UI overlap fix validation
- `test_improved_presentation.py` - UI presentation enhancement tests
- `test_light_mode.py` - Light mode theme tests

### `/demos/`

Demonstration scripts for showcasing features:

- `theme_showcase.py` - Theme system demonstration
- `demo_presentation.py` - Feature presentation demos
- `space_optimization_demo.py` - UI space optimization demos

### Core Test Files

- `test_gui.py` - Main GUI component tests
- `test_monitoring.py` - System monitoring tests
- `conftest.py` - PyTest configuration

Note: The legacy umbrella test `test_implementation.py` has been archived to `archive/deprecated/2025-08-25/tests/` and removed from active tests.

## Running Tests

```bash

## Run all tests

pytest

## Run specific test category

pytest tests/hardening/
pytest tests/ui/

## Run with coverage

pytest --cov=app tests/

```text

## Test Guidelines

1. **Naming Convention**: Use descriptive names starting with `test_`
2. **Organization**: Place tests in appropriate subdirectories
3. **Documentation**: Include docstrings explaining test purpose
4. **Isolation**: Each test should be independent and cleanup after itself
