#!/bin/bash
# Tool: unified-test-runner.sh
# Purpose: Unified testing framework to eliminate inconsistencies
# Usage: ./scripts/tools/testing/unified-test-runner.sh [--type=TYPE] [--coverage] [--verbose]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_debug() { echo -e "${CYAN}[DEBUG]${NC} $1"; }

# Default settings
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type=*)
            TEST_TYPE="${1#*=}"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            cat << EOF
Usage: $0 [options]

Unified test runner that consolidates:
    • Python unit tests (pytest)
    • Python integration tests
    • Security tests (bandit, semgrep)
    • Code quality tests (mypy, black)
    • Node.js tests (npm test)
    • Docker tests
    • GUI tests (pytest-qt)

Options:
    --type=TYPE     Test type: all, unit, integration, security, quality, gui, docker
    --coverage      Enable coverage reporting
    --verbose       Verbose output
    --help          Show this help

Test Types:
    all             Run all test categories (default)
    unit            Python unit tests only
    integration     Integration tests
    security        Security scanning tests
    quality         Code quality and linting
    gui             GUI tests with pytest-qt
    docker          Docker container tests
    node            Node.js tests
EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

cd "$WORKSPACE_ROOT"

echo "🧪 Unified Test Runner"
echo "====================="
echo "Test Type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo "Verbose: $VERBOSE"
echo ""

# Activate Python environment
if [[ -d ".venv" ]]; then
    source .venv/bin/activate
    log_info "Activated Python virtual environment"
else
    log_error "Virtual environment not found. Run setup first."
    exit 1
fi

# Test result tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
test_results=()

# Function to record test results
record_test() {
    local test_name="$1"
    local status="$2"
    local details="${3:-}"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [[ "$status" == "PASS" ]]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        test_results+=("✅ $test_name")
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        test_results+=("❌ $test_name: $details")
    fi
}

# Python unit tests
run_unit_tests() {
    log_info "Running Python unit tests..."

    local pytest_args=(
        "tests/"
        "--tb=short"
        "-v"
    )

    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args+=(
            "--cov=app"
            "--cov-report=term-missing"
            "--cov-report=html:htmlcov"
        )
    fi

    if [[ "$VERBOSE" == "false" ]]; then
        pytest_args+=("-q")
    fi

    if pytest "${pytest_args[@]}" 2>/dev/null; then
        record_test "Python Unit Tests" "PASS"
    else
        record_test "Python Unit Tests" "FAIL" "Some tests failed"
    fi
}

# Integration tests
run_integration_tests() {
    log_info "Running integration tests..."

    # Test core scanner integration
    if python -c "
from app.core.scanner import SecurityScanner
scanner = SecurityScanner()
print('✅ Scanner initialization successful')
" 2>/dev/null; then
        record_test "Scanner Integration" "PASS"
    else
        record_test "Scanner Integration" "FAIL" "Scanner initialization failed"
    fi

    # Test GUI integration (if DISPLAY available)
    if [[ -n "${DISPLAY:-}" ]] || [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
        if python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
print('✅ GUI integration successful')
app.quit()
" 2>/dev/null; then
            record_test "GUI Integration" "PASS"
        else
            record_test "GUI Integration" "FAIL" "GUI initialization failed"
        fi
    else
        log_warning "Skipping GUI tests - no display available"
        record_test "GUI Integration" "SKIP" "No display available"
    fi
}

# Security tests
run_security_tests() {
    log_info "Running security tests..."

    # Bandit security scan
    if command -v bandit >/dev/null 2>&1; then
        if bandit -r app/ -f json -o bandit-report.json >/dev/null 2>&1; then
            record_test "Bandit Security Scan" "PASS"
        else
            record_test "Bandit Security Scan" "FAIL" "Security issues found"
        fi
    else
        record_test "Bandit Security Scan" "SKIP" "Bandit not available"
    fi

    # Semgrep security scan
    if command -v semgrep >/dev/null 2>&1; then
        if semgrep --config=auto app/ --json -o semgrep-report.json >/dev/null 2>&1; then
            record_test "Semgrep Security Scan" "PASS"
        else
            record_test "Semgrep Security Scan" "FAIL" "Security issues found"
        fi
    else
        record_test "Semgrep Security Scan" "SKIP" "Semgrep not available"
    fi

    # Dependency security check
    if command -v safety >/dev/null 2>&1; then
        if safety check --json >/dev/null 2>&1; then
            record_test "Dependency Security Check" "PASS"
        else
            record_test "Dependency Security Check" "FAIL" "Vulnerable dependencies found"
        fi
    else
        record_test "Dependency Security Check" "SKIP" "Safety not available"
    fi
}

# Code quality tests
run_quality_tests() {
    log_info "Running code quality tests..."

    # MyPy type checking
    if command -v mypy >/dev/null 2>&1; then
        if mypy app/ --ignore-missing-imports >/dev/null 2>&1; then
            record_test "MyPy Type Checking" "PASS"
        else
            record_test "MyPy Type Checking" "FAIL" "Type errors found"
        fi
    else
        record_test "MyPy Type Checking" "SKIP" "MyPy not available"
    fi

    # Black code formatting check
    if command -v black >/dev/null 2>&1; then
        if black --check app/ tests/ >/dev/null 2>&1; then
            record_test "Black Code Formatting" "PASS"
        else
            record_test "Black Code Formatting" "FAIL" "Code formatting issues"
        fi
    else
        record_test "Black Code Formatting" "SKIP" "Black not available"
    fi

    # Ruff linting
    if command -v ruff >/dev/null 2>&1; then
        if ruff check app/ tests/ >/dev/null 2>&1; then
            record_test "Ruff Linting" "PASS"
        else
            record_test "Ruff Linting" "FAIL" "Linting issues found"
        fi
    else
        record_test "Ruff Linting" "SKIP" "Ruff not available"
    fi
}

# GUI tests with pytest-qt
run_gui_tests() {
    log_info "Running GUI tests..."

    if [[ -n "${DISPLAY:-}" ]] || [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
        if pytest tests/test_gui.py -v --tb=short 2>/dev/null; then
            record_test "GUI Tests" "PASS"
        else
            record_test "GUI Tests" "FAIL" "GUI tests failed"
        fi
    else
        log_warning "Skipping GUI tests - no display available"
        record_test "GUI Tests" "SKIP" "No display available"
    fi
}

# Docker tests
run_docker_tests() {
    log_info "Running Docker tests..."

    if command -v docker >/dev/null 2>&1; then
        # Test Docker build
        if docker build -t xanados-test . >/dev/null 2>&1; then
            record_test "Docker Build" "PASS"

            # Clean up test image
            docker rmi xanados-test >/dev/null 2>&1 || true
        else
            record_test "Docker Build" "FAIL" "Docker build failed"
        fi

        # Test docker-compose
        if [[ -f "docker-compose.yml" ]]; then
            if docker-compose config >/dev/null 2>&1; then
                record_test "Docker Compose Config" "PASS"
            else
                record_test "Docker Compose Config" "FAIL" "docker-compose.yml invalid"
            fi
        fi
    else
        record_test "Docker Tests" "SKIP" "Docker not available"
    fi
}

# Node.js tests
run_node_tests() {
    log_info "Running Node.js tests..."

    if [[ -f "package.json" ]]; then
        # Test npm scripts
        if npm run lint >/dev/null 2>&1; then
            record_test "Node.js Linting" "PASS"
        else
            record_test "Node.js Linting" "FAIL" "Linting failed"
        fi

        if npm run validate >/dev/null 2>&1; then
            record_test "Node.js Validation" "PASS"
        else
            record_test "Node.js Validation" "FAIL" "Validation failed"
        fi
    else
        record_test "Node.js Tests" "SKIP" "No package.json found"
    fi
}

# Run tests based on type
case "$TEST_TYPE" in
    "all")
        run_unit_tests
        run_integration_tests
        run_security_tests
        run_quality_tests
        run_gui_tests
        run_docker_tests
        run_node_tests
        ;;
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "security")
        run_security_tests
        ;;
    "quality")
        run_quality_tests
        ;;
    "gui")
        run_gui_tests
        ;;
    "docker")
        run_docker_tests
        ;;
    "node")
        run_node_tests
        ;;
    *)
        log_error "Unknown test type: $TEST_TYPE"
        exit 1
        ;;
esac

# Generate test report
echo ""
echo "📊 Test Results Summary"
echo "======================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

# Display individual results
for result in "${test_results[@]}"; do
    echo "$result"
done

echo ""

# Generate coverage report link if coverage was enabled
if [[ "$COVERAGE" == "true" ]] && [[ -d "htmlcov" ]]; then
    log_info "Coverage report generated: file://$(pwd)/htmlcov/index.html"
fi

# Generate test artifacts summary
echo "📁 Test Artifacts Generated:"
[[ -f "bandit-report.json" ]] && echo "  • bandit-report.json"
[[ -f "semgrep-report.json" ]] && echo "  • semgrep-report.json"
[[ -d "htmlcov" ]] && echo "  • htmlcov/ (coverage report)"

# Exit with appropriate code
if [[ $FAILED_TESTS -eq 0 ]]; then
    log_success "All tests passed!"
    exit 0
else
    log_error "$FAILED_TESTS test(s) failed"
    exit 1
fi
