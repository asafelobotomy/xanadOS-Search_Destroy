# Development Tools

This directory contains development tools and utilities for the xanadOS Search & Destroy project.

## Tools

### flatpak-pip-generator

- **Purpose**: Generates Flatpak manifests for Python dependencies
- **Usage**: Used during Flatpak package creation
- **Type**: External tool script
- **Location**: Moved from root directory for better organization

### node/package.json

- **Purpose**: Node.js dependencies for development tools (markdownlint)
- **Usage**: `cd tools/node && npm install` to install linting tools
- **Type**: Node.js package configuration
- **Location**: Moved from root directory for better organization

## Directory Organization

```text
tools/
├── README.md                    # This file
├── flatpak-pip-generator        # Flatpak dependency generator
├── node/                        # Node.js development tools
│   └── package.json            # markdownlint and other Node tools
└── [future tools]               # Additional development tools
```

## Usage

These tools are typically used during the build and packaging process. Most tools are called automatically by scripts in the `scripts/` directory or by the Makefile.

## Adding New Tools

When adding new development tools:

1. Place executable tools directly in this directory
2. Add documentation to this README
3. Ensure tools have proper permissions (`chmod +x`)
4. Update relevant build scripts if needed

## Related Directories

- `scripts/` - Build and deployment scripts
- `dev/` - Development utilities and testing tools
- `packaging/` - Package-specific files and configurations
