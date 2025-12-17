#!/usr/bin/env bash
# Automated version bumping script for xanadOS Search & Destroy
# Usage: ./bump_version.sh [major|minor|patch]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION_FILE="$PROJECT_ROOT/VERSION"
CHANGELOG="$PROJECT_ROOT/CHANGELOG.md"
PYPROJECT="$PROJECT_ROOT/pyproject.toml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if version type is provided
if [ $# -ne 1 ]; then
    log_error "Usage: $0 [major|minor|patch]"
    log_info "Example: $0 patch  # 0.3.0 -> 0.3.1"
    log_info "         $0 minor  # 0.3.0 -> 0.4.0"
    log_info "         $0 major  # 0.3.0 -> 1.0.0"
    exit 1
fi

BUMP_TYPE="$1"

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    log_error "Invalid bump type: $BUMP_TYPE"
    log_info "Must be one of: major, minor, patch"
    exit 1
fi

# Read current version
if [ ! -f "$VERSION_FILE" ]; then
    log_error "VERSION file not found at $VERSION_FILE"
    exit 1
fi

CURRENT_VERSION=$(cat "$VERSION_FILE")
log_info "Current version: $CURRENT_VERSION"

# Parse version components
if [[ $CURRENT_VERSION =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-.*)?$ ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    SUFFIX="${BASH_REMATCH[4]}"
else
    log_error "Invalid version format: $CURRENT_VERSION"
    exit 1
fi

# Calculate new version
case "$BUMP_TYPE" in
    major)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_MINOR=0
        NEW_PATCH=0
        ;;
    minor)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$((MINOR + 1))
        NEW_PATCH=0
        ;;
    patch)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
log_info "New version: $NEW_VERSION"

# Confirm before proceeding
read -p "Bump version from $CURRENT_VERSION to $NEW_VERSION? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Version bump cancelled"
    exit 0
fi

# Update VERSION file
log_info "Updating VERSION file..."
echo "$NEW_VERSION" > "$VERSION_FILE"

# Update pyproject.toml
log_info "Updating pyproject.toml..."
sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT"

# Update CHANGELOG.md
log_info "Updating CHANGELOG.md..."
TODAY=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [$NEW_VERSION] - $TODAY

### Added
-

### Changed
- Version bump to $NEW_VERSION

### Fixed
-

### Security
-
"

# Insert new version entry after the "## [Unreleased]" line
if grep -q "## \[Unreleased\]" "$CHANGELOG"; then
    # Create temporary file with new entry
    awk -v entry="$CHANGELOG_ENTRY" '
        /## \[Unreleased\]/ {
            print $0
            print ""
            print entry
            next
        }
        { print }
    ' "$CHANGELOG" > "$CHANGELOG.tmp"
    mv "$CHANGELOG.tmp" "$CHANGELOG"
else
    log_warn "No '## [Unreleased]' section found in CHANGELOG.md"
    log_warn "Please manually add the changelog entry"
fi

# Git operations
log_info "Staging changes..."
git add "$VERSION_FILE" "$PYPROJECT" "$CHANGELOG"

log_info "Creating commit..."
git commit -m "chore: bump version to $NEW_VERSION

- Updated VERSION file
- Updated pyproject.toml
- Updated CHANGELOG.md with release notes

Signed-off-by: $(git config user.name) <$(git config user.email)>"

log_info "Creating git tag..."
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION

See CHANGELOG.md for details."

# Summary
log_info "✅ Version bump complete!"
echo ""
log_info "Summary:"
log_info "  Old version: $CURRENT_VERSION"
log_info "  New version: $NEW_VERSION"
log_info "  Git tag: v$NEW_VERSION"
echo ""
log_warn "Next steps:"
log_info "  1. Review the changes: git show HEAD"
log_info "  2. Edit CHANGELOG.md to add detailed release notes"
log_info "  3. Push changes: git push origin master --tags"
log_info "  4. Build packages: ./scripts/deployment/build_all.sh"
log_info "  5. Create GitHub release"
