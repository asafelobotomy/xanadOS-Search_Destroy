#!/bin/bash
# Tool: validate-setup.sh
# Purpose: Comprehensive setup validation and environment health check
# Usage: ./scripts/tools/setup/validate-setup.sh [--fix] [--verbose]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Configuration
FIX_ISSUES=false
VERBOSE=false
ISSUES_FOUND=0
FIXES_APPLIED=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_ISSUES=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            cat << EOF
Usage: $0 [options]

Options:
    --fix           Automatically fix detected issues
    --verbose       Enable verbose output
    --help          Show this help

Validates:
    • Python environment and dependencies
    • Node.js environment and package managers
    • Docker configuration
    • Security tools setup
    • File permissions and structure
    • Version synchronization
EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🔍 Setup Validation & Health Check"
echo "=================================="

# Check Python environment
check_python_environment() {
    log_info "Checking Python environment..."

    # Activate virtual environment if it exists
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
        log_info "Activated Python virtual environment"
    fi

    # Check Python version
    if command -v python >/dev/null 2>&1; then
        PYTHON_VERSION=$(python --version 2>&1)
        log_success "$PYTHON_VERSION (compatible)"
    else
        log_error "Python not found"
        ((ERRORS++))
        return 1
    fi

    # Check critical packages
    CRITICAL_PACKAGES=("requests" "yaml" "packaging" "urllib3")
    IMPORT_NAMES=("requests" "yaml" "packaging" "urllib3")

    for i in "${!CRITICAL_PACKAGES[@]}"; do
        package="${CRITICAL_PACKAGES[i]}"
        import_name="${IMPORT_NAMES[i]}"
        if python -c "import $import_name" >/dev/null 2>&1; then
            log_success "Package $package available"
        else
            log_error "Critical package missing: $package"
            ((ISSUES_FOUND++))
        fi
    done
}

# Check Node.js environment
check_node_env() {
    log_info "Checking Node.js environment..."

    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js not installed"
        ((ISSUES_FOUND++))
        return
    fi

    NODE_VERSION=$(node --version | sed 's/v//')
    log_success "Node.js $NODE_VERSION"

    # Check package manager preference
    if command -v pnpm >/dev/null 2>&1; then
        PNPM_VERSION=$(pnpm --version)
        log_success "pnpm $PNPM_VERSION (preferred)"

        # Check if pnpm is used consistently
        if [[ -f "pnpm-lock.yaml" ]] && [[ -f "package-lock.json" ]]; then
            log_warning "Both pnpm-lock.yaml and package-lock.json found"
            ((ISSUES_FOUND++))
            if [[ "$FIX_ISSUES" == "true" ]]; then
                rm -f package-lock.json
                log_info "Removed package-lock.json to use pnpm consistently"
                ((FIXES_APPLIED++))
            fi
        fi
    else
        log_warning "pnpm not installed (using npm)"
        if [[ "$FIX_ISSUES" == "true" ]]; then
            npm install -g pnpm
            ((FIXES_APPLIED++))
        fi
    fi

    # Check for modern package manager versions
    if command -v uv >/dev/null 2>&1; then
        UV_VERSION=$(uv --version | cut -d' ' -f2)
        log_success "uv $UV_VERSION (fast Python package manager)"
    else
        log_warning "uv not installed (falling back to pip)"
        if [[ "$FIX_ISSUES" == "true" ]]; then
            curl -LsSf https://astral.sh/uv/install.sh | sh
            ((FIXES_APPLIED++))
        fi
    fi
}

# Check Docker setup
check_docker_setup() {
    log_info "Checking Docker setup..."

    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker not installed"
        ((ISSUES_FOUND++))
        return
    fi

    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
    log_success "Docker $DOCKER_VERSION"

    # Check if user can run docker without sudo
    if ! docker ps >/dev/null 2>&1; then
        log_warning "Cannot run Docker without sudo"
        log_info "Add user to docker group: sudo usermod -aG docker \$USER"
        ((ISSUES_FOUND++))
    fi

    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon not running"
        ((ISSUES_FOUND++))
        if [[ "$FIX_ISSUES" == "true" ]]; then
            sudo systemctl start docker
            ((FIXES_APPLIED++))
        fi
    fi
}

# Check security tools
check_security_tools() {
    log_info "Checking security tools..."

    # ClamAV
    if command -v clamscan >/dev/null 2>&1; then
        log_success "ClamAV installed"

        # Check if virus database is up to date
        if [[ -f "/var/lib/clamav/daily.cvd" ]]; then
            CLAMAV_AGE=$(find /var/lib/clamav/daily.cvd -mtime +7 | wc -l)
            if [[ $CLAMAV_AGE -gt 0 ]]; then
                log_warning "ClamAV database is more than 7 days old"
                ((ISSUES_FOUND++))
                if [[ "$FIX_ISSUES" == "true" ]]; then
                    sudo freshclam
                    ((FIXES_APPLIED++))
                fi
            fi
        fi
    else
        log_warning "ClamAV not installed"
        ((ISSUES_FOUND++))
    fi

    # RKHunter
    if command -v rkhunter >/dev/null 2>&1; then
        log_success "RKHunter installed"
    else
        log_warning "RKHunter not installed"
        ((ISSUES_FOUND++))
    fi
}

# Check file permissions and structure
check_file_structure() {
    log_info "Checking file structure and permissions..."

    # Check script permissions
    SCRIPTS=(
        "scripts/tools/security/security-scan.sh"
        "scripts/tools/validation/enhanced-quick-validate.sh"
        "scripts/tools/setup/modern-dev-setup.sh"
    )

    for script in "${SCRIPTS[@]}"; do
        if [[ -f "$script" ]]; then
            if [[ ! -x "$script" ]]; then
                log_warning "$script is not executable"
                ((ISSUES_FOUND++))
                if [[ "$FIX_ISSUES" == "true" ]]; then
                    chmod +x "$script"
                    ((FIXES_APPLIED++))
                fi
            fi
        else
            log_error "Required script missing: $script"
            ((ISSUES_FOUND++))
        fi
    done

    # Check for requirements.txt (needed by some tests)
    if [[ ! -f "requirements.txt" ]] && [[ -f "pyproject.toml" ]]; then
        log_info "Creating requirements.txt from pyproject.toml"
        if [[ "$FIX_ISSUES" == "true" ]]; then
            source .venv/bin/activate 2>/dev/null || true
            pip freeze > requirements.txt
            ((FIXES_APPLIED++))
        else
            log_warning "requirements.txt missing (some tests may fail)"
            ((ISSUES_FOUND++))
        fi
    fi
}

# Check version synchronization
check_version_sync() {
    log_info "Checking version synchronization..."

    if [[ -f "VERSION" ]] && [[ -f "package.json" ]] && [[ -f "pyproject.toml" ]]; then
        VERSION_FILE=$(cat VERSION)
        PACKAGE_VERSION=$(grep '"version"' package.json | cut -d'"' -f4)
        PYPROJECT_VERSION=$(grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)

        if [[ "$VERSION_FILE" == "$PACKAGE_VERSION" ]] && [[ "$VERSION_FILE" == "$PYPROJECT_VERSION" ]]; then
            log_success "Version synchronized: $VERSION_FILE"
        else
            log_error "Version mismatch: VERSION=$VERSION_FILE, package.json=$PACKAGE_VERSION, pyproject.toml=$PYPROJECT_VERSION"
            ((ISSUES_FOUND++))
            if [[ "$FIX_ISSUES" == "true" ]]; then
                python scripts/tools/version/version_manager.py --sync
                ((FIXES_APPLIED++))
            fi
        fi
    fi
}

# Run all checks
check_python_environment
check_node_env
check_docker_setup
check_security_tools
check_file_structure
check_version_sync

# Summary
echo ""
echo "📊 Validation Summary"
echo "===================="
echo "Issues found: $ISSUES_FOUND"
if [[ "$FIX_ISSUES" == "true" ]]; then
    echo "Fixes applied: $FIXES_APPLIED"
fi

if [[ $ISSUES_FOUND -eq 0 ]]; then
    log_success "Environment is properly configured!"
    exit 0
elif [[ "$FIX_ISSUES" == "true" ]]; then
    if [[ $FIXES_APPLIED -gt 0 ]]; then
        log_info "Applied $FIXES_APPLIED fixes. Remaining issues may require manual intervention."
    fi
    exit 0
else
    log_warning "Found $ISSUES_FOUND issues. Run with --fix to automatically resolve some of them."
    exit 1
fi
