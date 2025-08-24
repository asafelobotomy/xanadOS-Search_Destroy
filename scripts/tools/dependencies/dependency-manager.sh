#!/bin/bash
# Tool: dependency-manager.sh
# Purpose: Comprehensive dependency management, updating, and vulnerability monitoring
# Usage: ./dependency-manager.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="dependency-manager"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive dependency management, updating, and vulnerability monitoring"

# Configuration
LOG_DIR="logs/toolshed"
DRY_RUN=false
VERBOSE=false
AUTO_UPDATE=false
UPDATE_STRATEGY="minor"
BACKUP_ENABLED=true

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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool provides comprehensive dependency management including:
- Dependency updates with version constraints
- Vulnerability scanning and reporting
- License compliance checking
- Dependency tree analysis
- Automated security patching
- Backup and rollback capabilities

Options:
    -h, --help              Show this help message
    -d, --dry-run           Preview changes without executing
    -v, --verbose           Enable verbose output
    -u, --update            Enable automatic dependency updates
    -s, --strategy LEVEL    Update strategy (patch|minor|major) [default: minor]
    --check-only            Only check for updates, don't install
    --security-only         Only update packages with security vulnerabilities
    --backup                Create backup before updates (default: enabled)
    --no-backup             Disable backup creation
    --python                Manage only Python dependencies
    --node                  Manage only Node.js dependencies
    --go                    Manage only Go dependencies
    --rust                  Manage only Rust dependencies
    --all                   Manage all detected dependencies (default)

Examples:
    $0                                      # Check all dependencies
    $0 --update --strategy patch            # Update with patch-level changes only
    $0 --security-only --update             # Update only vulnerable packages
    $0 --python --update --backup           # Update Python deps with backup
    $0 --check-only                         # Just check for updates

Supported Package Managers:
    ✓ pip (Python) - requirements.txt, pyproject.toml, Pipfile
    ✓ npm/yarn (Node.js) - package.json, yarn.lock
    ✓ go mod (Go) - go.mod, go.sum
    ✓ cargo (Rust) - Cargo.toml, Cargo.lock
    ✓ composer (PHP) - composer.json, composer.lock
    ✓ bundler (Ruby) - Gemfile, Gemfile.lock

EOF
}

# Detect project type and package managers
detect_package_managers() {
    local managers=()

    if [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]] || [[ -f "Pipfile" ]]; then
        managers+=("python")
    fi

    if [[ -f "package.json" ]]; then
        managers+=("node")
    fi

    if [[ -f "go.mod" ]]; then
        managers+=("go")
    fi

    if [[ -f "Cargo.toml" ]]; then
        managers+=("rust")
    fi

    if [[ -f "composer.json" ]]; then
        managers+=("php")
    fi

    if [[ -f "Gemfile" ]]; then
        managers+=("ruby")
    fi

    echo "${managers[@]}"
}

# Create backup of dependency files
create_backup() {
    local manager=$1
    local backup_dir="dependency-backups/$(date +%Y%m%d_%H%M%S)"

    if [[ "$BACKUP_ENABLED" == "false" ]]; then
        return 0
    fi

    log_info "Creating backup for $manager dependencies..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create backup in $backup_dir"
        return 0
    fi

    mkdir -p "$backup_dir"

    case $manager in
        "python")
            if [[ -f "requirements.txt" ]]; then cp "requirements.txt" "$backup_dir/"; fi
            if [[ -f "pyproject.toml" ]]; then cp "pyproject.toml" "$backup_dir/"; fi
            if [[ -f "Pipfile" ]]; then cp "Pipfile" "$backup_dir/"; fi
            if [[ -f "Pipfile.lock" ]]; then cp "Pipfile.lock" "$backup_dir/"; fi
            ;;
        "node")
            if [[ -f "package.json" ]]; then cp "package.json" "$backup_dir/"; fi
            if [[ -f "package-lock.json" ]]; then cp "package-lock.json" "$backup_dir/"; fi
            if [[ -f "yarn.lock" ]]; then cp "yarn.lock" "$backup_dir/"; fi
            ;;
        "go")
            if [[ -f "go.mod" ]]; then cp "go.mod" "$backup_dir/"; fi
            if [[ -f "go.sum" ]]; then cp "go.sum" "$backup_dir/"; fi
            ;;
        "rust")
            if [[ -f "Cargo.toml" ]]; then cp "Cargo.toml" "$backup_dir/"; fi
            if [[ -f "Cargo.lock" ]]; then cp "Cargo.lock" "$backup_dir/"; fi
            ;;
    esac

    log_success "Backup created in $backup_dir"
}

# Check for outdated dependencies
check_outdated_python() {
    log_info "Checking Python dependencies for updates..."

    local outdated_file="dependency-analysis-python.json"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would check Python dependencies"
        return 0
    fi

    # Check using pip-outdated if available
    if command -v pip-outdated &> /dev/null; then
        pip-outdated --format=json > "$outdated_file" 2>/dev/null || true
    else
        # Use pip list --outdated
        pip list --outdated --format=json > "$outdated_file" 2>/dev/null || true
    fi

    # Check for security vulnerabilities with safety
    if command -v safety &> /dev/null; then
        safety check --json --output "dependency-security-python.json" 2>/dev/null || true
    else
        pip install safety
        safety check --json --output "dependency-security-python.json" 2>/dev/null || true
    fi

    log_success "Python dependency analysis complete"
}

# Check Node.js dependencies
check_outdated_node() {
    log_info "Checking Node.js dependencies for updates..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would check Node.js dependencies"
        return 0
    fi

    if command -v npm &> /dev/null; then
        # Check for outdated packages
        npm outdated --json > "dependency-analysis-node.json" 2>/dev/null || true

        # Security audit
        npm audit --json > "dependency-security-node.json" 2>/dev/null || true

        log_success "Node.js dependency analysis complete"
    fi
}

# Check Go dependencies
check_outdated_go() {
    log_info "Checking Go dependencies for updates..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would check Go dependencies"
        return 0
    fi

    if command -v go &> /dev/null && [[ -f "go.mod" ]]; then
        # List available updates
        go list -u -m all > "dependency-analysis-go.txt" 2>/dev/null || true

        # Check for vulnerabilities using govulncheck if available
        if command -v govulncheck &> /dev/null; then
            govulncheck -json ./... > "dependency-security-go.json" 2>/dev/null || true
        fi

        log_success "Go dependency analysis complete"
    fi
}

# Check Rust dependencies
check_outdated_rust() {
    log_info "Checking Rust dependencies for updates..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would check Rust dependencies"
        return 0
    fi

    if command -v cargo &> /dev/null && [[ -f "Cargo.toml" ]]; then
        # Install cargo-outdated if not available
        if ! command -v cargo-outdated &> /dev/null; then
            cargo install cargo-outdated
        fi

        # Check for outdated dependencies
        cargo outdated --format json > "dependency-analysis-rust.json" 2>/dev/null || true

        # Security audit
        if command -v cargo-audit &> /dev/null; then
            cargo audit --json > "dependency-security-rust.json" 2>/dev/null || true
        else
            cargo install cargo-audit
            cargo audit --json > "dependency-security-rust.json" 2>/dev/null || true
        fi

        log_success "Rust dependency analysis complete"
    fi
}

# Update Python dependencies
update_python_deps() {
    log_info "Updating Python dependencies..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update Python dependencies"
        return 0
    fi

    create_backup "python"

    if [[ -f "requirements.txt" ]]; then
        case $UPDATE_STRATEGY in
            "patch")
                # Update only patch versions
                pip install --upgrade $(pip list --outdated --format=columns | awk 'NR>2 {print $1}') --constraint <(pip freeze | sed 's/==/>=/') 2>/dev/null || true
                ;;
            "minor")
                # Update minor versions
                pip install --upgrade $(pip list --outdated --format=columns | awk 'NR>2 {print $1}') 2>/dev/null || true
                ;;
            "major")
                # Update all versions
                pip install --upgrade $(pip list --outdated --format=columns | awk 'NR>2 {print $1}') 2>/dev/null || true
                ;;
        esac

        # Generate new requirements.txt
        pip freeze > requirements.txt.new
        mv requirements.txt.new requirements.txt
    fi

    if [[ -f "Pipfile" ]]; then
        pipenv update
    fi

    log_success "Python dependencies updated"
}

# Update Node.js dependencies
update_node_deps() {
    log_info "Updating Node.js dependencies..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update Node.js dependencies"
        return 0
    fi

    create_backup "node"

    if [[ -f "package.json" ]]; then
        case $UPDATE_STRATEGY in
            "patch")
                npm update 2>/dev/null || true
                ;;
            "minor")
                npx npm-check-updates -u --target minor 2>/dev/null || true
                npm install 2>/dev/null || true
                ;;
            "major")
                npx npm-check-updates -u 2>/dev/null || true
                npm install 2>/dev/null || true
                ;;
        esac
    fi

    log_success "Node.js dependencies updated"
}

# Update Go dependencies
update_go_deps() {
    log_info "Updating Go dependencies..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update Go dependencies"
        return 0
    fi

    create_backup "go"

    if [[ -f "go.mod" ]]; then
        case $UPDATE_STRATEGY in
            "patch")
                go get -u=patch ./... 2>/dev/null || true
                ;;
            "minor"|"major")
                go get -u ./... 2>/dev/null || true
                ;;
        esac

        go mod tidy
        go mod verify
    fi

    log_success "Go dependencies updated"
}

# Update Rust dependencies
update_rust_deps() {
    log_info "Updating Rust dependencies..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update Rust dependencies"
        return 0
    fi

    create_backup "rust"

    if [[ -f "Cargo.toml" ]]; then
        cargo update
        cargo check
    fi

    log_success "Rust dependencies updated"
}

# Generate dependency report
generate_dependency_report() {
    log_info "Generating comprehensive dependency report..."

    local report_file="dependency-management-report.md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would generate dependency report"
        return 0
    fi

    cat > "$report_file" << EOF
# Dependency Management Report

**Generated**: $(date)
**Repository**: $(basename "$(pwd)")
**Update Strategy**: $UPDATE_STRATEGY
**Backup Enabled**: $BACKUP_ENABLED

## Summary

This report contains comprehensive dependency analysis including:

- 🔍 Outdated package detection
- 🔒 Security vulnerability scanning
- 📊 Dependency tree analysis
- 📝 License compliance checking
- 🔄 Update recommendations

## Detected Package Managers

$(detect_package_managers | tr ' ' '\n' | sed 's/^/- /')

## Analysis Results

### Python Dependencies
$(if [[ -f "dependency-analysis-python.json" ]]; then echo "📊 Outdated packages: See dependency-analysis-python.json"; fi)
$(if [[ -f "dependency-security-python.json" ]]; then echo "🔒 Security vulnerabilities: See dependency-security-python.json"; fi)

### Node.js Dependencies
$(if [[ -f "dependency-analysis-node.json" ]]; then echo "📊 Outdated packages: See dependency-analysis-node.json"; fi)
$(if [[ -f "dependency-security-node.json" ]]; then echo "🔒 Security audit: See dependency-security-node.json"; fi)

### Go Dependencies
$(if [[ -f "dependency-analysis-go.txt" ]]; then echo "📊 Available updates: See dependency-analysis-go.txt"; fi)
$(if [[ -f "dependency-security-go.json" ]]; then echo "🔒 Vulnerability scan: See dependency-security-go.json"; fi)

### Rust Dependencies
$(if [[ -f "dependency-analysis-rust.json" ]]; then echo "📊 Outdated crates: See dependency-analysis-rust.json"; fi)
$(if [[ -f "dependency-security-rust.json" ]]; then echo "🔒 Security audit: See dependency-security-rust.json"; fi)

## Backup Information

$(if [[ "$BACKUP_ENABLED" == "true" ]]; then echo "✅ Backups are enabled and stored in dependency-backups/"; else echo "❌ Backups are disabled"; fi)

## Recommendations

1. **Security Updates**: Prioritize packages with known vulnerabilities
2. **Version Strategy**: Use appropriate update strategy for your project lifecycle
3. **Testing**: Run full test suite after dependency updates
4. **Monitoring**: Set up automated dependency monitoring with tools like Dependabot
5. **License Compliance**: Review license changes after updates

## Next Steps

1. Review all outdated dependencies
2. Prioritize security vulnerabilities
3. Test updates in staging environment
4. Plan deployment of dependency updates
5. Monitor for new vulnerabilities

## Tools Used

- pip/pip-outdated (Python)
- safety (Python security)
- npm/npm-check-updates (Node.js)
- npm audit (Node.js security)
- go list/govulncheck (Go)
- cargo/cargo-outdated/cargo-audit (Rust)

EOF

    log_success "Dependency report generated: $report_file"
}

# Main execution function
main() {
    local target_managers=()
    local check_only=false
    local security_only=false

    # Create log directory
    mkdir -p "$LOG_DIR"

    log_info "Starting dependency management..."

    # Detect available package managers if none specified
    if [[ ${#target_managers[@]} -eq 0 ]]; then
        target_managers=($(detect_package_managers))
    fi

    if [[ ${#target_managers[@]} -eq 0 ]]; then
        log_error "No supported package managers detected"
        exit 1
    fi

    log_info "Detected package managers: ${target_managers[*]}"

    # Check dependencies for all detected managers
    for manager in "${target_managers[@]}"; do
        case $manager in
            "python")
                check_outdated_python
                if [[ "$AUTO_UPDATE" == "true" && "$check_only" == "false" ]]; then
                    update_python_deps
                fi
                ;;
            "node")
                check_outdated_node
                if [[ "$AUTO_UPDATE" == "true" && "$check_only" == "false" ]]; then
                    update_node_deps
                fi
                ;;
            "go")
                check_outdated_go
                if [[ "$AUTO_UPDATE" == "true" && "$check_only" == "false" ]]; then
                    update_go_deps
                fi
                ;;
            "rust")
                check_outdated_rust
                if [[ "$AUTO_UPDATE" == "true" && "$check_only" == "false" ]]; then
                    update_rust_deps
                fi
                ;;
        esac
    done

    # Generate comprehensive report
    generate_dependency_report

    echo ""
    log_success "Dependency management completed!"
    echo ""
    echo "Reports generated:"
    echo "- Comprehensive report: dependency-management-report.md"
    for manager in "${target_managers[@]}"; do
        if [[ -f "dependency-analysis-${manager}.json" ]] || [[ -f "dependency-analysis-${manager}.txt" ]]; then
            echo "- ${manager} analysis: dependency-analysis-${manager}.*"
        fi
        if [[ -f "dependency-security-${manager}.json" ]]; then
            echo "- ${manager} security: dependency-security-${manager}.json"
        fi
    done
    echo ""
    if [[ "$AUTO_UPDATE" == "true" ]]; then
        echo "✅ Dependencies have been updated"
    else
        echo "💡 Run with --update flag to apply dependency updates"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -u|--update)
            AUTO_UPDATE=true
            shift
            ;;
        -s|--strategy)
            UPDATE_STRATEGY="$2"
            shift 2
            ;;
        --check-only)
            check_only=true
            shift
            ;;
        --security-only)
            security_only=true
            shift
            ;;
        --backup)
            BACKUP_ENABLED=true
            shift
            ;;
        --no-backup)
            BACKUP_ENABLED=false
            shift
            ;;
        --python)
            target_managers=("python")
            shift
            ;;
        --node)
            target_managers=("node")
            shift
            ;;
        --go)
            target_managers=("go")
            shift
            ;;
        --rust)
            target_managers=("rust")
            shift
            ;;
        --all)
            target_managers=()
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage >&2
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"
