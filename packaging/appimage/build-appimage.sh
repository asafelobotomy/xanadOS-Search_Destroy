#!/bin/bash
# Build script for xanadOS Search & Destroy AppImage
# This script creates a portable AppImage for Linux distribution

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Build configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build/appimage"
APPDIR="$BUILD_DIR/xanadOS-Search-Destroy.AppDir"
VERSION=$(cat "$PROJECT_ROOT/VERSION" | tr -d '\n')
ARCH=$(uname -m)
OUTPUT_NAME="xanadOS-Search-Destroy-${VERSION}-${ARCH}.AppImage"

echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}  xanadOS Search & Destroy - AppImage Builder${NC}"
echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Version:${NC} $VERSION"
echo -e "${BLUE}Architecture:${NC} $ARCH"
echo -e "${BLUE}Output:${NC} $OUTPUT_NAME"
echo ""

# Check for required tools
echo -e "${YELLOW}→${NC} Checking build dependencies..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required but not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check for appimagetool
if ! command -v appimagetool &> /dev/null; then
    echo -e "${YELLOW}⚠ appimagetool not found, attempting to download...${NC}"
    # Download before creating build directories
    TOOL_DOWNLOAD_DIR="/tmp/appimage-tools"
    mkdir -p "$TOOL_DOWNLOAD_DIR"
    APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    curl -L "$APPIMAGETOOL_URL" -o "$TOOL_DOWNLOAD_DIR/appimagetool"
    chmod +x "$TOOL_DOWNLOAD_DIR/appimagetool"
    APPIMAGETOOL="$TOOL_DOWNLOAD_DIR/appimagetool"
    echo -e "${GREEN}✓${NC} appimagetool downloaded"
else
    APPIMAGETOOL="appimagetool"
    echo -e "${GREEN}✓${NC} appimagetool found"
fi

# Clean previous build
echo ""
echo -e "${YELLOW}→${NC} Cleaning previous build..."
rm -rf "$BUILD_DIR"
mkdir -p "$APPDIR/usr"
echo -e "${GREEN}✓${NC} Build directory prepared"

# Create directory structure
echo ""
echo -e "${YELLOW}→${NC} Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APPDIR/usr/share/polkit-1/actions"
mkdir -p "$APPDIR/usr/app"
mkdir -p "$APPDIR/usr/share/clamav"
mkdir -p "$APPDIR/usr/share/rkhunter"
echo -e "${GREEN}✓${NC} Directory structure created"

# Bundle system Python with all dependencies
echo ""
echo -e "${YELLOW}→${NC} Bundling Python runtime and dependencies..."

# Install dependencies in the project venv first
source "$PROJECT_ROOT/.venv/bin/activate"

# Copy Python binary and stdlib
PYTHON_BIN=$(which python3)
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

echo -e "${CYAN}  Copying Python $PYTHON_VERSION runtime...${NC}"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/python$PYTHON_VERSION"

# Copy Python binary
cp -L "$PYTHON_BIN" "$APPDIR/usr/bin/python3"
chmod +x "$APPDIR/usr/bin/python3"

# Copy Python standard library from system
echo -e "${CYAN}  Copying Python standard library...${NC}"
if [ -d "/usr/lib/python$PYTHON_VERSION" ]; then
    cp -r "/usr/lib/python$PYTHON_VERSION"/* "$APPDIR/usr/lib/python$PYTHON_VERSION/"
else
    echo -e "${RED}✗ System Python library not found at /usr/lib/python$PYTHON_VERSION${NC}"
    exit 1
fi

# Copy required shared libraries for Python
echo -e "${CYAN}  Copying Python shared libraries...${NC}"
for lib in $(ldd "$PYTHON_BIN" | grep "=>" | awk '{print $3}' | grep -E "libpython|libssl|libcrypto"); do
    if [ -f "$lib" ]; then
        cp -L "$lib" "$APPDIR/usr/lib/"
    fi
done

# Verify Python installation
if [ ! -f "$APPDIR/usr/bin/python3" ]; then
    echo -e "${RED}✗ Python installation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python runtime bundled"

# Install Python dependencies
echo ""
echo -e "${YELLOW}→${NC} Installing Python dependencies..."

# Install dependencies in the venv first, then copy them to AppDir
cd "$PROJECT_ROOT"
source .venv/bin/activate

# Ensure all dependencies are installed in the venv
echo -e "${CYAN}  Installing dependencies in venv...${NC}"
pip install -r "$SCRIPT_DIR/requirements.txt"
pip install -e .

# Copy site-packages from venv to AppDir
echo -e "${CYAN}  Copying dependencies to AppDir...${NC}"
VENV_SITE_PACKAGES="$PROJECT_ROOT/.venv/lib/python$PYTHON_VERSION/site-packages"
APPDIR_SITE_PACKAGES="$APPDIR/usr/lib/python$PYTHON_VERSION/site-packages"

# Ensure the directory exists and is writable
mkdir -p "$APPDIR_SITE_PACKAGES"
chmod -R u+w "$APPDIR/usr/lib/python$PYTHON_VERSION" 2>/dev/null || true

# Copy or overwrite with venv site-packages
cp -rf "$VENV_SITE_PACKAGES"/* "$APPDIR_SITE_PACKAGES/"

echo -e "${GREEN}✓${NC} Dependencies installed"

# Copy application code
echo ""
echo -e "${YELLOW}→${NC} Copying application files..."
cp -r "$PROJECT_ROOT/app" "$APPDIR/usr/app/"
cp -r "$PROJECT_ROOT/config" "$APPDIR/usr/app/"
cp "$PROJECT_ROOT/VERSION" "$APPDIR/usr/app/"
echo -e "${GREEN}✓${NC} Application files copied"

# Copy PolicyKit policies
echo -e "${YELLOW}→${NC} Copying PolicyKit policies..."
cp "$PROJECT_ROOT/config"/*.policy "$APPDIR/usr/share/polkit-1/actions/" 2>/dev/null || true
echo -e "${GREEN}✓${NC} PolicyKit policies copied"

# Copy AppRun launcher
echo -e "${YELLOW}→${NC} Installing AppRun launcher..."
cp "$SCRIPT_DIR/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
echo -e "${GREEN}✓${NC} AppRun installed"

# Copy desktop file
echo -e "${YELLOW}→${NC} Installing desktop integration..."
cp "$SCRIPT_DIR/xanadOS-Search-Destroy.desktop" "$APPDIR/xanadOS-Search-Destroy.desktop"
cp "$SCRIPT_DIR/xanadOS-Search-Destroy.desktop" "$APPDIR/usr/share/applications/"
echo -e "${GREEN}✓${NC} Desktop file installed"

# Copy icon files
echo -e "${YELLOW}→${NC} Installing application icons..."
mkdir -p "$APPDIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APPDIR/usr/app/icons"
if [ -f "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy-128.png" ]; then
    cp "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy-128.png" "$APPDIR/xanadOS-Search-Destroy.png"
    cp "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy-128.png" "$APPDIR/usr/share/icons/hicolor/128x128/apps/xanadOS-Search-Destroy.png"
    cp "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy-128.png" "$APPDIR/.DirIcon"
    # Also copy to app/icons for code path resolution (banner icon)
    cp "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy-128.png" "$APPDIR/usr/app/icons/io.github.asafelobotomy.SearchAndDestroy-128.png"
fi
# Copy large PNG icon for splash screen (org.xanados version exists)
if [ -f "$PROJECT_ROOT/packaging/icons/org.xanados.SearchAndDestroy.png" ]; then
    cp "$PROJECT_ROOT/packaging/icons/org.xanados.SearchAndDestroy.png" "$APPDIR/usr/app/icons/io.github.asafelobotomy.SearchAndDestroy.png"
fi
if [ -f "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy.svg" ]; then
    cp "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/xanadOS-Search-Destroy.svg"
    # Also copy to app/icons for code path resolution (system tray icon)
    cp "$PROJECT_ROOT/packaging/icons/io.github.asafelobotomy.SearchAndDestroy.svg" "$APPDIR/usr/app/icons/io.github.asafelobotomy.SearchAndDestroy.svg"
fi
echo -e "${GREEN}✓${NC} Icons installed"

# Bundle ClamAV if available on the system
echo ""
echo -e "${YELLOW}→${NC} Bundling ClamAV..."
if command -v clamscan &> /dev/null; then
    # Copy ClamAV binaries
    for clamav_bin in clamscan clamdscan freshclam clamd; do
        if command -v "$clamav_bin" &> /dev/null; then
            CLAMAV_BIN_PATH=$(which "$clamav_bin")
            cp -L "$CLAMAV_BIN_PATH" "$APPDIR/usr/bin/" 2>/dev/null || true
            echo -e "${CYAN}  Copied $clamav_bin${NC}"
        fi
    done

    # Copy ClamAV libraries
    for lib in $(ldd $(which clamscan) | grep "=>" | awk '{print $3}' | grep -E "libclam|libfreshclam"); do
        if [ -f "$lib" ]; then
            cp -L "$lib" "$APPDIR/usr/lib/"
            echo -e "${CYAN}  Copied $(basename $lib)${NC}"
        fi
    done

    # Copy ClamAV virus definitions if available
    if [ -d "/var/lib/clamav" ]; then
        cp /var/lib/clamav/*.cvd "$APPDIR/usr/share/clamav/" 2>/dev/null || true
        cp /var/lib/clamav/*.cld "$APPDIR/usr/share/clamav/" 2>/dev/null || true
        echo -e "${CYAN}  Copied virus definitions${NC}"
    fi

    # Copy ClamAV configuration
    if [ -f "/etc/clamav/clamd.conf" ]; then
        mkdir -p "$APPDIR/usr/etc/clamav"
        cp /etc/clamav/clamd.conf "$APPDIR/usr/etc/clamav/" 2>/dev/null || true
    fi

    echo -e "${GREEN}✓${NC} ClamAV bundled"
else
    echo -e "${YELLOW}⚠${NC} ClamAV not found on system - AppImage will use system ClamAV if available"
fi

# Bundle RKHunter if available on the system
echo ""
echo -e "${YELLOW}→${NC} Bundling RKHunter..."
if command -v rkhunter &> /dev/null; then
    # Copy RKHunter binary
    RKHUNTER_PATH=$(which rkhunter)
    cp -L "$RKHUNTER_PATH" "$APPDIR/usr/bin/"
    chmod +x "$APPDIR/usr/bin/rkhunter"
    echo -e "${CYAN}  Copied rkhunter binary${NC}"

    # Copy RKHunter data files
    if [ -d "/usr/share/rkhunter" ]; then
        cp -r /usr/share/rkhunter/* "$APPDIR/usr/share/rkhunter/" 2>/dev/null || true
        echo -e "${CYAN}  Copied rkhunter data files${NC}"
    elif [ -d "/var/lib/rkhunter" ]; then
        cp -r /var/lib/rkhunter/* "$APPDIR/usr/share/rkhunter/" 2>/dev/null || true
        echo -e "${CYAN}  Copied rkhunter data files${NC}"
    fi

    # Copy RKHunter configuration
    if [ -f "/etc/rkhunter.conf" ]; then
        mkdir -p "$APPDIR/usr/etc"
        cp /etc/rkhunter.conf "$APPDIR/usr/etc/" 2>/dev/null || true
    fi

    echo -e "${GREEN}✓${NC} RKHunter bundled"
else
    echo -e "${YELLOW}⚠${NC} RKHunter not found on system - AppImage will use system RKHunter if available"
fi

# Strip binaries to reduce size (optional)
echo ""
echo -e "${YELLOW}→${NC} Optimizing AppImage size..."
find "$APPDIR/usr/lib" -name "*.so*" -exec strip {} \; 2>/dev/null || true
find "$APPDIR/usr/bin" -type f -executable -exec strip {} \; 2>/dev/null || true
echo -e "${GREEN}✓${NC} Binaries optimized"

# Build the AppImage
echo ""
echo -e "${YELLOW}→${NC} Building AppImage..."
cd "$BUILD_DIR"

# Set environment for appimagetool
export ARCH="$ARCH"
export VERSION="$VERSION"

# Run appimagetool with extraction mode (works without FUSE)
"$APPIMAGETOOL" --appimage-extract-and-run --comp gzip "$APPDIR" "$OUTPUT_NAME"

if [ -f "$OUTPUT_NAME" ]; then
    chmod +x "$OUTPUT_NAME"

    # Move to releases directory
    mkdir -p "$PROJECT_ROOT/releases/appimage"
    mv "$OUTPUT_NAME" "$PROJECT_ROOT/releases/appimage/"

    # Calculate size
    SIZE=$(du -h "$PROJECT_ROOT/releases/appimage/$OUTPUT_NAME" | cut -f1)

    echo ""
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}  ✓ AppImage built successfully!${NC}"
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}File:${NC} releases/appimage/$OUTPUT_NAME"
    echo -e "${BLUE}Size:${NC} $SIZE"
    echo ""
    echo -e "${CYAN}To run the AppImage:${NC}"
    echo -e "  chmod +x releases/appimage/$OUTPUT_NAME"
    echo -e "  ./releases/appimage/$OUTPUT_NAME"
    echo ""
else
    echo -e "${RED}✗ AppImage build failed${NC}"
    exit 1
fi
