#!/usr/bin/env bash
# Create GitHub release with built packages
# Requires: gh CLI (GitHub CLI)

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

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) not found"
    log_info "Install: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    log_error "Not authenticated with GitHub"
    log_info "Run: gh auth login"
    exit 1
fi

# Extract release notes from CHANGELOG
extract_release_notes() {
    local version="$1"
    local changelog="$PROJECT_ROOT/CHANGELOG.md"

    if [ ! -f "$changelog" ]; then
        echo "Release v$version"
        return
    fi

    # Extract section between [version] and next [version] or EOF
    awk -v ver="$version" '
        /^## \['"$version"'\]/ { found=1; next }
        found && /^## \[/ { exit }
        found { print }
    ' "$changelog"
}

# Main release process
log_info "🚀 Creating GitHub release for v$VERSION"
echo ""

# Get release notes
RELEASE_NOTES=$(extract_release_notes "$VERSION")

if [ -z "$RELEASE_NOTES" ]; then
    log_warn "No release notes found in CHANGELOG.md"
    RELEASE_NOTES="Release v$VERSION

See [CHANGELOG.md](CHANGELOG.md) for details."
fi

# Check if tag exists
if ! git rev-parse "v$VERSION" &> /dev/null; then
    log_error "Git tag v$VERSION does not exist"
    log_info "Create tag first: git tag -a v$VERSION -m 'Release v$VERSION'"
    exit 1
fi

# Check if release already exists
if gh release view "v$VERSION" &> /dev/null; then
    log_warn "Release v$VERSION already exists"
    read -p "Delete and recreate? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting existing release..."
        gh release delete "v$VERSION" -y
    else
        log_error "Cancelled"
        exit 1
    fi
fi

# Create release
log_info "Creating release v$VERSION..."
gh release create "v$VERSION" \
    --title "v$VERSION" \
    --notes "$RELEASE_NOTES" \
    --draft \
    --generate-notes

# Upload assets
log_info "Uploading release assets..."

# Upload Debian packages
if [ -d "$BUILD_DIR/deb" ] && [ "$(ls -A $BUILD_DIR/deb)" ]; then
    log_info "Uploading .deb packages..."
    gh release upload "v$VERSION" "$BUILD_DIR/deb"/*.deb
fi

# Upload RPM packages
if [ -d "$BUILD_DIR/rpm" ] && [ "$(ls -A $BUILD_DIR/rpm)" ]; then
    log_info "Uploading .rpm packages..."
    gh release upload "v$VERSION" "$BUILD_DIR/rpm"/*.rpm
fi

# Upload AppImage
if [ -d "$BUILD_DIR/appimage" ] && [ "$(ls -A $BUILD_DIR/appimage)" ]; then
    log_info "Uploading AppImage..."
    gh release upload "v$VERSION" "$BUILD_DIR/appimage"/*.AppImage
fi

# Generate checksums
log_info "Generating checksums..."
cd "$BUILD_DIR"
find . -type f \( -name "*.deb" -o -name "*.rpm" -o -name "*.AppImage" \) -exec sha256sum {} \; > SHA256SUMS
gh release upload "v$VERSION" SHA256SUMS
cd "$PROJECT_ROOT"

# Summary
echo ""
log_info "✅ GitHub release created successfully!"
log_info "Release URL: $(gh release view v$VERSION --json url -q .url)"
echo ""
log_warn "Release is currently in DRAFT mode"
log_info "To publish: gh release edit v$VERSION --draft=false"
log_info "Or visit GitHub and publish manually"
