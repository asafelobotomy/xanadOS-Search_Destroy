#!/bin/bash
# Setup script for development tools

set -e

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$TOOLS_DIR")"

echo "Setting up development tools..."

# Check if flatpak-pip-generator has proper permissions
if [ -f "$TOOLS_DIR/flatpak-pip-generator" ]; then
    chmod +x "$TOOLS_DIR/flatpak-pip-generator"
    echo "✅ flatpak-pip-generator permissions set"
fi

# Setup Node.js tools if needed
if [ -f "$TOOLS_DIR/node/package.json" ]; then
    echo "📦 Setting up Node.js development tools..."
    cd "$TOOLS_DIR/node"
    
    if command -v npm >/dev/null 2>&1; then
        npm install
        echo "✅ Node.js tools installed"
    elif command -v yarn >/dev/null 2>&1; then
        yarn install
        echo "✅ Node.js tools installed (via yarn)"
    else
        echo "⚠️  npm/yarn not found - Node.js tools skipped"
    fi
    
    cd "$PROJECT_ROOT"
fi

echo "🎉 Tools setup complete!"
echo ""
echo "Available tools:"
echo "  - flatpak-pip-generator: Generate Flatpak Python dependencies"
if [ -d "$TOOLS_DIR/node/node_modules" ]; then
    echo "  - markdownlint: Lint markdown files"
fi
