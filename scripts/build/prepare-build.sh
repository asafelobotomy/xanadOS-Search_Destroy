#!/bin/bash
# Build preparation script for S&D - Search & Destroy

echo "🧹 Preparing build environment..."

# Stop any running instances
echo "Stopping any running application instances..."
pkill -f "python.*main.py" 2>/dev/null || true

# Clean all artifacts
echo "Cleaning build artifacts and cache files..."
make clean-all

# Verify virtual environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    make dev-setup
else
    echo "✅ Virtual environment exists"
fi

# Run tests to ensure everything works
echo "🧪 Running tests to verify build readiness..."
make test

# Check code style
echo "🎨 Checking code style..."
make check-style || echo "⚠️  Code style issues found (non-blocking)"

# Verify Flatpak manifest
echo "📋 Verifying Flatpak manifest..."
if [ -f "packaging/flatpak/org.xanados.SearchAndDestroy.yml" ]; then
    echo "✅ Flatpak manifest found"
else
    echo "❌ Flatpak manifest missing!"
    exit 1
fi

# Check required icons
echo "🎨 Checking application icons..."
icon_count=$(find packaging/icons/ -name "*.svg" -o -name "*.png*" | wc -l)
if [ "$icon_count" -gt 0 ]; then
    echo "✅ Application icons found ($icon_count files)"
else
    echo "❌ No application icons found!"
    exit 1
fi

echo ""
echo "🎉 Build environment is ready!"
echo ""
echo "Next steps:"
echo "  make build-flatpak    - Build the Flatpak package"
echo "  make install-flatpak  - Install locally"
echo "  make run-flatpak      - Run the installed application"
echo ""
