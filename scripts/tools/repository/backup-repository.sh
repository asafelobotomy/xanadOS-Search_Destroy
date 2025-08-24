#!/bin/bash

# Tool: backup-repository.sh
# Purpose: Create comprehensive repository backups with metadata
# Usage: ./backup-repository.sh [options]

set -euo pipefail

# Configuration
BACKUP_DIR="backups"
VERBOSE=false
INCLUDE_GIT=true
COMPRESS=true
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

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

Create comprehensive repository backups with metadata

Options:
    -d, --backup-dir DIR   Backup directory (default: backups)
    -v, --verbose          Enable verbose output
    --no-git              Exclude .git directory from backup
    --no-compress         Don't compress the backup
    -h, --help            Show this help message

Examples:
    $0                    # Create compressed backup with git history
    $0 --no-git           # Backup without git history
    $0 -d /tmp/backups    # Backup to custom directory

EOF
}

# Create repository backup
create_backup() {
    local repo_name
    repo_name=$(basename "$(pwd)")
    local backup_name="${repo_name}_backup_${TIMESTAMP}"
    local backup_path="$BACKUP_DIR/$backup_name"

    log_info "Creating backup: $backup_name"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Create temporary backup directory
    mkdir -p "$backup_path"

    # Copy repository contents
    log_info "Copying repository contents..."

    if [[ "$INCLUDE_GIT" == "true" ]]; then
        cp -r . "$backup_path/" 2>/dev/null || log_warning "Some files could not be copied"
    else
        rsync -av --exclude='.git' . "$backup_path/" || log_warning "Some files could not be copied"
    fi

    # Create backup metadata
    cat > "$backup_path/BACKUP_INFO.md" << EOF
# Backup Information

- **Created**: $(date)
- **Repository**: $repo_name
- **Git Included**: $INCLUDE_GIT
- **Backup Size**: $(du -sh "$backup_path" | cut -f1)
- **Git Commit**: $(git rev-parse HEAD 2>/dev/null || echo "No git repository")
- **Git Branch**: $(git branch --show-current 2>/dev/null || echo "No git repository")

## Contents

$(find "$backup_path" -type f | wc -l) files backed up
$(find "$backup_path" -type d | wc -l) directories backed up

EOF

    # Compress if requested
    if [[ "$COMPRESS" == "true" ]]; then
        log_info "Compressing backup..."
        cd "$BACKUP_DIR"
        tar -czf "${backup_name}.tar.gz" "$backup_name"
        rm -rf "$backup_name"
        backup_path="${backup_path}.tar.gz"
        cd - > /dev/null
    fi

    log_success "Backup created: $backup_path"
    log_info "Backup size: $(du -sh "$backup_path" | cut -f1)"
}

# Main execution
main() {
    log_info "Starting repository backup..."

    create_backup

    log_success "Repository backup complete!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-git)
            INCLUDE_GIT=false
            shift
            ;;
        --no-compress)
            COMPRESS=false
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
