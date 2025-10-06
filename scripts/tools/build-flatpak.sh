#!/bin/bash
#
# Unified Flatpak Build Tool for xanadOS Search & Destroy
# ======================================================
#
# Purpose: Complete Flatpak package building, testing, and validation
# Location: scripts/tools/build-flatpak.sh
# Dependencies: flatpak, flatpak-builder, org.kde.Platform runtime
#
# Features:
# - Automated manifest updating for current version/commit
# - Local build with proper sandboxing
# - Installation and testing
# - Runtime validation
# - Optional cleanup
#
# Usage Examples:
#   ./scripts/tools/build-flatpak.sh --build-only
#   ./scripts/tools/build-flatpak.sh --install --test
#   ./scripts/tools/build-flatpak.sh --full
#   ./scripts/tools/build-flatpak.sh --clean
#

set -e

# Script metadata
SCRIPT_NAME="build-flatpak.sh"
SCRIPT_VERSION="3.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
APP_ID="io.github.asafelobotomy.SearchAndDestroy"
MANIFEST_FILE="packaging/flatpak/${APP_ID}-optimized.yml"
BUILD_DIR="$PROJECT_ROOT/build/xanados-flatpak-build-$$"
REPO_DIR="$PROJECT_ROOT/build/xanados-flatpak-repo-$$"
FLATPAK_FILE="${APP_ID}.flatpak"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Help function
show_help() {
    cat << EOF
🚀 Unified Flatpak Build Tool for xanadOS Search & Destroy v${SCRIPT_VERSION}

USAGE:
    $SCRIPT_NAME [OPTIONS]

OPTIONS:
    --build-only        Build the Flatpak package only (no install/test)
    --install           Install the built package locally
    --test              Run functionality tests on installed package
    --full              Complete workflow: build + install + test
    --clean             Clean build artifacts and uninstall
    --update-manifest   Update manifest with current version/commit
    --verbose           Enable verbose output
    --help              Show this help message

EXAMPLES:
    # Quick build for development
    $SCRIPT_NAME --build-only

    # Complete build and test workflow
    $SCRIPT_NAME --full

    # Update manifest and build
    $SCRIPT_NAME --update-manifest --build-only

    # Clean all artifacts
    $SCRIPT_NAME --clean

REQUIREMENTS:
    - flatpak and flatpak-builder installed
    - org.kde.Platform//6.8 runtime available
    - com.riverbankcomputing.PyQt.BaseApp//6.8 base app available

EOF
}

# Dependency checking
check_dependencies() {
    log_header "🔍 Checking dependencies..."

    local missing_deps=()

    # Check flatpak tools
    if ! command -v flatpak >/dev/null 2>&1; then
        missing_deps+=("flatpak")
    fi

    if ! command -v flatpak-builder >/dev/null 2>&1; then
        missing_deps+=("flatpak-builder")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo "Install with: sudo dnf install flatpak flatpak-builder"
        echo "       or:    sudo apt install flatpak flatpak-builder"
        return 1
    fi

    # Check required runtimes
    log_info "Checking Flatpak runtimes..."
    if ! flatpak list --runtime | grep -q "org.kde.Platform.*6.8"; then
        log_warning "org.kde.Platform//6.8 not found. Installing..."
        flatpak install -y flathub org.kde.Platform//6.8 org.kde.Sdk//6.8
    fi

    if ! flatpak list --app | grep -q "com.riverbankcomputing.PyQt.BaseApp.*6.8"; then
        log_warning "PyQt BaseApp not found. Installing..."
        flatpak install -y flathub com.riverbankcomputing.PyQt.BaseApp//6.8
    fi

    log_success "All dependencies satisfied"
}

# Update manifest with current version and commit
update_manifest() {
    log_header "📝 Updating Flatpak manifest..."

    cd "$PROJECT_ROOT"

    # Get current version and commit
    local VERSION
    VERSION=$(cat VERSION | tr -d '\n')
    local COMMIT_HASH
    COMMIT_HASH=$(git rev-parse HEAD)
    local TAG_NAME="v${VERSION}"

    log_info "Version: $VERSION"
    log_info "Commit: $COMMIT_HASH"
    log_info "Tag: $TAG_NAME"

    # Verify tag exists
    if ! git tag | grep -q "^${TAG_NAME}$"; then
        log_error "Tag $TAG_NAME does not exist. Please create and push the tag first."
        echo "Run: git tag -a $TAG_NAME -m 'Release $VERSION' && git push origin $TAG_NAME"
        return 1
    fi

    # Update manifest
    if [ -f "$MANIFEST_FILE" ]; then
        log_info "Updating manifest: $MANIFEST_FILE"
        # Update only the search-and-destroy module's tag and commit
        sed -i '/- name: search-and-destroy/,/sources:/{
            s/tag: v[0-9]\+\.[0-9]\+\.[0-9]\+/tag: '"$TAG_NAME"'/
        }' "$MANIFEST_FILE"
        sed -i '/- name: search-and-destroy/,/^  - name:/{
            s/commit: [a-f0-9]\{40\}/commit: '"$COMMIT_HASH"'/
        }' "$MANIFEST_FILE"
        log_success "Manifest updated successfully"
    else
        log_error "Manifest file not found: $MANIFEST_FILE"
        return 1
    fi
}

# Build Flatpak package
build_flatpak() {
    log_header "🔨 Building Flatpak package..."

    cd "$PROJECT_ROOT"

    # Clean previous build if requested
    if [ "$CLEAN_BUILD" = "true" ]; then
        log_info "Cleaning previous build artifacts..."
        rm -rf "$BUILD_DIR" "$REPO_DIR" "$FLATPAK_FILE"
    fi

    # Set build options
    local BUILD_OPTS="--force-clean --ccache --keep-build-dirs"
    if [ "$VERBOSE" = "true" ]; then
        BUILD_OPTS="$BUILD_OPTS --verbose"
    fi

    # Build the package
    log_info "Starting Flatpak build process..."
    log_info "Manifest: $MANIFEST_FILE"
    log_info "Build directory: $BUILD_DIR"
    log_info "Repository: $REPO_DIR"

    if flatpak-builder $BUILD_OPTS --repo="$REPO_DIR" "$BUILD_DIR" "$MANIFEST_FILE"; then
        log_success "Flatpak build completed successfully"
    else
        log_error "Flatpak build failed"
        return 1
    fi

    # Export to single file
    log_info "Exporting to single .flatpak file..."
    if flatpak build-export "$REPO_DIR" "$BUILD_DIR"; then
        flatpak build-bundle "$REPO_DIR" "$FLATPAK_FILE" "$APP_ID"
        log_success "Package exported: $FLATPAK_FILE"

        # Show package info
        local SIZE
        SIZE=$(du -h "$FLATPAK_FILE" | cut -f1)
        log_info "Package size: $SIZE"
    else
        log_error "Failed to export package"
        return 1
    fi
}

# Install Flatpak locally
install_flatpak() {
    log_header "📦 Installing Flatpak package locally..."

    cd "$PROJECT_ROOT"

    # Check if already installed
    if flatpak list --app | grep -q "$APP_ID"; then
        log_info "Removing existing installation..."
        flatpak uninstall -y "$APP_ID" || log_warning "Failed to uninstall existing version"
    fi

    # Install from repository
    if [ -d "$REPO_DIR" ]; then
        log_info "Installing from local repository..."
        if flatpak install -y "$REPO_DIR" "$APP_ID"; then
            log_success "Package installed successfully"
        else
            log_error "Installation failed"
            return 1
        fi
    elif [ -f "$FLATPAK_FILE" ]; then
        log_info "Installing from bundle file..."
        if flatpak install -y "$FLATPAK_FILE"; then
            log_success "Package installed successfully"
        else
            log_error "Installation failed"
            return 1
        fi
    else
        log_error "No package found to install. Build first."
        return 1
    fi

    # Verify installation
    if flatpak list --app | grep -q "$APP_ID"; then
        log_success "Installation verified"
        flatpak info "$APP_ID" | head -10
    else
        log_error "Installation verification failed"
        return 1
    fi
}

# Test Flatpak functionality
test_flatpak() {
    log_header "🧪 Testing Flatpak functionality..."

    # Check if installed
    if ! flatpak list --app | grep -q "$APP_ID"; then
        log_error "Package not installed. Install first."
        return 1
    fi

    # Test basic functionality
    log_info "Testing basic launch (version check)..."
    if timeout 10s flatpak run "$APP_ID" --version >/dev/null 2>&1; then
        log_success "Basic launch test passed"
    else
        log_warning "Basic launch test failed or timed out"
    fi

    # Test help output
    log_info "Testing help output..."
    if timeout 10s flatpak run "$APP_ID" --help >/dev/null 2>&1; then
        log_success "Help output test passed"
    else
        log_warning "Help output test failed or timed out"
    fi

    # Show package permissions
    log_info "Package permissions:"
    flatpak info --show-permissions "$APP_ID" | head -20

    log_success "Flatpak testing completed"
}

# Clean build artifacts
clean_artifacts() {
    log_header "🧹 Cleaning build artifacts..."

    cd "$PROJECT_ROOT"

    # Remove build directories
    local items_to_remove=("$BUILD_DIR" "$REPO_DIR" "$FLATPAK_FILE")

    for item in "${items_to_remove[@]}"; do
        if [ -e "$item" ]; then
            log_info "Removing: $item"
            rm -rf "$item"
        fi
    done

    # Uninstall if requested
    if flatpak list --app | grep -q "$APP_ID"; then
        log_info "Uninstalling Flatpak package..."
        flatpak uninstall -y "$APP_ID" || log_warning "Failed to uninstall"
    fi

    log_success "Cleanup completed"
}

# Main execution
main() {
    log_header "🚀 xanadOS Search & Destroy Flatpak Build Tool v${SCRIPT_VERSION}"

    # Navigate to project root
    cd "$PROJECT_ROOT"

    # Verify we're in the right place
    if [ ! -f "app/main.py" ] || [ ! -f "$MANIFEST_FILE" ]; then
        log_error "Not in correct project directory or missing required files"
        log_error "Expected: app/main.py and $MANIFEST_FILE"
        return 1
    fi

    # Parse command line arguments
    local DO_BUILD=false
    local DO_INSTALL=false
    local DO_TEST=false
    local DO_CLEAN=false
    local DO_UPDATE_MANIFEST=false
    local DO_FULL=false
    VERBOSE=false
    CLEAN_BUILD=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-only)
                DO_BUILD=true
                shift
                ;;
            --install)
                DO_INSTALL=true
                shift
                ;;
            --test)
                DO_TEST=true
                shift
                ;;
            --full)
                DO_FULL=true
                shift
                ;;
            --clean)
                DO_CLEAN=true
                shift
                ;;
            --update-manifest)
                DO_UPDATE_MANIFEST=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                return 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                return 1
                ;;
        esac
    done

    # Set defaults if no specific action requested
    if ! $DO_BUILD && ! $DO_INSTALL && ! $DO_TEST && ! $DO_CLEAN && ! $DO_UPDATE_MANIFEST && ! $DO_FULL; then
        DO_FULL=true
    fi

    # Execute requested actions
    if $DO_CLEAN; then
        clean_artifacts
        return 0
    fi

    # Check dependencies unless only cleaning
    check_dependencies

    if $DO_UPDATE_MANIFEST || $DO_FULL; then
        update_manifest
    fi

    if $DO_BUILD || $DO_FULL; then
        build_flatpak
    fi

    if $DO_INSTALL || $DO_FULL; then
        install_flatpak
    fi

    if $DO_TEST || $DO_FULL; then
        test_flatpak
    fi

    log_header "✅ Flatpak build process completed successfully!"

    if [ -f "$FLATPAK_FILE" ]; then
        echo
        log_success "Ready to distribute: $FLATPAK_FILE"
        log_info "Install with: flatpak install $FLATPAK_FILE"
        log_info "Run with: flatpak run $APP_ID"
    fi
}

# Execute main function with all arguments
main "$@"
