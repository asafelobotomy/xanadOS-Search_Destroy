#!/usr/bin/env bash
# Build all distribution packages for xanadOS Search & Destroy
# Outputs: .deb, .rpm, and AppImage

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build/dist"
VERSION=$(cat "$PROJECT_ROOT/VERSION")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create build directory
log_info "Creating build directory: $BUILD_DIR"
mkdir -p "$BUILD_DIR"/{deb,rpm,appimage}

# Function to build Debian package
build_deb() {
    log_info "Building Debian package (.deb)..."
    cd "$PROJECT_ROOT/packaging/debian"

    # Check if dpkg-buildpackage is available
    if ! command -v dpkg-buildpackage &> /dev/null; then
        log_error "dpkg-buildpackage not found. Install: sudo apt install build-essential devscripts"
        return 1
    fi

    # Build package
    dpkg-buildpackage -us -uc -b

    # Move .deb to build directory
    mv ../*.deb "$BUILD_DIR/deb/" 2>/dev/null || true

    # Cleanup
    rm ../*.buildinfo ../*.changes 2>/dev/null || true

    log_info "✅ Debian package built: $BUILD_DIR/deb/"
    cd "$PROJECT_ROOT"
}

# Function to build RPM package
build_rpm() {
    log_info "Building RPM package (.rpm)..."
    cd "$PROJECT_ROOT/packaging/rpm"

    # Check if rpmbuild is available
    if ! command -v rpmbuild &> /dev/null; then
        log_error "rpmbuild not found. Install: sudo dnf install rpm-build rpmdevtools"
        return 1
    fi

    # Setup RPM build tree
    rpmdev-setuptree 2>/dev/null || mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

    # Copy spec file
    cp xanados-search-destroy.spec ~/rpmbuild/SPECS/

    # Create source tarball
    cd "$PROJECT_ROOT"
    tar czf ~/rpmbuild/SOURCES/xanados-search-destroy-${VERSION}.tar.gz \
        --transform "s,^,xanados-search-destroy-${VERSION}/," \
        --exclude='.git' \
        --exclude='build' \
        --exclude='archive' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        .

    # Build RPM
    rpmbuild -ba ~/rpmbuild/SPECS/xanados-search-destroy.spec

    # Move .rpm to build directory
    mv ~/rpmbuild/RPMS/x86_64/*.rpm "$BUILD_DIR/rpm/" 2>/dev/null || true
    mv ~/rpmbuild/RPMS/noarch/*.rpm "$BUILD_DIR/rpm/" 2>/dev/null || true

    log_info "✅ RPM package built: $BUILD_DIR/rpm/"
    cd "$PROJECT_ROOT"
}

# Function to build AppImage
build_appimage() {
    log_info "Building AppImage..."
    cd "$PROJECT_ROOT/build/appimage"

    # Check if appimagetool is available
    if ! command -v appimagetool &> /dev/null; then
        log_warn "appimagetool not found. Downloading..."
        wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
            -O appimagetool
        chmod +x appimagetool
        APPIMAGETOOL="./appimagetool"
    else
        APPIMAGETOOL="appimagetool"
    fi

    # Run build script
    if [ -f "build-appimage.sh" ]; then
        bash build-appimage.sh

        # Move AppImage to build directory
        mv *.AppImage "$BUILD_DIR/appimage/" 2>/dev/null || true

        log_info "✅ AppImage built: $BUILD_DIR/appimage/"
    else
        log_error "build-appimage.sh not found"
        return 1
    fi

    cd "$PROJECT_ROOT"
}

# Main build process
log_info "🚀 Building all packages for version $VERSION"
echo ""

# Track build status
DEB_STATUS="⏭️ SKIPPED"
RPM_STATUS="⏭️ SKIPPED"
APPIMAGE_STATUS="⏭️ SKIPPED"

# Build Debian package
if build_deb; then
    DEB_STATUS="✅ SUCCESS"
else
    DEB_STATUS="❌ FAILED"
fi
echo ""

# Build RPM package
if build_rpm; then
    RPM_STATUS="✅ SUCCESS"
else
    RPM_STATUS="❌ FAILED"
fi
echo ""

# Build AppImage
if build_appimage; then
    APPIMAGE_STATUS="✅ SUCCESS"
else
    APPIMAGE_STATUS="❌ FAILED"
fi
echo ""

# Summary
log_info "📦 Build Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Debian (.deb):  $DEB_STATUS"
echo -e "RPM (.rpm):     $RPM_STATUS"
echo -e "AppImage:       $APPIMAGE_STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_info "Output directory: $BUILD_DIR"
echo ""

# List built packages
if [ "$(ls -A $BUILD_DIR/deb 2>/dev/null)" ]; then
    log_info "Debian packages:"
    ls -lh "$BUILD_DIR/deb/"
fi

if [ "$(ls -A $BUILD_DIR/rpm 2>/dev/null)" ]; then
    log_info "RPM packages:"
    ls -lh "$BUILD_DIR/rpm/"
fi

if [ "$(ls -A $BUILD_DIR/appimage 2>/dev/null)" ]; then
    log_info "AppImage packages:"
    ls -lh "$BUILD_DIR/appimage/"
fi

log_info "✨ Build process complete!"
