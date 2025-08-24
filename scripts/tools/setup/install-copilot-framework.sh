#!/bin/bash

# GitHub Copilot Enhancement Framework - Complete Installation Script
# This script installs the entire framework into VS Code/local environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Detect VS Code configuration directory
detect_vscode_config() {
    local config_dirs=(
        "$HOME/.vscode"
        "$HOME/.vscode-insiders"
        "$HOME/Library/Application Support/Code/User"
        "$HOME/Library/Application Support/Code - Insiders/User"
        "$HOME/AppData/Roaming/Code/User"
        "$HOME/AppData/Roaming/Code - Insiders/User"
    )
    
    for dir in "${config_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "$dir"
            return 0
        fi
    done
    
    # Default fallback
    echo "$HOME/.vscode"
}

# Create directory structure
create_directories() {
    local base_dir="$1"
    local dirs=(
        "copilot-instructions"
        "copilot-instructions/chatmodes"
        "copilot-instructions/instructions"
        "copilot-instructions/prompts"
        "copilot-instructions/schemas"
        "copilot-instructions/runbooks"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$base_dir/$dir"
        log_info "Created directory: $base_dir/$dir"
    done
}

# Copy instruction files
copy_instructions() {
    local dest_dir="$1"
    
    log_info "Installing core instructions..."
    cp "$REPO_ROOT/.github/copilot-instructions.md" "$dest_dir/copilot-instructions.md"
    
    log_info "Installing specialized instruction files..."
    cp -r "$REPO_ROOT/.github/instructions/"* "$dest_dir/copilot-instructions/instructions/"
    
    log_info "Installing chat modes..."
    cp -r "$REPO_ROOT/.github/chatmodes/"* "$dest_dir/copilot-instructions/chatmodes/"
    
    log_info "Installing prompt templates..."
    if [[ -d "$REPO_ROOT/.github/prompts" ]]; then
        cp -r "$REPO_ROOT/.github/prompts/"* "$dest_dir/copilot-instructions/prompts/"
    fi
    
    log_info "Installing schemas..."
    if [[ -d "$REPO_ROOT/.github/schemas" ]]; then
        cp -r "$REPO_ROOT/.github/schemas/"* "$dest_dir/copilot-instructions/schemas/"
    fi
    
    log_info "Installing runbooks..."
    if [[ -d "$REPO_ROOT/.github/runbooks" ]]; then
        cp -r "$REPO_ROOT/.github/runbooks/"* "$dest_dir/copilot-instructions/runbooks/"
    fi
}

# Create master instruction file that references all components
create_master_instructions() {
    local dest_dir="$1"
    local master_file="$dest_dir/copilot-instructions-framework.md"
    
    cat > "$master_file" << 'EOF'
---
applyTo: "**/*"
priority: "framework"
---

# GitHub Copilot Enhancement Framework - Complete Instructions

This file loads the entire GitHub Copilot Enhancement Framework with all specialized instructions, chat modes, and tools.

## Framework Components

### Core Instructions
- Base repository instructions: `copilot-instructions.md`

### Specialized Instructions (by scope)
- Agent workflow and quality: `instructions/agent-workflow.instructions.md`
- Code quality standards: `instructions/code-quality.instructions.md`
- Security practices: `instructions/security.instructions.md`
- Testing methodology: `instructions/testing.instructions.md`
- Documentation standards: `instructions/docs-policy.instructions.md`
- File organization: `instructions/file-organization.instructions.md`
- Toolshed usage: `instructions/toolshed-usage.instructions.md`
- Version control: `instructions/version-control.instructions.md`
- Documentation awareness: `instructions/documentation-awareness.instructions.md`
- Debugging practices: `instructions/debugging.instructions.md`
- Archive policy: `instructions/archive-policy.instructions.md`

### Chat Modes (specialized AI personalities)
- **Architect**: `chatmodes/architect.chatmode.md` - System design and architecture
- **Elite Engineer**: `chatmodes/elite-engineer.chatmode.md` - Advanced development
- **Documentation**: `chatmodes/documentation.chatmode.md` - Technical writing
- **Security**: `chatmodes/security.chatmode.md` - Security-focused development
- **Testing**: `chatmodes/testing.chatmode.md` - Test-driven development
- **Performance**: `chatmodes/performance.chatmode.md` - Optimization focused
- **Advanced Task Planner**: `chatmodes/advanced-task-planner.chatmode.md` - Project planning
- **Claude Sonnet 4 Architect**: `chatmodes/claude-sonnet4-architect.chatmode.md` - Claude-specific
- **Gemini Pro Specialist**: `chatmodes/gemini-pro-specialist.chatmode.md` - Gemini-specific
- **GPT-5 Elite Developer**: `chatmodes/gpt5-elite-developer.chatmode.md` - GPT-specific
- **O1 Preview Reasoning**: `chatmodes/o1-preview-reasoning.chatmode.md` - Reasoning-focused

### Usage in GitHub Copilot Chat

**Load specific instruction sets:**
```
@github use instructions/security.instructions.md
@github use instructions/testing.instructions.md
```

**Activate specialized chat modes:**
```
@github use chatmodes/architect.chatmode.md
@github use chatmodes/security.chatmode.md
```

**Load the complete framework:**
```
@github use copilot-instructions-framework.md
```

## Framework Philosophy

This framework follows a systematic "Check First, Act Second" workflow:
1. **Discovery Phase** - Read relevant instructions
2. **Analysis Phase** - Understand requirements
3. **Validation Phase** - Verify against policies
4. **Execution Phase** - Execute with compliance
5. **Verification Phase** - Confirm quality

## Quick Reference

- **Toolshed**: Use existing scripts in `scripts/tools/` before creating new ones
- **Documentation**: Follow placement rules in `docs/` hierarchy
- **File Organization**: Respect directory structure policies
- **Quality**: Prioritize thoroughness over speed
- **Validation**: Run `npm run quick:validate` for quality checks

---

**Installation Date**: $(date)
**Framework Version**: Comprehensive GitHub Copilot Enhancement Framework
**Components**: Core instructions + 11 specialized instructions + 11 chat modes + schemas + prompts
EOF

    log_success "Created master instruction file: $master_file"
}

# Main installation function
main() {
    log_info "🚀 Installing GitHub Copilot Enhancement Framework..."
    
    # Detect VS Code configuration directory
    local vscode_config
    vscode_config=$(detect_vscode_config)
    log_info "VS Code config directory: $vscode_config"
    
    # Create directories
    create_directories "$vscode_config"
    
    # Copy all framework components
    copy_instructions "$vscode_config"
    
    # Create master instruction file
    create_master_instructions "$vscode_config"
    
    log_success "🎉 GitHub Copilot Enhancement Framework installed successfully!"
    echo
    log_info "📋 Installation Summary:"
    echo "   • Core instructions: copilot-instructions.md"
    echo "   • Specialized instructions: 11 files in copilot-instructions/instructions/"
    echo "   • Chat modes: 11 files in copilot-instructions/chatmodes/"
    echo "   • Master framework file: copilot-instructions-framework.md"
    echo
    log_info "🔧 Usage in VS Code:"
    echo "   • Load complete framework: @github use copilot-instructions-framework.md"
    echo "   • Load specific components: @github use instructions/security.instructions.md"
    echo "   • Activate chat modes: @github use chatmodes/architect.chatmode.md"
    echo
    log_info "📖 Documentation: Check README.md for full usage instructions"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
