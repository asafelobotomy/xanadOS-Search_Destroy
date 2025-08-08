# Development Guide

This directory contains development tools, scripts, and resources for the xanadOS-Search_Destroy project.

## Directory Structure

```
dev/
├── README.md                 # This file
├── cleanup_repository.py     # Repository cleanup script
├── debug-scripts/           # Debug and test scripts
│   ├── README.md
│   └── *.py                 # Various debug/test files
├── demos/                   # Demo applications
│   ├── demo_strawberry_theme.py
│   └── demo_sunrise_theme.py
└── test-scripts/            # Test validation scripts
    ├── test_*.py            # Various test scripts
    └── README.md
```

## Usage

### Repository Cleanup
```bash
python dev/cleanup_repository.py
```

### Running Tests
```bash
# Run specific test scripts
python dev/test-scripts/test_[specific_feature].py

# Run all tests
find dev/test-scripts -name "test_*.py" -exec python {} \;
```

### Debug Scripts
Debug scripts are located in `dev/debug-scripts/` and can be used for:
- Authentication testing
- GUI component debugging  
- Firewall functionality testing
- RKHunter integration testing

### Development Workflow

1. **Before making changes**: Run cleanup script to ensure clean environment
2. **During development**: Use debug scripts to test specific components
3. **After changes**: Run relevant test scripts to validate functionality
4. **Before commit**: Ensure all tests pass and run cleanup script

- `demo_strawberry_theme.py` - Demonstrates the dark theme (Strawberry palette)
- `demo_sunrise_theme.py` - Demonstrates the light theme (Sunrise palette)

### `/test-scripts/`

Contains development test scripts used during implementation:

- Various test scripts for bug fixes, UI improvements, and feature testing
- These scripts were used during development to validate specific functionality

## Usage

These resources are primarily for developers working on the application. They are not required for normal application usage.

### Running Demo Scripts

```bash
cd dev/demos
python demo_strawberry_theme.py
python demo_sunrise_theme.py
```

### Test Scripts

The test scripts in `/test-scripts/` are historical development aids and may require modification to run with the current codebase.

## Note

Files in this directory are development resources and are not included in the main application distribution.
