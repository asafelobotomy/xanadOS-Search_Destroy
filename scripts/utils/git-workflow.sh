#!/bin/bash

# Git Workflow Helper Script
# Implements industry-standard branching strategy for the GitHub Copilot Enhancement Framework

set -e

# Configuration
DEFAULT_BRANCH="main"
DEVELOP_BRANCH="develop"
VERSION_FILE="VERSION"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
}

# Get current branch
get_current_branch() {
    git branch --show-current
}

# Check if branch exists
branch_exists() {
    git show-ref --verify --quiet refs/heads/"$1"
}

# Create feature branch
create_feature_branch() {
    local feature_name="$1"

    if [ -z "$feature_name" ]; then
        print_error "Feature name is required"
        echo "Usage: $0 feature <feature-name>"
        exit 1
    fi

    local branch_name="feature/$feature_name"

    print_status "Creating feature branch: $branch_name"

    # Ensure we're on main and it's up to date
    git checkout "$DEFAULT_BRANCH"
    git pull origin "$DEFAULT_BRANCH"

    # Create and switch to feature branch
    if branch_exists "$branch_name"; then
        print_warning "Branch $branch_name already exists, switching to it"
        git checkout "$branch_name"
    else
        git checkout -b "$branch_name"
        print_success "Created and switched to $branch_name"
    fi

    # Set up tracking
    git push -u origin "$branch_name" || true
}

# Create hotfix branch
create_hotfix_branch() {
    local hotfix_name="$1"

    if [ -z "$hotfix_name" ]; then
        print_error "Hotfix name is required"
        echo "Usage: $0 hotfix <hotfix-name>"
        exit 1
    fi

    local branch_name="hotfix/$hotfix_name"

    print_status "Creating hotfix branch: $branch_name"

    # Ensure we're on main and it's up to date
    git checkout "$DEFAULT_BRANCH"
    git pull origin "$DEFAULT_BRANCH"

    # Create and switch to hotfix branch
    if branch_exists "$branch_name"; then
        print_warning "Branch $branch_name already exists, switching to it"
        git checkout "$branch_name"
    else
        git checkout -b "$branch_name"
        print_success "Created and switched to $branch_name"
    fi

    # Set up tracking
    git push -u origin "$branch_name" || true
}

# Create release branch
create_release_branch() {
    local version="$1"

    if [ -z "$version" ]; then
        print_error "Version is required"
        echo "Usage: $0 release <version>"
        echo "Example: $0 release 1.2.0"
        exit 1
    fi

    local branch_name="release/v$version"

    print_status "Creating release branch: $branch_name"

    # Ensure we're on develop or main
    local current_branch=$(get_current_branch)
    if [[ "$current_branch" != "$DEFAULT_BRANCH" && "$current_branch" != "$DEVELOP_BRANCH" ]]; then
        print_warning "Switching to $DEFAULT_BRANCH for release"
        git checkout "$DEFAULT_BRANCH"
        git pull origin "$DEFAULT_BRANCH"
    fi

    # Create and switch to release branch
    if branch_exists "$branch_name"; then
        print_warning "Branch $branch_name already exists, switching to it"
        git checkout "$branch_name"
    else
        git checkout -b "$branch_name"

        # Update version file
        if [ -f "$VERSION_FILE" ]; then
            sed -i "s/VERSION_MAJOR=.*/VERSION_MAJOR=$(echo $version | cut -d. -f1)/" "$VERSION_FILE"
            sed -i "s/VERSION_MINOR=.*/VERSION_MINOR=$(echo $version | cut -d. -f2)/" "$VERSION_FILE"
            sed -i "s/VERSION_PATCH=.*/VERSION_PATCH=$(echo $version | cut -d. -f3)/" "$VERSION_FILE"

            git add "$VERSION_FILE"
            git commit -m "chore: bump version to $version"
        fi

        print_success "Created and switched to $branch_name"
    fi

    # Set up tracking
    git push -u origin "$branch_name" || true
}

# Finish feature branch
finish_feature() {
    local current_branch=$(get_current_branch)

    if [[ ! "$current_branch" =~ ^feature/ ]]; then
        print_error "Not on a feature branch"
        exit 1
    fi

    print_status "Finishing feature branch: $current_branch"

    # Ensure everything is committed
    if ! git diff-index --quiet HEAD --; then
        print_error "You have uncommitted changes. Please commit or stash them first."
        exit 1
    fi

    # Push current branch
    git push origin "$current_branch"

    # Switch to main and update
    git checkout "$DEFAULT_BRANCH"
    git pull origin "$DEFAULT_BRANCH"

    print_success "Feature branch $current_branch is ready for PR"
    print_status "Create a pull request from $current_branch to $DEFAULT_BRANCH"
}

# Finish release
finish_release() {
    local current_branch=$(get_current_branch)

    if [[ ! "$current_branch" =~ ^release/ ]]; then
        print_error "Not on a release branch"
        exit 1
    fi

    # Extract version from branch name
    local version=$(echo "$current_branch" | sed 's/release\/v//')

    print_status "Finishing release: $current_branch (v$version)"

    # Ensure everything is committed
    if ! git diff-index --quiet HEAD --; then
        print_error "You have uncommitted changes. Please commit or stash them first."
        exit 1
    fi

    # Push release branch
    git push origin "$current_branch"

    # Merge to main
    git checkout "$DEFAULT_BRANCH"
    git pull origin "$DEFAULT_BRANCH"
    git merge --no-ff "$current_branch" -m "chore: release v$version"

    # Create tag
    git tag -a "v$version" -m "Release v$version"

    # Push main and tags
    git push origin "$DEFAULT_BRANCH"
    git push origin "v$version"

    # Clean up release branch
    git branch -d "$current_branch"
    git push origin --delete "$current_branch"

    print_success "Release v$version completed and tagged"
}

# Show current status
show_status() {
    print_status "Git Workflow Status"
    echo ""
    echo "Current branch: $(get_current_branch)"
    echo "Repository status:"
    git status --short
    echo ""
    echo "Recent commits:"
    git log --oneline -5
    echo ""
    echo "Available branches:"
    git branch -a
}

# Main script logic
case "$1" in
    "feature")
        check_git_repo
        create_feature_branch "$2"
        ;;
    "hotfix")
        check_git_repo
        create_hotfix_branch "$2"
        ;;
    "release")
        check_git_repo
        create_release_branch "$2"
        ;;
    "finish")
        check_git_repo
        case "$2" in
            "feature")
                finish_feature
                ;;
            "release")
                finish_release
                ;;
            *)
                print_error "Unknown finish type: $2"
                echo "Usage: $0 finish [feature|release]"
                exit 1
                ;;
        esac
        ;;
    "status")
        check_git_repo
        show_status
        ;;
    *)
        echo "Git Workflow Helper for GitHub Copilot Enhancement Framework"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  feature <name>     Create a new feature branch"
        echo "  hotfix <name>      Create a new hotfix branch"
        echo "  release <version>  Create a new release branch"
        echo "  finish feature     Finish current feature branch"
        echo "  finish release     Finish current release branch"
        echo "  status             Show repository status"
        echo ""
        echo "Examples:"
        echo "  $0 feature user-authentication"
        echo "  $0 hotfix critical-security-fix"
        echo "  $0 release 1.2.0"
        echo "  $0 finish feature"
        echo "  $0 finish release"
        echo "  $0 status"
        exit 1
        ;;
esac
