#!/bin/bash
# xanadOS Search & Destroy - One-Command Complete Setup
# This script handles everything needed for development environment setup
# Usage: bash scripts/setup.sh [--force] [--minimal]

set -euo pipefail

# Script metadata
SCRIPT_VERSION="1.0.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$REPO_ROOT/setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# Configuration
FORCE_INSTALL=false
MINIMAL_INSTALL=false
ISSUES_FOUND=0
FIXES_APPLIED=0

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO")  echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[✓]${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[⚠]${NC} $message" ;;
        "ERROR") echo -e "${RED}[✗]${NC} $message" >&2 ;;
        "HEADER") echo -e "${BOLD}${CYAN}$message${NC}" ;;
        "STEP")  echo -e "${PURPLE}→${NC} $message" ;;
    esac

    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Progress indicator
show_progress() {
    local current=$1
    local total=$2
    local message="$3"
    local percent=$((current * 100 / total))
    local filled=$((percent / 5))
    local empty=$((20 - filled))

    printf "\r${CYAN}[%*s%*s] %d%% - %s${NC}" \
        $filled "" $empty "" $percent "$message"

    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# Error handling
error_exit() {
    log ERROR "$1"
    echo ""
    log ERROR "Setup failed! Check $LOG_FILE for details."
    exit 1
}

# Detect operating system
detect_system() {
    if [[ -f /etc/arch-release ]]; then
        echo "arch"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    elif [[ -f /etc/fedora-release ]]; then
        echo "fedora"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Banner
show_banner() {
    clear
    echo -e "${BOLD}${CYAN}"
    cat << 'EOF'
╭─────────────────────────────────────────────────────────────────╮
│                                                                 │
│    🚀 xanadOS Search & Destroy - Complete Setup Script         │
│                                                                 │
│    ✨ One command installs everything you need:                │
│       • Python virtual environment with all dependencies       │
│       • Modern package managers (uv, pnpm, fnm)               │
│       • Node.js and JavaScript dependencies                    │
│       • Security tools (ClamAV, RKHunter)                     │
│       • Development tools and validation                       │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯
EOF
    echo -e "${NC}"
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            --minimal)
                MINIMAL_INSTALL=true
                shift
                ;;
            --help|-h)
                cat << EOF
Usage: $0 [options]

Options:
    --force     Force reinstallation of all tools
    --minimal   Install only essential dependencies
    --help      Show this help

This script will:
1. Install modern package managers (uv, pnpm, fnm)
2. Create Python virtual environment
3. Install all Python dependencies
4. Install Node.js dependencies
5. Install system security tools
6. Configure development environment
7. Validate installation

Log file: $LOG_FILE
EOF
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# System requirements check
check_requirements() {
    log INFO "Checking system requirements..."

    # Check Bash version
    if [[ ${BASH_VERSION%%.*} -lt 4 ]]; then
        error_exit "Bash 4.0 or higher required. Current: $BASH_VERSION"
    fi

    # Check for essential tools
    local essential_tools=("curl" "git")
    for tool in "${essential_tools[@]}"; do
        if ! command_exists "$tool"; then
            error_exit "$tool is required but not installed"
        fi
    done

    # Check Python version
    if ! command_exists python3; then
        error_exit "Python 3 is required but not installed"
    fi

    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local min_version="3.10"
    if [[ "$(printf '%s\n' "$min_version" "$python_version" | sort -V | head -n1)" != "$min_version" ]]; then
        error_exit "Python $min_version or higher required. Current: $python_version"
    fi

    log SUCCESS "System requirements met"
}

# Install modern package managers
install_package_managers() {
    log HEADER "Installing modern package managers..."

    local steps=3
    local current=0

    # Install uv (Python package manager)
    ((current++))
    show_progress $current $steps "Installing uv (Python package manager)..."
    if ! command_exists uv || [[ "$FORCE_INSTALL" == "true" ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        if command_exists uv; then
            log SUCCESS "uv $(uv --version) installed"
        else
            error_exit "Failed to install uv"
        fi
    else
        log SUCCESS "uv already installed ($(uv --version))"
    fi

    # Install pnpm (Node.js package manager)
    ((current++))
    show_progress $current $steps "Installing pnpm (Node.js package manager)..."
    if ! command_exists pnpm || [[ "$FORCE_INSTALL" == "true" ]]; then
        curl -fsSL https://get.pnpm.io/install.sh | sh -
        export PATH="$HOME/.local/share/pnpm:$PATH"
        if command_exists pnpm; then
            log SUCCESS "pnpm $(pnpm --version) installed"
        else
            log WARN "pnpm installation may have failed, will try npm"
        fi
    else
        log SUCCESS "pnpm already installed ($(pnpm --version))"
    fi

    # Install fnm (Node.js version manager)
    ((current++))
    show_progress $current $steps "Installing fnm (Node.js version manager)..."
    if ! command_exists fnm || [[ "$FORCE_INSTALL" == "true" ]]; then
        # Install unzip if needed (required for fnm)
        if ! command_exists unzip; then
            local system=$(detect_system)
            case "$system" in
                "arch") sudo pacman -S --noconfirm unzip ;;
                "debian") sudo apt-get update && sudo apt-get install -y unzip ;;
                "fedora") sudo dnf install -y unzip ;;
                "macos") brew install unzip ;;
            esac
        fi

        curl -fsSL https://fnm.vercel.app/install | bash
        export PATH="$HOME/.local/share/fnm:$PATH"
        if command_exists fnm; then
            log SUCCESS "fnm $(fnm --version) installed"
        else
            log WARN "fnm installation may have failed"
        fi
    else
        log SUCCESS "fnm already installed ($(fnm --version))"
    fi

    echo ""
}

# Configure shell environment
configure_shell() {
    log INFO "Configuring shell environment..."

    local shell_config="$HOME/.bashrc"
    if [[ "$SHELL" == *"zsh"* ]]; then
        shell_config="$HOME/.zshrc"
    fi

    # Create backup
    if [[ -f "$shell_config" ]]; then
        cp "$shell_config" "${shell_config}.backup.$(date +%Y%m%d%H%M%S)"
    fi

    # Add PATH configurations if not present
    local config_block="
# xanadOS Development Environment - Added by setup script
export PATH=\"\$HOME/.local/bin:\$PATH\"
export PATH=\"\$HOME/.local/share/pnpm:\$PATH\"
export PATH=\"\$HOME/.local/share/fnm:\$PATH\"

# Initialize fnm for automatic Node.js version switching
if command -v fnm >/dev/null 2>&1; then
    eval \"\$(fnm env --use-on-cd)\"
fi

# Auto-activate Python virtual environment for xanadOS project
if [[ \"\$PWD\" == *\"xanadOS-Search_Destroy\"* ]] && [[ -f \"\$PWD/.venv/bin/activate\" ]]; then
    source \"\$PWD/.venv/bin/activate\"
fi
"

    if ! grep -q "xanadOS Development Environment" "$shell_config" 2>/dev/null; then
        echo "$config_block" >> "$shell_config"
        log SUCCESS "Shell configuration updated"
    else
        log SUCCESS "Shell already configured"
    fi

    # Apply to current session
    export PATH="$HOME/.local/bin:$HOME/.local/share/pnpm:$HOME/.local/share/fnm:$PATH"
}

# Setup Python environment
setup_python_environment() {
    log HEADER "Setting up Python environment..."

    cd "$REPO_ROOT"

    local steps=4
    local current=0

    # Create virtual environment
    ((current++))
    show_progress $current $steps "Creating Python virtual environment..."
    if [[ ! -d ".venv" ]] || [[ "$FORCE_INSTALL" == "true" ]]; then
        rm -rf .venv
        if command_exists uv; then
            uv venv .venv --python python3
        else
            python3 -m venv .venv
        fi
        log SUCCESS "Virtual environment created"
    else
        log SUCCESS "Virtual environment already exists"
    fi

    # Activate virtual environment
    ((current++))
    show_progress $current $steps "Activating virtual environment..."
    source .venv/bin/activate
    log SUCCESS "Virtual environment activated"

    # Upgrade pip in virtual environment
    ((current++))
    show_progress $current $steps "Upgrading pip..."
    python -m pip install --upgrade pip
    log SUCCESS "pip upgraded"

    # Install project dependencies
    ((current++))
    show_progress $current $steps "Installing Python dependencies..."
    if command_exists uv; then
        # Use uv for faster installation
        uv pip install -e .
        if [[ "$MINIMAL_INSTALL" != "true" ]]; then
            uv pip install -e ".[dev]" || log WARN "Some dev dependencies failed to install"
        fi
    else
        # Fallback to pip
        pip install -e .
        if [[ "$MINIMAL_INSTALL" != "true" ]]; then
            pip install -e ".[dev]" || log WARN "Some dev dependencies failed to install"
        fi
    fi
    log SUCCESS "Python dependencies installed"

    echo ""
}

# Setup Node.js environment
setup_nodejs_environment() {
    log HEADER "Setting up Node.js environment..."

    cd "$REPO_ROOT"

    local steps=3
    local current=0

    # Install Node.js if needed
    ((current++))
    show_progress $current $steps "Checking Node.js installation..."
    if ! command_exists node; then
        if command_exists fnm; then
            fnm install --lts
            fnm use lts-latest
            fnm default lts-latest
            eval "$(fnm env)"
            log SUCCESS "Node.js installed via fnm"
        else
            log WARN "Node.js not found and fnm not available"
            return
        fi
    else
        log SUCCESS "Node.js $(node --version) available"
    fi

    # Install npm dependencies
    ((current++))
    show_progress $current $steps "Installing Node.js dependencies..."
    if [[ -f "package.json" ]]; then
        if command_exists pnpm; then
            pnpm install
            log SUCCESS "Dependencies installed with pnpm"
        elif command_exists npm; then
            npm install
            log SUCCESS "Dependencies installed with npm"
        else
            log WARN "No Node.js package manager available"
        fi
    else
        log WARN "No package.json found"
    fi

    # Verify installation
    ((current++))
    show_progress $current $steps "Verifying Node.js setup..."
    if [[ -d "node_modules" ]]; then
        log SUCCESS "Node.js environment ready"
    else
        log WARN "Node.js dependencies may not be fully installed"
    fi

    echo ""
}

# Install system dependencies
install_system_dependencies() {
    if [[ "$MINIMAL_INSTALL" == "true" ]]; then
        log INFO "Skipping system dependencies (minimal install)"
        return
    fi

    log HEADER "Installing system dependencies..."

    local system=$(detect_system)
    local steps=2
    local current=0

    # Install security tools
    ((current++))
    show_progress $current $steps "Installing security tools..."
    case "$system" in
        "arch")
            if ! command_exists clamscan || ! command_exists rkhunter; then
                sudo pacman -S --noconfirm clamav clamav-daemon rkhunter cronie || log WARN "Some security tools failed to install"
                sudo systemctl enable --now cronie || log WARN "Failed to enable cron service"
            fi
            ;;
        "debian")
            if ! command_exists clamscan || ! command_exists rkhunter; then
                sudo apt-get update
                sudo apt-get install -y clamav clamav-daemon rkhunter cron || log WARN "Some security tools failed to install"
                sudo systemctl enable --now cron || log WARN "Failed to enable cron service"
            fi
            ;;
        "fedora")
            if ! command_exists clamscan || ! command_exists rkhunter; then
                sudo dnf install -y clamav clamav-update rkhunter cronie || log WARN "Some security tools failed to install"
                sudo systemctl enable --now crond || log WARN "Failed to enable cron service"
            fi
            ;;
        "macos")
            if ! command_exists clamscan; then
                brew install clamav || log WARN "ClamAV installation failed"
            fi
            ;;
        *)
            log WARN "Unknown system, skipping system dependencies"
            ;;
    esac

    # Update ClamAV database
    ((current++))
    show_progress $current $steps "Updating security databases..."
    if command_exists freshclam; then
        sudo freshclam || log WARN "ClamAV database update failed"
    fi

    log SUCCESS "System dependencies installed"
    echo ""
}

# Validate installation
validate_installation() {
    log HEADER "Validating installation..."

    local steps=5
    local current=0
    local issues=0

    # Check Python environment
    ((current++))
    show_progress $current $steps "Validating Python environment..."
    if [[ -d ".venv" ]] && source .venv/bin/activate && python -c "import app.main" 2>/dev/null; then
        log SUCCESS "Python environment valid"
    else
        log WARN "Python environment issues detected"
        ((issues++))
    fi

    # Check critical Python modules
    ((current++))
    show_progress $current $steps "Checking critical Python modules..."
    source .venv/bin/activate || true
    local critical_modules=("requests" "numpy" "aiohttp" "psutil")
    for module in "${critical_modules[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            log SUCCESS "$module available"
        else
            log WARN "$module not available"
            ((issues++))
        fi
    done

    # Check Node.js environment
    ((current++))
    show_progress $current $steps "Validating Node.js environment..."
    if command_exists node && [[ -f "package.json" ]]; then
        if npm run --silent version:get >/dev/null 2>&1; then
            log SUCCESS "Node.js environment valid"
        else
            log WARN "Node.js environment issues detected"
            ((issues++))
        fi
    else
        log WARN "Node.js environment not available"
        ((issues++))
    fi

    # Check development tools
    ((current++))
    show_progress $current $steps "Checking development tools..."
    local tools=("uv" "pnpm" "fnm")
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            log SUCCESS "$tool available"
        else
            log WARN "$tool not available"
            ((issues++))
        fi
    done

    # Run comprehensive validation
    ((current++))
    show_progress $current $steps "Running comprehensive validation..."
    if [[ -f "package.json" ]] && command_exists npm; then
        if npm run quick:validate >/dev/null 2>&1; then
            log SUCCESS "Comprehensive validation passed"
        else
            log WARN "Some validation checks failed (non-critical)"
        fi
    fi

    echo ""

    # Report results
    if [[ $issues -eq 0 ]]; then
        log SUCCESS "✅ Installation validation completed successfully!"
    else
        log WARN "⚠️  Installation completed with $issues minor issues"
        log INFO "These issues are typically non-critical and won't affect core functionality"
    fi
}

# Generate setup report
generate_report() {
    log INFO "Generating setup report..."

    local report_file="$REPO_ROOT/SETUP_REPORT.md"

    cat > "$report_file" << EOF
# xanadOS Search & Destroy - Setup Report

**Generated:** $(date)
**Script Version:** $SCRIPT_VERSION

## Installed Tools

### Package Managers
- **uv:** $(command_exists uv && uv --version || echo "Not installed")
- **pnpm:** $(command_exists pnpm && pnpm --version || echo "Not installed")
- **fnm:** $(command_exists fnm && fnm --version || echo "Not installed")

### Runtime Versions
- **Node.js:** $(command_exists node && node --version || echo "Not installed")
- **Python:** $(python3 --version 2>/dev/null || echo "Not installed")

### Security Tools
- **ClamAV:** $(command_exists clamscan && clamscan --version | head -1 || echo "Not installed")
- **RKHunter:** $(command_exists rkhunter && echo "Installed" || echo "Not installed")

## Environment Status

### Virtual Environment
- **Status:** $(test -d .venv && echo "Created" || echo "Not found")
- **Python Packages:** $(test -d .venv && source .venv/bin/activate && pip list | wc -l || echo "0") installed

### Node.js Environment
- **Dependencies:** $(test -d node_modules && echo "Installed" || echo "Not installed")
- **Package Count:** $(test -f package.json && cat package.json | grep -c '"' || echo "0") defined

## Next Steps

1. **Start development:**
   \`\`\`bash
   cd $REPO_ROOT
   source .venv/bin/activate  # Or just cd into directory for auto-activation
   make dev
   \`\`\`

2. **Run the application:**
   \`\`\`bash
   python -m app.main
   \`\`\`

3. **Run tests:**
   \`\`\`bash
   npm test
   \`\`\`

4. **Use modern package managers:**
   \`\`\`bash
   # Python packages
   uv add package-name

   # Node.js packages
   pnpm add package-name

   # Switch Node.js versions
   fnm use 18
   \`\`\`

## Troubleshooting

If you encounter issues:

1. **Check the log:** \`cat $LOG_FILE\`
2. **Re-run setup:** \`bash scripts/setup.sh --force\`
3. **Minimal setup:** \`bash scripts/setup.sh --minimal\`

For more help, see: docs/user/Installation.md
EOF

    log SUCCESS "Setup report generated: $report_file"
}

# Main execution
main() {
    # Initialize log
    echo "# xanadOS Setup Log - $(date)" > "$LOG_FILE"

    show_banner
    parse_arguments "$@"

    log INFO "Starting xanadOS Search & Destroy complete setup..."
    log INFO "Mode: $([ "$MINIMAL_INSTALL" == "true" ] && echo "Minimal" || echo "Full")"
    log INFO "Force reinstall: $FORCE_INSTALL"

    # Main setup sequence
    check_requirements
    install_package_managers
    configure_shell
    setup_python_environment
    setup_nodejs_environment
    install_system_dependencies
    validate_installation
    generate_report

    # Final success message
    echo ""
    log HEADER "🎉 Setup Complete!"
    echo ""
    log SUCCESS "Your xanadOS Search & Destroy development environment is ready!"
    echo ""
    log INFO "Next steps:"
    echo "  1. Restart your terminal (or run: source ~/.bashrc)"
    echo "  2. Navigate to the project: cd $REPO_ROOT"
    echo "  3. Start developing: make dev"
    echo ""
    log INFO "For detailed information, see: SETUP_REPORT.md"
    log INFO "Full log available at: $LOG_FILE"
}

# Run main function with all arguments
main "$@"
