#!/bin/bash

# Tool: generate-docs.sh
# Purpose: Automated documentation generation and maintenance
# Usage: ./generate-docs.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="generate-docs"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Automated documentation generation and maintenance for repositories"

# Configuration
LOG_DIR="logs/toolshed"
VERBOSE=false
DRY_RUN=false
OUTPUT_DIR="docs"
FORCE_OVERWRITE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_DIR/generate-docs.log"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$LOG_DIR/generate-docs.log"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_DIR/generate-docs.log"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOG_DIR/generate-docs.log"
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

Automated documentation generation and maintenance

This tool generates and maintains:
- API documentation from code comments
- README files with current project status
- Table of contents for documentation directories
- Cross-reference links between documents
- Changelog updates from git history

Options:
    -v, --verbose           Enable verbose logging
    -d, --dry-run          Show what would be done without making changes
    -o, --output DIR       Output directory (default: docs)
    -f, --force            Overwrite existing files without prompt
    -h, --help             Show this help message

Examples:
    $0                     # Generate all documentation
    $0 --dry-run           # Preview documentation changes
    $0 -o custom-docs      # Generate docs in custom directory

EOF
}

# Initialize logging
setup_logging() {
    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Logging enabled: $LOG_DIR/generate-docs.log"
    fi
}

# Generate API documentation from comments
generate_api_docs() {
    log_info "Generating API documentation..."
    
    local api_files=$(find . -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.sh" | grep -v node_modules | grep -v .git)
    
    if [[ -z "$api_files" ]]; then
        log_warning "No API files found for documentation generation"
        return 0
    fi
    
    local output_file="$OUTPUT_DIR/api/README.md"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would generate API docs at: $output_file"
        return 0
    fi
    
    mkdir -p "$(dirname "$output_file")"
    
    cat > "$output_file" << 'EOF'
# API Documentation

This directory contains automatically generated API documentation.

## Available APIs

EOF
    
    while IFS= read -r file; do
        local basename=$(basename "$file")
        echo "- [$basename]($file) - $(head -n 5 "$file" | grep -o "Purpose:.*" || echo "API interface")" >> "$output_file"
    done <<< "$api_files"
    
    log_success "Generated API documentation"
}

# Generate README with project status
generate_readme() {
    log_info "Generating README with current project status..."
    
    local readme_file="README.md"
    
    if [[ -f "$readme_file" ]] && [[ "$FORCE_OVERWRITE" != "true" ]]; then
        log_warning "README.md exists - use --force to overwrite"
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would generate/update README.md"
        return 0
    fi
    
    # Get project info
    local project_name=$(basename "$(pwd)")
    local git_remote=$(git remote get-url origin 2>/dev/null || echo "No remote configured")
    local last_commit=$(git log -1 --format="%h - %s (%ar)" 2>/dev/null || echo "No commits")
    local file_count=$(find . -type f -not -path "./.git/*" -not -path "./node_modules/*" | wc -l)
    
    cat > "$readme_file" << EOF
# $project_name

## Project Status

- **Last Updated**: $(date '+%Y-%m-%d %H:%M:%S')
- **Total Files**: $file_count
- **Last Commit**: $last_commit
- **Repository**: $git_remote

## Documentation

- [API Documentation](docs/api/) - Interface specifications
- [Guides](docs/guides/) - How-to documentation
- [Reference](docs/reference/) - Quick lookup materials

## Quick Start

\`\`\`bash
# Clone repository
git clone $git_remote

# Install dependencies (if applicable)
npm install  # or pip install -r requirements.txt

# Run validation
./scripts/validation/validate-structure.sh
\`\`\`

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

EOF
    
    log_success "Generated README.md"
}

# Generate table of contents for directories
generate_toc() {
    log_info "Generating table of contents..."
    
    local doc_dirs=("docs/guides" "docs/tutorials" "docs/reference")
    
    for dir in "${doc_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            continue
        fi
        
        local toc_file="$dir/README.md"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "Would generate TOC at: $toc_file"
            continue
        fi
        
        if [[ -f "$toc_file" ]]; then
            log_info "TOC already exists at $toc_file"
            continue
        fi
        
        local dir_name=$(basename "$dir")
        
        cat > "$toc_file" << EOF
# $dir_name

## Available Documents

EOF
        
        find "$dir" -name "*.md" -not -name "README.md" | sort | while read -r file; do
            local basename=$(basename "$file" .md)
            local title=$(head -n 1 "$file" | sed 's/^# //' || echo "$basename")
            echo "- [$title]($basename.md)" >> "$toc_file"
        done
        
        log_success "Generated TOC for $dir"
    done
}

# Update changelog from git history
update_changelog() {
    log_info "Updating changelog from git history..."
    
    local changelog_file="CHANGELOG.md"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Would update CHANGELOG.md"
        return 0
    fi
    
    if [[ ! -f "$changelog_file" ]]; then
        cat > "$changelog_file" << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

EOF
    fi
    
    # Get recent commits
    local recent_commits=$(git log --oneline --since="1 week ago" 2>/dev/null || echo "")
    
    if [[ -n "$recent_commits" ]]; then
        # Backup existing changelog
        cp "$changelog_file" "${changelog_file}.backup"
        
        # Insert recent changes
        sed -i '/^# Changelog/a\\n## Recent Changes (Generated)\n' "$changelog_file"
        
        while IFS= read -r commit; do
            echo "- $commit" | sed -i '/^## Recent Changes/r /dev/stdin' "$changelog_file"
        done <<< "$recent_commits"
        
        log_success "Updated changelog with recent commits"
    else
        log_warning "No recent commits to add to changelog"
    fi
}

# Main execution function
main() {
    setup_logging
    
    log_info "Starting documentation generation..."
    log_info "Output directory: $OUTPUT_DIR"
    
    # Create output directory structure
    if [[ "$DRY_RUN" != "true" ]]; then
        mkdir -p "$OUTPUT_DIR"/{api,guides,tutorials,reference}
    fi
    
    # Generate different types of documentation
    generate_api_docs
    generate_readme
    generate_toc
    update_changelog
    
    log_success "Documentation generation complete!"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "This was a dry run - no files were modified"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_OVERWRITE=true
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
