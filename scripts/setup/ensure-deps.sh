#!/usr/bin/env bash
# Dependency Verification and Auto-Installation Script
# Ensures all critical dependencies are installed for xanadOS Search & Destroy

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

# Check if we're in the project root
check_project_root() {
    if [[ ! -f "pyproject.toml" ]] || [[ ! -f "app/main.py" ]]; then
        log_error "This script must be run from the xanadOS-Search_Destroy project root"
        exit 1
    fi
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -d ".venv" ]]; then
        log_warning "Virtual environment not found. Creating one..."
        
        # Check for UV first
        if command -v uv >/dev/null 2>&1; then
            log_info "Using UV to create virtual environment..."
            uv venv .venv --python python3
        else
            log_info "Using standard venv..."
            python3 -m venv .venv
        fi
        
        log_success "Virtual environment created"
    else
        log_success "Virtual environment found"
    fi
}

# Install dependencies using UV or pip
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Use UV if available for faster installation
    if command -v uv >/dev/null 2>&1; then
        log_info "Using UV for fast dependency installation..."
        uv pip install -e .
        uv pip install -e ".[dev]"
    else
        log_info "Using pip for dependency installation..."
        pip install --upgrade pip
        pip install -e .
        pip install -e ".[dev]"
    fi
    
    log_success "Dependencies installed"
}

# Validate critical modules
validate_modules() {
    log_info "Validating critical modules..."
    
    source .venv/bin/activate
    
    # Critical modules for application functionality
    local modules=(
        "numpy:Unified Security Engine"
        "schedule:Scheduled scanning"
        "aiohttp:Async operations" 
        "inotify:File system monitoring"
        "dns:DNS analysis"
        "PyQt6:GUI framework"
        "psutil:System monitoring"
        "cryptography:Security features"
    )
    
    local failed_modules=()
    
    for module_info in "${modules[@]}"; do
        local module
        local purpose
        module=$(echo "$module_info" | cut -d: -f1)
        purpose=$(echo "$module_info" | cut -d: -f2)
        
        if python -c "import $module" 2>/dev/null; then
            log_success "$module (${purpose})"
        else
            log_error "$module (${purpose}) - MISSING"
            failed_modules+=("$module")
        fi
    done
    
    if [[ ${#failed_modules[@]} -eq 0 ]]; then
        log_success "All critical modules validated successfully!"
        return 0
    else
        log_error "Failed modules: ${failed_modules[*]}"
        return 1
    fi
}

# Test application startup
test_startup() {
    log_info "Testing application startup..."
    
    source .venv/bin/activate
    
    # Test import without starting GUI
    if timeout 10s python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.core.unified_security_engine import UnifiedSecurityEngine
    from app.core.file_scanner import FileScanner
    print('Core modules imported successfully')
except Exception as e:
    print(f'Import error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "Application core modules load successfully"
    else
        log_warning "Application startup test failed - check dependencies"
        return 1
    fi
}

# Update lock file
update_lockfile() {
    if command -v uv >/dev/null 2>&1; then
        log_info "Updating UV lock file..."
        uv lock
        log_success "Lock file updated"
    fi
}

# Main execution
main() {
    # Check for validate-only flag
    local validate_only=false
    if [[ "${1:-}" == "--validate-only" ]]; then
        validate_only=true
        shift
    fi
    
    echo "🔧 xanadOS Search & Destroy - Dependency Setup & Validation"
    echo "============================================================"
    
    check_project_root
    
    if [[ "$validate_only" == "true" ]]; then
        # Only validate, don't install
        log_info "Validation-only mode"
        if [[ ! -d ".venv" ]]; then
            log_error "Virtual environment not found"
            exit 1
        fi
        validate_modules
        exit $?
    fi
    
    check_venv
    install_dependencies
    
    if validate_modules; then
        test_startup
        update_lockfile
        
        echo ""
        log_success "🎉 Environment setup complete!"
        echo ""
        echo "Next steps:"
        echo "  1. Activate environment: source .venv/bin/activate"
        echo "  2. Run application: python -m app.main"
        echo "  3. Run tests: pytest"
        echo "  4. Or use Make: make run"
        echo ""
    else
        log_error "Environment setup failed - some dependencies are missing"
        echo ""
        echo "Try manual installation:"
        echo "  source .venv/bin/activate"
        echo "  pip install -e ."
        echo "  pip install -e \".[dev]\""
        exit 1
    fi
}

# Run main function
main "$@"
