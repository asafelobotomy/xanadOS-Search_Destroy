#!/bin/bash

# Tool: quick-setup.sh
# Purpose: Quick setup script for VS Code integration
# Usage: curl -sSL <url> | bash -s -- [options]

set -euo pipefail

# Configuration
REPO_URL="https://github.com/asafelobotomy/agent-instructions-co-pilot"
TARGET_DIR="${1:-copilot-enhancement}"
ESSENTIAL_ONLY="${2:-false}"

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

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --essential-only)
            ESSENTIAL_ONLY=true
            shift
            ;;
        --target-dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        --help)
            cat << EOF
Usage: $0 [options]

Options:
    --essential-only    Copy only essential files to current directory
    --target-dir DIR    Target directory (default: copilot-enhancement)
    --help             Show this help message

Examples:
    # Full setup
    curl -sSL <url> | bash

    # Essential files only to current directory
    curl -sSL <url> | bash -s -- --essential-only

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main setup function
setup_copilot_enhancement() {
    log_info "Setting up GitHub Copilot Enhancement Framework..."
    
    if [[ "$ESSENTIAL_ONLY" == "true" ]]; then
        setup_essential_files
    else
        setup_full_repository
    fi
    
    setup_vscode_integration
    
    log_success "Setup complete!"
    log_info "Next steps:"
    echo "  1. Open VS Code in the directory"
    echo "  2. Accept the workspace recommendations when prompted"
    echo "  3. Navigate to .github/chatmodes/ and try a chatmode"
    echo "  4. Copy any .chatmode.md content to GitHub Copilot Chat"
}

# Setup essential files only
setup_essential_files() {
    log_info "Copying essential GitHub Copilot files..."
    
    # Create essential directories
    mkdir -p .github/{chatmodes,prompts,instructions}
    mkdir -p scripts/validation
    
    # Download essential chatmodes
    local chatmodes=("architect" "elite-engineer" "security" "testing" "documentation")
    for mode in "${chatmodes[@]}"; do
        curl -sSL "$REPO_URL/raw/main/.github/chatmodes/${mode}.chatmode.md" \
            -o ".github/chatmodes/${mode}.chatmode.md" 2>/dev/null || log_warning "Could not download ${mode}.chatmode.md"
    done
    
    # Download essential prompts
    local prompts=("security-review" "code-refactoring" "api-design")
    for prompt in "${prompts[@]}"; do
        curl -sSL "$REPO_URL/raw/main/.github/prompts/${prompt}.prompt.md" \
            -o ".github/prompts/${prompt}.prompt.md" 2>/dev/null || log_warning "Could not download ${prompt}.prompt.md"
    done
    
    # Download essential instructions
    curl -sSL "$REPO_URL/raw/main/.github/instructions/security.instructions.md" \
        -o ".github/instructions/security.instructions.md" 2>/dev/null || log_warning "Could not download security instructions"
    
    # Download validation script
    curl -sSL "$REPO_URL/raw/main/scripts/validation/validate-structure.sh" \
        -o "scripts/validation/validate-structure.sh" 2>/dev/null || log_warning "Could not download validation script"
    chmod +x scripts/validation/validate-structure.sh 2>/dev/null || true
    
    log_success "Essential files copied"
}

# Setup full repository
setup_full_repository() {
    log_info "Cloning full repository to $TARGET_DIR..."
    
    if command -v git >/dev/null 2>&1; then
        git clone "$REPO_URL" "$TARGET_DIR"
        cd "$TARGET_DIR"
        log_success "Repository cloned to $TARGET_DIR"
    else
        log_error "Git not found. Please install git or use --essential-only option"
        exit 1
    fi
}

# Setup VS Code integration
setup_vscode_integration() {
    log_info "Setting up VS Code integration..."
    
    # Download workspace file
    curl -sSL "$REPO_URL/raw/main/github-copilot-enhancement.code-workspace" \
        -o "github-copilot-enhancement.code-workspace" 2>/dev/null || log_warning "Could not download workspace file"
    
    # Download VS Code settings if .vscode directory doesn't exist
    if [[ ! -d ".vscode" ]]; then
        mkdir -p .vscode
        curl -sSL "$REPO_URL/raw/main/.vscode/extensions.json" \
            -o ".vscode/extensions.json" 2>/dev/null || log_warning "Could not download extensions.json"
    fi
    
    log_success "VS Code integration configured"
}

# Check if running in VS Code terminal
check_vscode_environment() {
    if [[ -n "${VSCODE_PID:-}" ]] || [[ -n "${TERM_PROGRAM:-}" && "$TERM_PROGRAM" == "vscode" ]]; then
        log_info "Running in VS Code - enhanced integration available"
        return 0
    fi
    return 1
}

# Main execution
main() {
    log_info "GitHub Copilot Enhancement Framework Quick Setup"
    echo
    
    if check_vscode_environment; then
        log_info "VS Code detected - setting up with enhanced integration"
    fi
    
    setup_copilot_enhancement
    
    if check_vscode_environment; then
        log_info "VS Code integration complete!"
        log_info "Reload the window to see the new workspace configuration"
    fi
}

# Run main function
main "$@"
