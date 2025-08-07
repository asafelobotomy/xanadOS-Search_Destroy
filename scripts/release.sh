#!/bin/bash
# Release script for xanadOS Search & Destroy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if version is provided
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <version> [--dry-run]"
fi

VERSION=$1
DRY_RUN=""

if [ "$2" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
    log_warning "Running in dry-run mode"
fi

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    log_error "Invalid version format. Use semantic versioning (e.g., 2.1.0)"
fi

log_info "Starting release process for version $VERSION"

# Check if we're on develop branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "develop" ]; then
    log_error "Release must be started from develop branch. Current branch: $CURRENT_BRANCH"
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    log_error "Working directory is not clean. Please commit or stash changes."
fi

# Pull latest changes
log_info "Pulling latest changes from develop..."
git pull origin develop

# Create release branch
RELEASE_BRANCH="release/$VERSION"
log_info "Creating release branch: $RELEASE_BRANCH"
if [ -z "$DRY_RUN" ]; then
    git checkout -b "$RELEASE_BRANCH"
fi

# Update version file
log_info "Updating VERSION file..."
if [ -z "$DRY_RUN" ]; then
    echo "$VERSION" > VERSION
    git add VERSION
fi

# Update changelog
log_info "Please update CHANGELOG.md with release notes for version $VERSION"
read -p "Press Enter when you've updated the CHANGELOG.md file..."

if [ -z "$DRY_RUN" ]; then
    git add CHANGELOG.md
    git commit -m "chore(release): bump version to $VERSION"
fi

# Run tests (if test suite exists)
if [ -f "tests/run_tests.py" ]; then
    log_info "Running tests..."
    python3 tests/run_tests.py
    log_success "Tests passed"
fi

# Build documentation (if docs exist)
if [ -f "docs/build.sh" ]; then
    log_info "Building documentation..."
    cd docs && ./build.sh && cd ..
    log_success "Documentation built"
fi

# Merge to master
log_info "Merging to master..."
if [ -z "$DRY_RUN" ]; then
    git checkout master
    git pull origin master
    git merge --no-ff "$RELEASE_BRANCH" -m "chore(release): merge release $VERSION"
fi

# Create tag
log_info "Creating tag v$VERSION..."
if [ -z "$DRY_RUN" ]; then
    git tag -a "v$VERSION" -m "Release version $VERSION"
fi

# Push to remote
if [ -z "$DRY_RUN" ]; then
    log_info "Pushing to remote..."
    git push origin master
    git push origin "v$VERSION"
fi

# Merge back to develop
log_info "Merging back to develop..."
if [ -z "$DRY_RUN" ]; then
    git checkout develop
    git merge master
    git push origin develop
fi

# Cleanup
log_info "Cleaning up release branch..."
if [ -z "$DRY_RUN" ]; then
    git branch -d "$RELEASE_BRANCH"
fi

log_success "Release $VERSION completed successfully!"
log_info "Release artifacts:"
log_info "  - Git tag: v$VERSION"
log_info "  - Master branch updated"
log_info "  - Develop branch updated"

if [ -z "$DRY_RUN" ]; then
    log_info "Next steps:"
    log_info "  1. Create GitHub release with tag v$VERSION"
    log_info "  2. Build and distribute packages"
    log_info "  3. Update documentation sites"
    log_info "  4. Announce release"
fi
