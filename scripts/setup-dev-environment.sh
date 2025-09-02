#!/usr/bin/env bash
# Modern Development Environment Setup Script
# Comprehensive setup for 2025 Python security application development

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    log_info "Starting xanadOS Search & Destroy development environment setup..."

    # Check for uv package manager (2025 standard)
    if ! command_exists uv; then
        log_warning "uv package manager not found. Installing..."
        install_uv
    else
        log_success "uv package manager already installed"
    fi

    # Setup Python environment with uv
    setup_python_environment

    # Install security analysis tools
    install_security_tools

    # Setup development tools
    setup_development_tools

    # Configure security settings
    configure_security

    # Setup pre-commit hooks
    setup_precommit_hooks

    # Validate installation
    validate_setup

    log_success "Development environment setup complete!"
    print_next_steps
}

# Install uv package manager
install_uv() {
    log_info "Installing uv package manager..."

    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command_exists wget; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        log_error "Neither curl nor wget found. Please install one and retry."
        exit 1
    fi

    # Add uv to PATH for current session (uv installs to ~/.local/bin by default)
    export PATH="$HOME/.local/bin:$PATH"

    # Give the system a moment to recognize the new installation
    sleep 1

    if command_exists uv; then
        log_success "uv installed successfully"
        uv --version
    else
        log_error "uv installation failed"
        exit 1
    fi
}

# Setup Python environment with modern tools
setup_python_environment() {
    log_info "Setting up Python environment..."

    # Create virtual environment with uv (faster than venv)
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment with uv..."
        uv venv --python 3.11
        log_success "Virtual environment created"
    fi

    # Install project in development mode with uv
    log_info "Installing project dependencies with uv..."

    # First install the main project dependencies
    uv sync || {
        log_error "Failed to sync basic dependencies"
        exit 1
    }

    # Install development dependencies including formatting tools
    log_info "Installing development dependencies (black, ruff, isort, etc.)..."
    uv sync --extra dev || {
        log_warning "Failed to install dev dependencies, continuing with basic setup..."
    }

    # Ensure critical runtime dependencies are installed
    log_info "Installing critical runtime dependencies..."
    uv pip install "numpy>=1.24.0" "schedule>=1.2.0" "aiohttp>=3.9.0" "inotify>=0.2.10" "dnspython>=2.6.0" || {
        log_warning "Some critical dependencies failed to install"
    }

    # Install additional optional dependency groups
    local optional_groups=("security" "docs" "debugging")
    for group in "${optional_groups[@]}"; do
        log_info "Installing $group dependencies..."
        uv sync --extra "$group" || {
            log_warning "Failed to install $group dependencies, continuing..."
        }
    done

    log_success "Python environment setup complete"
    log_info "Available tools: black, ruff, isort, mypy, pytest, bandit, safety"
}

# Install advanced security analysis tools
install_security_tools() {
    log_info "Installing security analysis tools..."

    # Security dependency groups from pyproject.toml
    local security_groups=(
        "security"
        "malware-analysis"
    )

    for group in "${security_groups[@]}"; do
        log_info "Installing $group dependencies..."
        uv pip install -e ".[${group}]" || {
            log_warning "Failed to install $group dependencies, continuing..."
        }
    done

    # Install system-level security tools if available
    install_system_security_tools

    log_success "Security tools installation complete"
}

# Install system-level security tools
install_system_security_tools() {
    log_info "Checking for system-level security tools..."

    # Detect package manager
    if command_exists apt-get; then
        PKG_MANAGER="apt-get"
        INSTALL_CMD="sudo apt-get install -y"
    elif command_exists dnf; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
    elif command_exists pacman; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
    elif command_exists brew; then
        PKG_MANAGER="brew"
        INSTALL_CMD="brew install"
    else
        log_warning "No supported package manager found, skipping system tools"
        return
    fi

    log_info "Found package manager: $PKG_MANAGER"

    # Essential security tools
    local tools=()

    case $PKG_MANAGER in
        "apt-get")
            tools=("clamav" "clamav-daemon" "rkhunter" "chkrootkit" "lynis")
            ;;
        "dnf")
            tools=("clamav" "clamav-update" "rkhunter" "chkrootkit")
            ;;
        "pacman")
            tools=("clamav" "rkhunter" "chkrootkit")
            ;;
        "brew")
            tools=("clamav" "rkhunter")
            ;;
    esac

    for tool in "${tools[@]}"; do
        if ! command_exists "$tool"; then
            log_info "Installing $tool..."
            $INSTALL_CMD "$tool" || log_warning "Failed to install $tool"
        else
            log_success "$tool already installed"
        fi
    done
}

# Setup development tools and configuration
setup_development_tools() {
    log_info "Setting up development tools..."

    # Install development dependencies
    uv pip install -e ".[dev]" || {
        log_warning "Failed to install dev dependencies"
    }

    # Setup configuration files
    setup_configuration_files

    log_success "Development tools setup complete"
}

# Setup configuration files
setup_configuration_files() {
    log_info "Setting up configuration files..."

    # Create necessary directories
    mkdir -p logs config/yara_rules .uv-cache

    # Create basic YARA rules directory
    if [ ! -f "config/yara_rules/README.md" ]; then
        cat > config/yara_rules/README.md << EOF
# YARA Rules Directory

This directory contains YARA rules for malware detection.

## Usage
- Place your custom YARA rules in this directory
- Rules should have .yar or .yara extension
- Follow YARA rule syntax: https://yara.readthedocs.io/

## Default Rules
The application will automatically load rules from this directory on startup.
EOF
        log_success "Created YARA rules directory"
    fi

    # Create logs directory
    if [ ! -f "logs/README.md" ]; then
        cat > logs/README.md << EOF
# Logs Directory

This directory contains application logs.

## Log Files
- security.log: Security events and malware detection
- application.log: General application events
- debug.log: Debug information (development only)

## Rotation
Logs are automatically rotated when they exceed configured size limits.
EOF
        log_success "Created logs directory"
    fi
}

# Configure security settings
configure_security() {
    log_info "Configuring security settings..."

    # Update ClamAV database if installed
    if command_exists freshclam; then
        log_info "Updating ClamAV virus database..."
        sudo freshclam 2>/dev/null || {
            log_warning "Failed to update ClamAV database"
        }
    fi

    # Set appropriate file permissions
    chmod 750 scripts/tools/*.sh 2>/dev/null || true
    chmod 644 config/*.toml config/*.json 2>/dev/null || true

    log_success "Security configuration complete"
}

# Setup pre-commit hooks
setup_precommit_hooks() {
    log_info "Setting up pre-commit hooks..."

    if command_exists pre-commit; then
        pre-commit install || {
            log_warning "Failed to install pre-commit hooks"
        }
        log_success "Pre-commit hooks installed"
    else
        log_warning "pre-commit not available, skipping hooks setup"
    fi
}

# Validate the setup
validate_setup() {
    log_info "Validating installation..."

    # Check Python environment
    if python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
        log_success "Python environment OK"
    else
        log_error "Python environment validation failed"
    fi

    # Check critical dependencies for core functionality
    local critical_deps=("numpy" "schedule" "aiohttp" "inotify" "dnspython" "PyQt6" "psutil" "cryptography")
    local failed_deps=()
    
    for dep in "${critical_deps[@]}"; do
        if python -c "import ${dep}" 2>/dev/null; then
            log_success "$dep import OK"
        else
            log_warning "$dep import failed"
            failed_deps+=("$dep")
        fi
    done

    # Check optional dependencies
    local optional_deps=("yara" "pycryptodome" "scapy")
    for dep in "${optional_deps[@]}"; do
        if python -c "import ${dep}" 2>/dev/null; then
            log_success "$dep import OK (optional)"
        else
            log_warning "$dep import failed (optional)"
        fi
    done

    # Report results
    if [[ ${#failed_deps[@]} -eq 0 ]]; then
        log_success "All critical dependencies validated!"
    else
        log_warning "Some critical dependencies failed: ${failed_deps[*]}"
        log_info "Run 'scripts/setup/ensure-deps.sh' to fix missing dependencies"
    fi

    # Check configuration files
    if [ -f "config/security_config.toml" ]; then
        log_success "Security configuration found"
    else
        log_warning "Security configuration missing"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    log_info "Setup complete! Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   source .venv/bin/activate"
    echo ""
    echo "2. Verify all dependencies (recommended):"
    echo "   ./scripts/setup/ensure-deps.sh"
    echo ""
    echo "3. Run the application:"
    echo "   python -m app.main"
    echo "   # OR using Make: make run"
    echo ""
    echo "4. Run tests:"
    echo "   pytest"
    echo "   # OR using Make: make test"
    echo ""
    echo "5. Run security scan:"
    echo "   bandit -r app/"
    echo ""
    echo "6. Format code:"
    echo "   ruff format ."
    echo ""
    echo "7. For development with uv:"
    echo "   uv run python -m app.main"
    echo "   uv add <package-name>  # Add new dependencies"
    echo "   uv sync               # Sync dependencies"
    echo ""
    log_success "Happy coding! 🚀"
}

# Run main function
main "$@"
