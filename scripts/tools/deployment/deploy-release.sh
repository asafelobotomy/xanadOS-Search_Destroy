#!/bin/bash

# Tool: deploy-release.sh
# Purpose: Automated release deployment with validation
# Usage: ./deploy-release.sh [options]

set -euo pipefail

# Configuration
RELEASE_BRANCH="main"
VERSION=""
DRY_RUN=false
SKIP_TESTS=false
AUTO_TAG=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

Automated release deployment with validation

Options:
    -v, --version VERSION   Release version (e.g., 1.0.0)
    -b, --branch BRANCH     Release branch (default: main)
    -d, --dry-run          Show what would be done without executing
    --skip-tests           Skip test validation before release
    --no-tag              Don't create git tag
    -h, --help            Show this help message

Examples:
    $0 -v 1.2.0           # Deploy version 1.2.0
    $0 -v 1.2.0 --dry-run # Preview release deployment

EOF
}

# Validate release prerequisites
validate_prerequisites() {
    log_info "Validating release prerequisites..."
    
    # Check git status
    if [[ -n "$(git status --porcelain)" ]]; then
        log_error "Repository has uncommitted changes"
        return 1
    fi
    
    # Check current branch
    local current_branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "$RELEASE_BRANCH" ]]; then
        log_error "Must be on release branch: $RELEASE_BRANCH (currently on: $current_branch)"
        return 1
    fi
    
    # Check if version is specified
    if [[ -z "$VERSION" ]]; then
        log_error "Version must be specified with -v/--version"
        return 1
    fi
    
    # Validate version format
    if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Version must be in format X.Y.Z (e.g., 1.0.0)"
        return 1
    fi
    
    log_success "Prerequisites validated"
}

# Run tests if not skipped
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Skipping test validation"
        return 0
    fi
    
    log_info "Running test validation..."
    
    # Run linting
    if command -v npm >/dev/null 2>&1 && [[ -f "package.json" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "Would run: npm run lint"
        else
            npm run lint || { log_error "Linting failed"; return 1; }
        fi
    fi
    
    # Run structure validation
    if [[ -x "scripts/validation/verify-structure.sh" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "Would run: scripts/validation/verify-structure.sh"
        else
            ./scripts/validation/verify-structure.sh || { log_error "Structure validation failed"; return 1; }
        fi
    fi
    
    log_success "Tests passed"
}

# Update version files
update_version() {
    log_info "Updating version to $VERSION..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would update version files with: $VERSION"
        return 0
    fi
    
    # Update package.json if it exists
    if [[ -f "package.json" ]]; then
        sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json
        log_success "Updated package.json version"
    fi
    
    # Update VERSION file if it exists
    if [[ -f "VERSION" ]]; then
        echo "$VERSION" > VERSION
        log_success "Updated VERSION file"
    fi
    
    # Update CHANGELOG.md
    if [[ -f "CHANGELOG.md" ]]; then
        local release_date
        release_date=$(date '+%Y-%m-%d')
        sed -i "1a\\## [$VERSION] - $release_date\\n" CHANGELOG.md
        log_success "Updated CHANGELOG.md"
    fi
}

# Create git tag
create_tag() {
    if [[ "$AUTO_TAG" != "true" ]]; then
        log_info "Skipping tag creation"
        return 0
    fi
    
    log_info "Creating git tag: v$VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would create tag: v$VERSION"
        return 0
    fi
    
    git add . || true
    git commit -m "chore: release version $VERSION" || log_warning "No changes to commit"
    git tag -a "v$VERSION" -m "Release version $VERSION"
    
    log_success "Created tag: v$VERSION"
}

# Deploy release
deploy_release() {
    log_info "Deploying release..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would push changes and tags to origin"
        return 0
    fi
    
    # Push changes and tags
    git push origin "$RELEASE_BRANCH"
    if [[ "$AUTO_TAG" == "true" ]]; then
        git push origin "v$VERSION"
    fi
    
    log_success "Release deployed to origin"
}

# Main execution
main() {
    log_info "Starting release deployment for version: $VERSION"
    
    validate_prerequisites
    run_tests
    update_version
    create_tag
    deploy_release
    
    log_success "Release $VERSION deployed successfully!"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "This was a dry run - no changes were made"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -b|--branch)
            RELEASE_BRANCH="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --no-tag)
            AUTO_TAG=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
