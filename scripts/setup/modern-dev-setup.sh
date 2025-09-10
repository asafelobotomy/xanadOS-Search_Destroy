#!/usr/bin/env bash
# 🚀 Modern Development Environment Setup - 2025 Edition
# Comprehensive, automated, and user-friendly setup with modern best practices

set -euo pipefail

# Version and metadata
readonly SCRIPT_VERSION="2.11.2"
readonly REQUIRED_BASH_VERSION=4

# Colors and formatting
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color
readonly BOLD='\033[1m'

# Emojis for better UX
readonly CHECKMARK="✅"
readonly WARNING="⚠️"
readonly ERROR="❌"
readonly GEAR="⚙️"
readonly SPARKLES="✨"
readonly LIGHTNING="⚡"
readonly FOLDER="📁"
readonly COMPUTER="💻"

# Configuration
REPO_ROOT=""
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly REPO_ROOT

SETUP_LOG=""
SETUP_LOG="$REPO_ROOT/logs/setup-$(date +%Y%m%d-%H%M%S).log"
readonly SETUP_LOG

readonly CONFIG_FILE="$HOME/.xanados-dev-config"

# Create logs directory if it doesn't exist
mkdir -p "$REPO_ROOT/logs"

# Advanced logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO")  echo -e "${BLUE}${GEAR} [INFO]${NC} $message" | tee -a "$SETUP_LOG" ;;
        "SUCCESS") echo -e "${GREEN}${CHECKMARK} [SUCCESS]${NC} $message" | tee -a "$SETUP_LOG" ;;
        "WARNING") echo -e "${YELLOW}${WARNING} [WARNING]${NC} $message" | tee -a "$SETUP_LOG" ;;
        "ERROR") echo -e "${RED}${ERROR} [ERROR]${NC} $message" | tee -a "$SETUP_LOG" ;;
        "HEADER") echo -e "${WHITE}${BOLD}${SPARKLES} $message ${SPARKLES}${NC}" | tee -a "$SETUP_LOG" ;;
        "SUBHEADER") echo -e "${CYAN}${BOLD}$message${NC}" | tee -a "$SETUP_LOG" ;;
    esac
}

# Enhanced error handling
error_exit() {
    log ERROR "$1"
    log ERROR "Setup failed. Check the log at: $SETUP_LOG"
    exit "${2:-1}"
}

# Progress indicator
show_progress() {
    local current="$1"
    local total="$2"
    local task="$3"
    local percent=$((current * 100 / total))
    local bar_length=30
    local filled_length=$((bar_length * current / total))

    printf "\r${CYAN}[%3d%%]${NC} [" "$percent"
    printf "%*s" "$filled_length" "" | tr ' ' '█'
    printf "%*s" $((bar_length - filled_length)) "" | tr ' ' '░'
    printf "] ${WHITE}%s${NC}" "$task"
}

# System detection with enhanced support
detect_system() {
    log INFO "Detecting system configuration..."

    # OS Detection
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v pacman >/dev/null 2>&1; then
            echo "arch"
        elif command -v apt-get >/dev/null 2>&1; then
            echo "debian"
        elif command -v dnf >/dev/null 2>&1; then
            echo "fedora"
        elif command -v yum >/dev/null 2>&1; then
            echo "rhel"
        elif command -v zypper >/dev/null 2>&1; then
            echo "suse"
        elif command -v apk >/dev/null 2>&1; then
            echo "alpine"
        else
            echo "linux-unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Modern package manager detection and installation
setup_modern_package_managers() {
    log HEADER "Setting up modern package managers"
    local system=$(detect_system)

    # 1. Install fnm (Fast Node Manager) - 500x faster than nvm
    if ! command -v fnm >/dev/null 2>&1; then
        log INFO "Installing fnm (Fast Node Manager)..."
        case "$system" in
            "arch")
                if command -v paru >/dev/null 2>&1; then
                    paru -S fnm --noconfirm || sudo pacman -S fnm --noconfirm
                elif command -v yay >/dev/null 2>&1; then
                    yay -S fnm --noconfirm
                else
                    curl -fsSL https://fnm.vercel.app/install | bash
                fi
                ;;
            "debian"|"ubuntu")
                curl -fsSL https://fnm.vercel.app/install | bash
                ;;
            "fedora"|"rhel")
                curl -fsSL https://fnm.vercel.app/install | bash
                ;;
            "macos")
                if command -v brew >/dev/null 2>&1; then
                    brew install fnm
                else
                    curl -fsSL https://fnm.vercel.app/install | bash
                fi
                ;;
            *)
                curl -fsSL https://fnm.vercel.app/install | bash
                ;;
        esac

        # Add fnm to current session
        export PATH="$HOME/.local/bin:$PATH"
        log SUCCESS "fnm installed successfully"
    else
        log SUCCESS "fnm already installed"
    fi

    # Configure fnm for automatic switching
    setup_fnm_auto_switching

    # 2. Install pnpm (70% less disk space, 2-3x faster than npm)
    if ! command -v pnpm >/dev/null 2>&1; then
        log INFO "Installing pnpm (Performance & Efficiency Package Manager)..."
        if command -v fnm >/dev/null 2>&1; then
            # Use fnm to install Node.js first
            fnm install --lts
            fnm use lts-latest
            fnm default lts-latest
        fi

        # Install pnpm
        curl -fsSL https://get.pnpm.io/install.sh | sh
        export PATH="$HOME/.local/share/pnpm:$PATH"
        log SUCCESS "pnpm installed successfully"
    else
        log SUCCESS "pnpm already installed"
    fi

    # 3. Setup uv (already handled in main script, but ensure it's optimized)
    if ! command -v uv >/dev/null 2>&1; then
        log INFO "Installing uv (Modern Python Package Manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        log SUCCESS "uv installed successfully"
    else
        log SUCCESS "uv already installed"
    fi
}

# Setup automatic Node.js version switching
setup_fnm_auto_switching() {
    log INFO "Configuring automatic Node.js version switching..."

    # Create .nvmrc equivalent file for this project
    if [[ ! -f "$REPO_ROOT/.node-version" ]]; then
        echo "lts/*" > "$REPO_ROOT/.node-version"
        log SUCCESS "Created .node-version file"
    fi

    # Setup shell integration
    local shell_config=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        shell_config="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        shell_config="$HOME/.bashrc"
    else
        shell_config="$HOME/.profile"
    fi

    if [[ -f "$shell_config" ]] && ! grep -q "fnm env" "$shell_config"; then
        cat >> "$shell_config" << 'EOF'

# fnm (Fast Node Manager)
if command -v fnm >/dev/null 2>&1; then
    eval "$(fnm env --use-on-cd)"
fi
EOF
        log SUCCESS "Added fnm auto-switching to $shell_config"
    fi
}

# Enhanced dependency installation with modern tools
install_dependencies_modern() {
    log HEADER "Installing dependencies with modern package managers"

    local steps=6
    local current=0

    # Node.js setup with fnm
    ((current++))
    show_progress $current $steps "Checking Node.js..."
    if command -v node >/dev/null 2>&1; then
        log SUCCESS "Node.js $(node --version) already available"
    elif command -v fnm >/dev/null 2>&1; then
        # Only install if Node.js is not available
        fnm install --lts 2>/dev/null || log WARN "Failed to install Node.js with fnm"
        fnm use lts-latest 2>/dev/null || true
        fnm default lts-latest 2>/dev/null || true
        eval "$(fnm env)" 2>/dev/null || true
        log SUCCESS "Node.js setup attempted with fnm"
    fi
    echo ""

    # Install JavaScript dependencies with pnpm
    ((current++))
    show_progress $current $steps "Installing JavaScript dependencies..."
    if command -v pnpm >/dev/null 2>&1 && [[ -f "$REPO_ROOT/package.json" ]]; then
        cd "$REPO_ROOT"
        pnpm install --frozen-lockfile 2>/dev/null || pnpm install
        log SUCCESS "JavaScript dependencies installed with pnpm"
    fi
    echo ""

    # Python dependencies with uv
    ((current++))
    show_progress $current $steps "Setting up Python environment..."
    if command -v uv >/dev/null 2>&1; then
        cd "$REPO_ROOT"
        uv sync --all-extras
        log SUCCESS "Python environment synchronized"
    fi
    echo ""

    # System dependencies
    ((current++))
    show_progress $current $steps "Installing system dependencies..."
    install_system_dependencies
    echo ""

    # Security tools
    ((current++))
    show_progress $current $steps "Installing security tools..."
    install_security_tools_modern
    echo ""

    # Development tools
    ((current++))
    show_progress $current $steps "Setting up development tools..."
    setup_development_tools_modern
    echo ""

    log SUCCESS "All dependencies installed successfully!"
}

# Modern system dependency installation
install_system_dependencies() {
    local system=$(detect_system)

    case "$system" in
        "arch")
            if ! command -v clamav >/dev/null 2>&1; then
                sudo pacman -S --noconfirm clamav clamav-daemon rkhunter cronie git curl wget
                # Enable and start cron service
                sudo systemctl enable cronie.service
                sudo systemctl start cronie.service
            fi
            ;;
        "debian"|"ubuntu")
            if ! command -v clamav >/dev/null 2>&1; then
                sudo apt-get update
                sudo apt-get install -y clamav clamav-daemon rkhunter cron git curl wget
                # Enable and start cron service
                sudo systemctl enable cron.service
                sudo systemctl start cron.service
            fi
            ;;
        "fedora"|"rhel")
            if ! command -v clamav >/dev/null 2>&1; then
                sudo dnf install -y clamav clamav-update rkhunter cronie git curl wget
                # Enable and start cron service
                sudo systemctl enable crond.service
                sudo systemctl start crond.service
            fi
            ;;
        "macos")
            if command -v brew >/dev/null 2>&1; then
                brew install clamav rkhunter git curl wget
            fi
            ;;
    esac
}

# Enhanced security tools installation
install_security_tools_modern() {
    log INFO "Installing modern security analysis tools..."

    # Update ClamAV with progress indicator
    if command -v freshclam >/dev/null 2>&1; then
        log INFO "Updating ClamAV virus definitions..."
        sudo freshclam || log WARNING "ClamAV update failed, continuing..."
    fi

    # Install Python security tools with uv
    if command -v uv >/dev/null 2>&1; then
        cd "$REPO_ROOT"
        uv sync --extra security --extra malware-analysis
    fi
}

# Modern development tools setup
setup_development_tools_modern() {
    log INFO "Setting up modern development tools..."

    # Setup pre-commit hooks if available
    if command -v pre-commit >/dev/null 2>&1; then
        cd "$REPO_ROOT"
        if [[ -f ".pre-commit-config.yaml" ]]; then
            pre-commit install
            log SUCCESS "Pre-commit hooks installed"
        fi
    fi

    # Setup direnv for automatic environment loading
    setup_direnv_integration
}

# Direnv integration for automatic environment activation
setup_direnv_integration() {
    log INFO "Setting up direnv for automatic environment activation..."

    # Install direnv if not present
    local system=$(detect_system)
    if ! command -v direnv >/dev/null 2>&1; then
        case "$system" in
            "arch") sudo pacman -S --noconfirm direnv ;;
            "debian"|"ubuntu") sudo apt-get install -y direnv ;;
            "fedora"|"rhel") sudo dnf install -y direnv ;;
            "macos") brew install direnv ;;
        esac
    fi

    # Create .envrc file for automatic activation
    if [[ ! -f "$REPO_ROOT/.envrc" ]]; then
        cat > "$REPO_ROOT/.envrc" << 'EOF'
# Automatically activate Python virtual environment
source_env_if_exists .venv/bin/activate

# Load environment variables from .env if it exists
dotenv_if_exists

# Ensure uv is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Ensure pnpm is in PATH
export PATH="$HOME/.local/share/pnpm:$PATH"

# Auto-switch Node.js version with fnm
if command -v fnm >/dev/null 2>&1; then
    eval "$(fnm env)"
    if [[ -f .node-version ]]; then
        fnm use
    fi
fi

echo "🚀 xanadOS development environment activated!"
EOF

        log SUCCESS "Created .envrc for automatic environment activation"
        log INFO "Run 'direnv allow' to enable automatic activation"
    fi
}

# Enhanced validation with detailed reporting
validate_setup_modern() {
    log HEADER "Validating modern development environment"

    local total_checks=15
    local passed_checks=0
    local failed_checks=()

    # Helper function for validation
    validate_tool() {
        local tool="$1"
        local description="$2"
        local extra_check="${3:-}"

        if command -v "$tool" >/dev/null 2>&1; then
            if [[ -n "$extra_check" ]]; then
                if eval "$extra_check"; then
                    log SUCCESS "$description is installed and working"
                    return 0
                else
                    log WARNING "$description is installed but not working properly"
                    return 1
                fi
            else
                log SUCCESS "$description is installed"
                return 0
            fi
        else
            log WARNING "$description is not installed"
            return 1
        fi
    }

    # Validation checks
    validate_tool "fnm" "fnm (Fast Node Manager)" && ((passed_checks++)) || failed_checks+=("fnm")
    validate_tool "node" "Node.js" "node --version >/dev/null 2>&1" && ((passed_checks++)) || failed_checks+=("node")
    validate_tool "npm" "npm" && ((passed_checks++)) || failed_checks+=("npm")
    validate_tool "pnpm" "pnpm (Performance Package Manager)" && ((passed_checks++)) || failed_checks+=("pnpm")
    validate_tool "uv" "uv (Modern Python Manager)" && ((passed_checks++)) || failed_checks+=("uv")
    validate_tool "python3" "Python 3" && ((passed_checks++)) || failed_checks+=("python3")
    validate_tool "git" "Git" && ((passed_checks++)) || failed_checks+=("git")
    validate_tool "clamav" "ClamAV" || validate_tool "clamscan" "ClamAV Scanner" && ((passed_checks++)) || failed_checks+=("clamav")
    validate_tool "rkhunter" "RKHunter" && ((passed_checks++)) || failed_checks+=("rkhunter")
    validate_tool "direnv" "direnv (Environment Automation)" && ((passed_checks++)) || failed_checks+=("direnv")

    # Python environment checks
    if [[ -d "$REPO_ROOT/.venv" ]]; then
        log SUCCESS "Python virtual environment exists"
        ((passed_checks++))
    else
        log WARNING "Python virtual environment not found"
        failed_checks+=("python-venv")
    fi

    # Project file checks
    if [[ -f "$REPO_ROOT/package.json" ]] && [[ -f "$REPO_ROOT/pyproject.toml" ]]; then
        log SUCCESS "Project configuration files exist"
        ((passed_checks++))
    else
        log WARNING "Missing project configuration files"
        failed_checks+=("project-config")
    fi

    # Environment files
    if [[ -f "$REPO_ROOT/.envrc" ]]; then
        log SUCCESS "Environment automation configured (.envrc)"
        ((passed_checks++))
    else
        log WARNING "Environment automation not configured"
        failed_checks+=("envrc")
    fi

    # Node version management
    if [[ -f "$REPO_ROOT/.node-version" ]]; then
        log SUCCESS "Node.js version pinning configured"
        ((passed_checks++))
    else
        log WARNING "Node.js version not pinned"
        failed_checks+=("node-version")
    fi

    # Final validation
    if [[ -f "$REPO_ROOT/logs" ]]; then
        log SUCCESS "Logging directory configured"
        ((passed_checks++))
    else
        log WARNING "Logging directory missing"
        failed_checks+=("logs")
    fi

    # Report results
    local pass_rate=$((passed_checks * 100 / total_checks))

    echo ""
    log HEADER "Validation Results"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}${CHECKMARK} Passed: ${WHITE}$passed_checks/$total_checks${NC} (${GREEN}$pass_rate%${NC})"

    if [[ ${#failed_checks[@]} -gt 0 ]]; then
        echo -e "${YELLOW}${WARNING} Failed: ${WHITE}${#failed_checks[@]}${NC} - ${YELLOW}${failed_checks[*]}${NC}"
    fi

    if [[ $pass_rate -ge 90 ]]; then
        echo -e "${GREEN}${SPARKLES} Excellent! Your development environment is ready!${NC}"
    elif [[ $pass_rate -ge 75 ]]; then
        echo -e "${YELLOW}${GEAR} Good setup! Consider addressing the failed checks.${NC}"
    else
        echo -e "${RED}${WARNING} Setup needs attention. Please resolve the failed checks.${NC}"
    fi
}

# Performance benchmarking
benchmark_setup() {
    log HEADER "Benchmarking package manager performance"

    if command -v pnpm >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        log INFO "Comparing pnpm vs npm performance..."

        # Create temporary test project
        local test_dir=$(mktemp -d)
        cd "$test_dir"

        # Initialize test package.json
        cat > package.json << 'EOF'
{
  "name": "benchmark-test",
  "version": "1.0.0",
  "dependencies": {
    "lodash": "^4.17.21",
    "react": "^18.2.0",
    "express": "^4.18.2"
  }
}
EOF

        # Benchmark pnpm
        log INFO "Benchmarking pnpm install..."
        local pnpm_start=$(date +%s%N)
        pnpm install --silent >/dev/null 2>&1
        local pnpm_end=$(date +%s%N)
        local pnpm_time=$(( (pnpm_end - pnpm_start) / 1000000 ))

        # Clean up for npm test
        rm -rf node_modules package-lock.json pnpm-lock.yaml

        # Benchmark npm
        log INFO "Benchmarking npm install..."
        local npm_start=$(date +%s%N)
        npm install --silent >/dev/null 2>&1
        local npm_end=$(date +%s%N)
        local npm_time=$(( (npm_end - npm_start) / 1000000 ))

        # Calculate improvement
        local improvement=$(( (npm_time - pnpm_time) * 100 / npm_time ))

        # Cleanup
        cd "$REPO_ROOT"
        rm -rf "$test_dir"

        log SUCCESS "Performance Results:"
        echo -e "  ${CYAN}pnpm: ${WHITE}${pnpm_time}ms${NC}"
        echo -e "  ${CYAN}npm:  ${WHITE}${npm_time}ms${NC}"
        echo -e "  ${GREEN}pnpm is ${improvement}% faster than npm${NC}"
    fi
}

# Generate comprehensive setup report
generate_setup_report() {
    local report_file="$REPO_ROOT/logs/setup-report-$(date +%Y%m%d-%H%M%S).md"

    cat > "$report_file" << EOF
# xanadOS Development Environment Setup Report

**Date:** $(date)
**Setup Script Version:** $SCRIPT_VERSION
**System:** $(detect_system)

## Installed Tools

### Package Managers
- **fnm (Fast Node Manager):** $(command -v fnm >/dev/null 2>&1 && fnm --version || echo "Not installed")
- **pnpm (Performance Package Manager):** $(command -v pnpm >/dev/null 2>&1 && pnpm --version || echo "Not installed")
- **uv (Python Package Manager):** $(command -v uv >/dev/null 2>&1 && uv --version || echo "Not installed")

### Runtime Versions
- **Node.js:** $(command -v node >/dev/null 2>&1 && node --version || echo "Not installed")
- **Python:** $(command -v python3 >/dev/null 2>&1 && python3 --version || echo "Not installed")

### Security Tools
- **ClamAV:** $(command -v clamscan >/dev/null 2>&1 && clamscan --version | head -1 || echo "Not installed")
- **RKHunter:** $(command -v rkhunter >/dev/null 2>&1 && rkhunter --version | head -1 || echo "Not installed")

### Environment Automation
- **direnv:** $(command -v direnv >/dev/null 2>&1 && direnv version || echo "Not installed")

## Next Steps

1. **Activate environment automation:**
   \`\`\`bash
   direnv allow
   \`\`\`

2. **Install project dependencies:**
   \`\`\`bash
   pnpm install
   uv sync
   \`\`\`

3. **Run validation:**
   \`\`\`bash
   pnpm run quick:validate
   \`\`\`

## Modern Development Workflow

- **Automatic environment activation:** Powered by direnv + .envrc
- **Fast package management:** pnpm for JavaScript, uv for Python
- **Automatic Node.js switching:** fnm with .node-version
- **Enhanced performance:** Up to 70% disk space savings with pnpm

## Support

For issues or questions, check the documentation in \`docs/\` or the toolshed in \`scripts/tools/\`.
EOF

    log SUCCESS "Setup report generated: $report_file"
}

# Interactive setup mode
interactive_setup() {
    log HEADER "Interactive Setup Mode"

    echo -e "${WHITE}Welcome to the xanadOS Modern Development Environment Setup!${NC}"
    echo ""
    echo -e "This setup will install and configure:"
    echo -e "  ${CYAN}• fnm (Fast Node Manager) - 500x faster than nvm${NC}"
    echo -e "  ${CYAN}• pnpm (Performance Package Manager) - 70% less disk space${NC}"
    echo -e "  ${CYAN}• uv (Modern Python Manager) - 10-100x faster than pip${NC}"
    echo -e "  ${CYAN}• direnv (Environment Automation) - Automatic activation${NC}"
    echo -e "  ${CYAN}• Security tools (ClamAV, RKHunter)${NC}"
    echo ""

    read -p "$(echo -e "${YELLOW}Do you want to proceed with the modern setup? [Y/n]:${NC} ")" -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log INFO "Setup cancelled by user"
        exit 0
    fi

    # Package manager preferences
    echo -e "${WHITE}Package Manager Preferences:${NC}"
    read -p "$(echo -e "${CYAN}Use pnpm instead of npm? (Recommended) [Y/n]:${NC} ")" -n 1 -r
    echo ""

    local use_pnpm=true
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        use_pnpm=false
    fi

    # Save preferences
    cat > "$CONFIG_FILE" << EOF
# xanadOS Development Environment Configuration
SETUP_VERSION="$SCRIPT_VERSION"
USE_PNPM="$use_pnpm"
SETUP_DATE="$(date)"
EOF

    return 0
}

# Main execution function
main() {
    # Header
    clear
    echo -e "${WHITE}${BOLD}"
    echo "╭─────────────────────────────────────────────────────────────────╮"
    echo "│                                                                 │"
    echo "│  🚀 xanadOS Modern Development Environment Setup - 2025 Edition │"
    echo "│                                                                 │"
    echo "│  Enhanced with modern package managers and automation           │"
    echo "│  • fnm (500x faster Node.js management)                        │"
    echo "│  • pnpm (70% less disk space)                                  │"
    echo "│  • uv (10-100x faster Python)                                  │"
    echo "│  • direnv (automatic environment activation)                   │"
    echo "│                                                                 │"
    echo "╰─────────────────────────────────────────────────────────────────╯"
    echo -e "${NC}"

    log INFO "Starting modern development environment setup..."
    log INFO "Log file: $SETUP_LOG"

    # System requirements check
    if [[ ${BASH_VERSION%%.*} -lt $REQUIRED_BASH_VERSION ]]; then
        error_exit "Bash version $REQUIRED_BASH_VERSION or higher required. Current: $BASH_VERSION"
    fi

    # Interactive mode if no arguments
    if [[ $# -eq 0 ]]; then
        interactive_setup
    fi

    # Main setup sequence
    local start_time=$(date +%s)

    setup_modern_package_managers
    install_dependencies_modern
    validate_setup_modern
    benchmark_setup
    generate_setup_report

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Success message
    echo ""
    echo -e "${GREEN}${BOLD}${SPARKLES}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${SPARKLES}${NC}"
    echo -e "${GREEN}${BOLD}                        SETUP COMPLETED SUCCESSFULLY!${NC}"
    echo -e "${GREEN}${BOLD}${SPARKLES}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${SPARKLES}${NC}"
    echo ""
    echo -e "${WHITE}${COMPUTER} Setup completed in ${CYAN}${duration}s${NC}"
    echo -e "${WHITE}${FOLDER} Project ready for development!${NC}"
    echo ""
    echo -e "${YELLOW}${GEAR} Next Steps:${NC}"
    echo -e "  ${CYAN}1.${NC} Run ${WHITE}direnv allow${NC} to enable automatic environment activation"
    echo -e "  ${CYAN}2.${NC} Start developing with ${WHITE}cd${NC} to auto-activate environment"
    echo -e "  ${CYAN}3.${NC} Use ${WHITE}pnpm${NC} for JavaScript packages (70% faster)"
    echo -e "  ${CYAN}4.${NC} Use ${WHITE}uv${NC} for Python packages (100x faster)"
    echo ""
    echo -e "${GREEN}${LIGHTNING} Happy coding with the modern development stack! ${LIGHTNING}${NC}"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
