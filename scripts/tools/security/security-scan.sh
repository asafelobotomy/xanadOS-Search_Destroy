#!/bin/bash
# Tool: security-scan.sh
# Purpose: Comprehensive security scanning for vulnerabilities and compliance
# Usage: ./security-scan.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="security-scan"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive security scanning for vulnerabilities and compliance"

# Configuration
LOG_DIR="logs/toolshed"
DRY_RUN=false
VERBOSE=false
OUTPUT_FORMAT="text"
SEVERITY_THRESHOLD="medium"

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

# Severity mapping helpers (maps our threshold to each tool's flags)
map_severities() {
    local thr="${SEVERITY_THRESHOLD,,}"  # normalize to lowercase

    # Semgrep expects one of: INFO | WARNING | ERROR (we use threshold)
    case "$thr" in
        low)      SEMGREP_SEVERITY="INFO" ;;
        medium)   SEMGREP_SEVERITY="WARNING" ;;
        high)     SEMGREP_SEVERITY="ERROR" ;;
        critical) SEMGREP_SEVERITY="ERROR" ;;
        *)        SEMGREP_SEVERITY="WARNING" ;;
    esac

    # Trivy accepts comma list of severities to include
    case "$thr" in
        low)      TRIVY_SEVERITIES="LOW,MEDIUM,HIGH,CRITICAL" ;;
        medium)   TRIVY_SEVERITIES="MEDIUM,HIGH,CRITICAL" ;;
        high)     TRIVY_SEVERITIES="HIGH,CRITICAL" ;;
        critical) TRIVY_SEVERITIES="CRITICAL" ;;
        *)        TRIVY_SEVERITIES="MEDIUM,HIGH,CRITICAL" ;;
    esac

    # Bandit severity
    case "$thr" in
        low)      BANDIT_SEVERITY="low" ;;
        medium)   BANDIT_SEVERITY="medium" ;;
        high)     BANDIT_SEVERITY="high" ;;
        critical) BANDIT_SEVERITY="high" ;; # bandit max is high
        *)        BANDIT_SEVERITY="medium" ;;
    esac

    # Checkov uses a threshold-like value
    case "$thr" in
        low)      CHECKOV_SEVERITY="LOW" ;;
        medium)   CHECKOV_SEVERITY="MEDIUM" ;;
        high)     CHECKOV_SEVERITY="HIGH" ;;
        critical) CHECKOV_SEVERITY="CRITICAL" ;;
        *)        CHECKOV_SEVERITY="MEDIUM" ;;
    esac

    # npm audit level
    case "$thr" in
        low)      NPM_AUDIT_LEVEL="low" ;;
        medium)   NPM_AUDIT_LEVEL="moderate" ;;
        high)     NPM_AUDIT_LEVEL="high" ;;
        critical) NPM_AUDIT_LEVEL="critical" ;;
        *)        NPM_AUDIT_LEVEL="moderate" ;;
    esac
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool performs comprehensive security scanning including:
- SAST (Static Application Security Testing)
- Dependency vulnerability scanning
- Container/Docker security scanning
- Infrastructure as Code (IaC) security scanning
- Secrets detection
- License compliance checking

Options:
    -h, --help              Show this help message
    -d, --dry-run           Preview changes without executing
    -v, --verbose           Enable verbose output
    -o, --output FORMAT     Output format (text|json|sarif) [default: text]
    -s, --severity LEVEL    Minimum severity threshold (low|medium|high|critical) [default: medium]
    --sast-only            Run only static analysis security testing
    --deps-only            Run only dependency scanning
    --containers-only      Run only container security scanning
    --iac-only             Run only infrastructure as code scanning
    --secrets-only         Run only secrets detection
    --license-only         Run only license compliance checking
    --all                  Run all security scans (default)

Examples:
    $0                              # Run all security scans
    $0 --sast-only                  # Run only static analysis
    $0 --deps-only --output json    # Run dependency scan with JSON output
    $0 --severity high              # Show only high and critical issues
    $0 --containers-only            # Scan Docker containers only

Security Tools Used:
    ✓ Semgrep - SAST scanning for multiple languages
    ✓ Bandit - Python security scanning
    ✓ ESLint Security - JavaScript security rules
    ✓ Trivy - Container and dependency vulnerability scanning
    ✓ Checkov - Infrastructure as Code security scanning
    ✓ detect-secrets - Secrets detection
    ✓ FOSSA/License-Checker - License compliance
    ✓ Safety - Python dependency scanning
    ✓ npm audit - Node.js dependency scanning

EOF
}

# Check if required tools are available
check_dependencies() {
    local required_tools=()
    local missing_tools=()

    # Add tools based on what we find in the repository
    if [[ -f "package.json" ]]; then
        required_tools+=("npm")
    fi

    if [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]] || [[ -f "Pipfile" ]]; then
        required_tools+=("python" "pip")
    fi

    if [[ -f "Dockerfile" ]] || [[ -d ".docker" ]]; then
        required_tools+=("docker")
    fi

    # Check for missing tools
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warning "Missing tools: ${missing_tools[*]}"
        log_info "Some scans may be skipped. Install missing tools for complete coverage."
    fi
}

# Install security tools if not available
install_security_tools() {
    log_info "Checking and installing security tools..."

    # Install semgrep for SAST
    if ! command -v semgrep &> /dev/null; then
        log_info "Installing semgrep..."
        if [[ "$DRY_RUN" == "false" ]]; then
            pip install semgrep
        fi
    fi

    # Install trivy for container/dependency scanning
    if ! command -v trivy &> /dev/null; then
        log_info "Installing trivy..."
        if [[ "$DRY_RUN" == "false" ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y wget apt-transport-https gnupg lsb-release
                wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
                echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
                sudo apt-get update && sudo apt-get install -y trivy
            elif command -v brew &> /dev/null; then
                brew install trivy
            fi
        fi
    fi

    # Install checkov for IaC scanning
    if ! command -v checkov &> /dev/null; then
        log_info "Installing checkov..."
        if [[ "$DRY_RUN" == "false" ]]; then
            pip install checkov
        fi
    fi

    # Install detect-secrets
    if ! command -v detect-secrets &> /dev/null; then
        log_info "Installing detect-secrets..."
        if [[ "$DRY_RUN" == "false" ]]; then
            pip install detect-secrets
        fi
    fi
}

# Run SAST (Static Application Security Testing)
run_sast_scan() {
    log_info "Running SAST security scanning..."

    local output_file="security-sast-report"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run SAST scanning with semgrep"
        return 0
    fi

    # Run semgrep for general SAST
    if command -v semgrep &> /dev/null; then
        case $OUTPUT_FORMAT in
            "json")
                semgrep --config=auto --severity "$SEMGREP_SEVERITY" --json --output="${output_file}.json" .
                ;;
            "sarif")
                semgrep --config=auto --severity "$SEMGREP_SEVERITY" --sarif --output="${output_file}.sarif" .
                ;;
            *)
                semgrep --config=auto --severity "$SEMGREP_SEVERITY" .
                ;;
        esac
        log_success "SAST scan completed"
    else
        log_warning "Semgrep not available, skipping SAST scan"
    fi

    # Run Python-specific security scanning
    if [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
    if command -v bandit &> /dev/null; then
            log_info "Running Python security scan with bandit..."
            case $OUTPUT_FORMAT in
                "json")
            bandit -r . --severity-level "$BANDIT_SEVERITY" -f json -o "security-python-report.json" || true
                    ;;
                *)
            bandit -r . --severity-level "$BANDIT_SEVERITY" || true
                    ;;
            esac
        else
        pip install bandit
        bandit -r . --severity-level "$BANDIT_SEVERITY" || true
        fi
    fi
}

# Run dependency vulnerability scanning
run_dependency_scan() {
    log_info "Running dependency vulnerability scanning..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run dependency vulnerability scanning"
        return 0
    fi

    # Scan Python dependencies
    if [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
        log_info "Scanning Python dependencies..."

        # Use safety for Python dependency scanning
        if command -v safety &> /dev/null; then
            case $OUTPUT_FORMAT in
                "json")
                    safety check --json --output "security-python-deps.json" || true
                    ;;
                *)
                    safety check || true
                    ;;
            esac
        else
            pip install safety
            safety check || true
        fi

        # Use trivy for Python dependencies
        if command -v trivy &> /dev/null; then
            case $OUTPUT_FORMAT in
                "sarif")
                    trivy fs --security-checks vuln --severity "$TRIVY_SEVERITIES" --format sarif --output "security-python-deps.sarif" . || true
                    ;;
                *)
                    trivy fs --security-checks vuln --severity "$TRIVY_SEVERITIES" . || true
                    ;;
            esac
        fi
    fi

    # Scan Node.js dependencies
    if [[ -f "package.json" ]]; then
        log_info "Scanning Node.js dependencies..."

    if command -v npm &> /dev/null; then
            case $OUTPUT_FORMAT in
                "json")
            npm audit --audit-level "$NPM_AUDIT_LEVEL" --json > "security-npm-audit.json" || true
                    ;;
                *)
            npm audit --audit-level "$NPM_AUDIT_LEVEL" || true
                    ;;
            esac
        fi

        # Use trivy for Node.js dependencies
        if command -v trivy &> /dev/null; then
            trivy fs --security-checks vuln . || true
        fi
    fi
}

# Run container security scanning
run_container_scan() {
    log_info "Running container security scanning..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run container security scanning"
        return 0
    fi

    # Find Docker files and images
    if [[ -f "Dockerfile" ]]; then
        log_info "Scanning Dockerfile..."

        if command -v trivy &> /dev/null; then
            case $OUTPUT_FORMAT in
                "json")
                    trivy config --severity "$TRIVY_SEVERITIES" --format json --output "security-dockerfile.json" Dockerfile || true
                    ;;
                "sarif")
                    trivy config --severity "$TRIVY_SEVERITIES" --format sarif --output "security-dockerfile.sarif" Dockerfile || true
                    ;;
                *)
                    trivy config --severity "$TRIVY_SEVERITIES" Dockerfile || true
                    ;;
            esac
        fi

        # Scan built images if Docker is available
        if command -v docker &> /dev/null; then
            local images
            images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>" | head -5)
            for image in $images; do
                log_info "Scanning Docker image: $image"
                if command -v trivy &> /dev/null; then
                    case $OUTPUT_FORMAT in
                        "sarif")
                            trivy image --severity "$TRIVY_SEVERITIES" --format sarif -o "security-image-$(echo "$image" | tr '/:' '__').sarif" "$image" || true
                            ;;
                        *)
                            trivy image --severity "$TRIVY_SEVERITIES" "$image" || true
                            ;;
                    esac
                fi
            done
        fi
    fi
}

# Run Infrastructure as Code scanning
run_iac_scan() {
    log_info "Running Infrastructure as Code security scanning..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run IaC security scanning"
        return 0
    fi

    # Look for IaC files
    local iac_files
    iac_files=$(find . -name "*.tf" -o -name "*.yaml" -o -name "*.yml" -o -name "Dockerfile" -o -name "docker-compose.yml" | grep -v node_modules | head -20)

    if [[ -n "$iac_files" ]]; then
        log_info "Found IaC files, running checkov scan..."

        if command -v checkov &> /dev/null; then
            case $OUTPUT_FORMAT in
                "json")
                    checkov -d . --framework all --severity "$CHECKOV_SEVERITY" --output json --output-file "security-iac-report.json" || true
                    ;;
                "sarif")
                    checkov -d . --framework all --severity "$CHECKOV_SEVERITY" --output sarif --output-file-path "security-iac-report.sarif" || true
                    ;;
                *)
                    checkov -d . --framework all --severity "$CHECKOV_SEVERITY" || true
                    ;;
            esac
        else
            log_warning "Checkov not available, skipping IaC scan"
        fi
    else
        log_info "No IaC files found, skipping IaC scan"
    fi
}

# Run secrets detection
run_secrets_scan() {
    log_info "Running secrets detection..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run secrets detection"
        return 0
    fi

    if command -v detect-secrets &> /dev/null; then
        # Create baseline if it doesn't exist (detect-secrets expects output redirection for baseline)
        if [[ ! -f ".secrets.baseline" ]]; then
            log_info "Creating detect-secrets baseline at .secrets.baseline"
            detect-secrets scan --all-files > .secrets.baseline || true
        fi

        # Run secrets scan; when baseline exists, use it to filter known secrets
        case $OUTPUT_FORMAT in
            "json")
                if [[ -f ".secrets.baseline" ]]; then
                    detect-secrets scan --all-files --baseline .secrets.baseline > "security-secrets-report.json" || true
                else
                    detect-secrets scan --all-files > "security-secrets-report.json" || true
                fi
                ;;
            *)
                if [[ -f ".secrets.baseline" ]]; then
                    detect-secrets scan --all-files --baseline .secrets.baseline || true
                else
                    detect-secrets scan --all-files || true
                fi
                ;;
        esac

        log_success "Secrets detection completed"
    else
        log_warning "detect-secrets not available, skipping secrets scan"
    fi
}

# Run license compliance checking
run_license_scan() {
    log_info "Running license compliance checking..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run license compliance checking"
        return 0
    fi

    # Check Python licenses
    if [[ -f "requirements.txt" ]]; then
        if command -v pip-licenses &> /dev/null; then
            case $OUTPUT_FORMAT in
                "json")
                    pip-licenses --format=json --output-file="security-python-licenses.json" || true
                    ;;
                *)
                    pip-licenses || true
                    ;;
            esac
        else
            pip install pip-licenses
            pip-licenses || true
        fi
    fi

    # Check Node.js licenses
    if [[ -f "package.json" ]]; then
        if command -v license-checker &> /dev/null; then
            case $OUTPUT_FORMAT in
                "json")
                    license-checker --json --out "security-npm-licenses.json" || true
                    ;;
                *)
                    license-checker || true
                    ;;
            esac
        else
            npm install -g license-checker
            license-checker || true
        fi
    fi
}

# Generate comprehensive security report
generate_security_report() {
    log_info "Generating comprehensive security report..."

    local report_file="security-comprehensive-report.md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would generate security report"
        return 0
    fi

    cat > "$report_file" << EOF
# Security Scan Report

**Generated**: $(date)
**Repository**: $(basename "$(pwd)")
**Severity Threshold**: $SEVERITY_THRESHOLD

## Summary

This report contains the results of comprehensive security scanning including:

- ✅ Static Application Security Testing (SAST)
- ✅ Dependency Vulnerability Scanning
- ✅ Container Security Scanning
- ✅ Infrastructure as Code (IaC) Scanning
- ✅ Secrets Detection
- ✅ License Compliance Checking

## Scan Results

### SAST Results
$(if [[ -f "security-sast-report.json" ]]; then echo "See security-sast-report.json for detailed results"; else echo "No SAST report generated"; fi)

### Dependency Scan Results
$(if [[ -f "security-python-deps.json" ]]; then echo "Python dependencies: See security-python-deps.json"; fi)
$(if [[ -f "security-npm-audit.json" ]]; then echo "Node.js dependencies: See security-npm-audit.json"; fi)

### Container Scan Results
$(if [[ -f "security-dockerfile.json" ]]; then echo "Dockerfile scan: See security-dockerfile.json"; fi)

### IaC Scan Results
$(if [[ -f "security-iac-report.json" ]]; then echo "IaC scan: See security-iac-report.json"; fi)

### Secrets Detection Results
$(if [[ -f "security-secrets-report.json" ]]; then echo "Secrets scan: See security-secrets-report.json"; fi)

### License Compliance Results
$(if [[ -f "security-python-licenses.json" ]]; then echo "Python licenses: See security-python-licenses.json"; fi)
$(if [[ -f "security-npm-licenses.json" ]]; then echo "Node.js licenses: See security-npm-licenses.json"; fi)

## Next Steps

1. Review all identified vulnerabilities and security issues
2. Prioritize fixes based on severity (Critical > High > Medium > Low)
3. Update dependencies to latest secure versions
4. Fix any secrets detected in code
5. Address any license compliance issues
6. Re-run security scan after fixes

## Tools Used

- Semgrep (SAST)
- Trivy (Container/Dependency scanning)
- Bandit (Python security)
- Safety (Python dependencies)
- npm audit (Node.js dependencies)
- Checkov (IaC scanning)
- detect-secrets (Secrets detection)
- License checkers (Compliance)

EOF

    log_success "Security report generated: $report_file"
}

# Main execution function
main() {
    local scan_type="all"

    # Create log directory
    mkdir -p "$LOG_DIR"

    log_info "Starting comprehensive security scanning..."

    # Check dependencies
    check_dependencies

    # Install required tools
    install_security_tools

    # Enable verbose tracing if requested
    if [[ "${VERBOSE:-false}" == "true" ]]; then
        log_info "Verbose mode enabled"
        set -x
    fi

    # Map severities for tools
    map_severities

    # Run scans based on options
    case $scan_type in
        "sast"|"all")
            run_sast_scan
            ;;& # Continue to next case
        "deps"|"all")
            run_dependency_scan
            ;;& # Continue to next case
        "containers"|"all")
            run_container_scan
            ;;& # Continue to next case
        "iac"|"all")
            run_iac_scan
            ;;& # Continue to next case
        "secrets"|"all")
            run_secrets_scan
            ;;& # Continue to next case
        "license"|"all")
            run_license_scan
            ;;
    esac

    # Generate comprehensive report
    generate_security_report

    echo ""
    log_success "Security scanning completed!"
    echo ""
    echo "Reports generated:"
    echo "- Comprehensive report: security-comprehensive-report.md"
    if [[ -f "security-sast-report.json" ]]; then echo "- SAST report: security-sast-report.json"; fi
    if [[ -f "security-python-deps.json" ]]; then echo "- Python deps: security-python-deps.json"; fi
    if [[ -f "security-npm-audit.json" ]]; then echo "- Node.js deps: security-npm-audit.json"; fi
    echo ""
    echo "Next steps:"
    echo "1. Review all security reports"
    echo "2. Fix critical and high severity issues first"
    echo "3. Update dependencies and re-scan"
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
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -s|--severity)
            SEVERITY_THRESHOLD="$2"
            shift 2
            ;;
        --sast-only)
            scan_type="sast"
            shift
            ;;
        --deps-only)
            scan_type="deps"
            shift
            ;;
        --containers-only)
            scan_type="containers"
            shift
            ;;
        --iac-only)
            scan_type="iac"
            shift
            ;;
        --secrets-only)
            scan_type="secrets"
            shift
            ;;
        --license-only)
            scan_type="license"
            shift
            ;;
        --all)
            scan_type="all"
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
