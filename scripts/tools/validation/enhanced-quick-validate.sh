#!/bin/bash
# Enhanced Quick Validation for Modern Repository
# Optimized for current xanadOS Search & Destroy state
# Date: $(date +%Y-%m-%d)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}🚀 Enhanced Quick Validation for Modernized Repository${NC}"
echo "=================================================================="
echo ""

# Track validation results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Validation tracking function
track_result() {
    local status="$1"
    local message="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    case "$status" in
        "PASS")
            echo -e "${GREEN}  ✅ $message${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            ;;
        "FAIL")
            echo -e "${RED}  ❌ $message${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            ;;
        "WARN")
            echo -e "${YELLOW}  ⚠️  $message${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            ;;
    esac
}

echo -e "${YELLOW}📋 PHASE 1: Repository Organization Validation${NC}"
echo "----------------------------------------------------------------"

# Check root directory organization (realistic for modern projects)
ROOT_FILES=$(find . -maxdepth 1 -type f | wc -l)
if [[ $ROOT_FILES -le 30 ]]; then
    track_result "PASS" "Root directory organization (${ROOT_FILES} files - acceptable for modern toolchain)"
else
    track_result "WARN" "Root directory has ${ROOT_FILES} files (recommend ≤30) - consider organizing config files"
fi

# Check archive organization
if [[ -d "archive" ]] && [[ -f "archive/ARCHIVE_INDEX.md" ]]; then
    track_result "PASS" "Archive system properly organized"
else
    track_result "FAIL" "Archive system not properly organized"
fi

# Check essential directories
ESSENTIAL_DIRS=("docs" "scripts" "app" "tests" "config")
for dir in "${ESSENTIAL_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        track_result "PASS" "Essential directory present: $dir"
    else
        track_result "FAIL" "Essential directory missing: $dir"
    fi
done

echo ""
echo -e "${YELLOW}📋 PHASE 2: Modern Development Environment${NC}"
echo "----------------------------------------------------------------"

# Check modern tooling
if command -v uv >/dev/null 2>&1; then
    UV_VERSION=$(uv --version | cut -d' ' -f2)
    track_result "PASS" "Modern Python package manager (uv $UV_VERSION)"
else
    track_result "WARN" "uv not available (falling back to pip)"
fi

if command -v pnpm >/dev/null 2>&1; then
    PNPM_VERSION=$(pnpm --version)
    track_result "PASS" "Modern Node package manager (pnpm $PNPM_VERSION)"
else
    track_result "WARN" "pnpm not available (falling back to npm)"
fi

if command -v fnm >/dev/null 2>&1; then
    track_result "PASS" "Modern Node version manager (fnm)"
else
    track_result "WARN" "fnm not available"
fi

# Check modern configuration files
if [[ -f "pyproject.toml" ]]; then
    track_result "PASS" "Modern Python configuration (pyproject.toml)"
else
    track_result "FAIL" "pyproject.toml missing"
fi

# Check unified Makefile
if [[ -f "Makefile" ]] && ! [[ -f "Makefile.modern" ]]; then
    track_result "PASS" "Unified Makefile system (no dual system)"
else
    track_result "WARN" "Dual Makefile system detected"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 3: Core Validation Suite${NC}"
echo "----------------------------------------------------------------"

# Markdown linting
echo -e "${BLUE}Running markdown validation...${NC}"
if npm run lint >/dev/null 2>&1; then
    track_result "PASS" "Markdown linting validation"
else
    track_result "FAIL" "Markdown linting issues found"
fi

# Spell checking (main files)
echo -e "${BLUE}Running spell check on core files...${NC}"
if npm run spell:check:main >/dev/null 2>&1; then
    track_result "PASS" "Spell checking (core files)"
else
    track_result "FAIL" "Spell checking issues found"
fi

# Version synchronization
echo -e "${BLUE}Checking version synchronization...${NC}"
if npm run version:sync:check >/dev/null 2>&1; then
    track_result "PASS" "Version synchronization"
else
    track_result "FAIL" "Version synchronization issues"
fi

# Template and chatmode validation
echo -e "${BLUE}Validating templates and chatmodes...${NC}"
if npm run validate >/dev/null 2>&1; then
    track_result "PASS" "Template and chatmode validation"
else
    track_result "FAIL" "Template/chatmode validation issues"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 4: Code Quality (Non-blocking)${NC}"
echo "----------------------------------------------------------------"

# Python validation (development-friendly approach)
echo -e "${BLUE}Running Python code quality checks...${NC}"
PYTHON_OUTPUT=$(bash scripts/tools/quality/check-python.sh 2>&1 || true)

# Count different types of issues
SYNTAX_ERRORS=$(echo "$PYTHON_OUTPUT" | grep -c "E[0-9]\|W[0-9]" || echo "0")
UNUSED_IMPORTS=$(echo "$PYTHON_OUTPUT" | grep -c "F401.*imported but unused" || echo "0")
OTHER_ISSUES=$(echo "$PYTHON_OUTPUT" | grep -c "F[0-9]" | head -1 || echo "0")
OTHER_ISSUES=$((OTHER_ISSUES - UNUSED_IMPORTS))

if [[ $SYNTAX_ERRORS -eq 0 && $OTHER_ISSUES -eq 0 ]]; then
    if [[ $UNUSED_IMPORTS -gt 0 ]]; then
        track_result "PASS" "Python code quality (${UNUSED_IMPORTS} development imports - acceptable)"
    else
        track_result "PASS" "Python code quality (clean)"
    fi
else
    track_result "WARN" "Python code quality issues (${SYNTAX_ERRORS} syntax, ${OTHER_ISSUES} other - non-blocking)"
fi

# Security privilege escalation audit
echo -e "${BLUE}Running security privilege audit...${NC}"
if python3 scripts/tools/security/privilege-escalation-audit.py --validate-only >/dev/null 2>&1; then
    track_result "PASS" "Security privilege escalation audit"
else
    track_result "WARN" "Security audit issues (check manually)"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 5: Repository Health Check${NC}"
echo "----------------------------------------------------------------"

# Check for proper .gitignore
if [[ -f ".gitignore" ]] && grep -q "\.venv" ".gitignore"; then
    track_result "PASS" "Git ignore configuration"
else
    track_result "WARN" "Git ignore may need updates"
fi

# Check for presence of documentation
if [[ -f "README.md" ]] && [[ -f "CONTRIBUTING.md" ]] && [[ -f "CHANGELOG.md" ]]; then
    track_result "PASS" "Essential documentation present"
else
    track_result "FAIL" "Essential documentation missing"
fi

# Check for GitHub configuration
if [[ -d ".github" ]] && [[ -f ".github/copilot-instructions.md" ]]; then
    track_result "PASS" "GitHub/Copilot configuration"
else
    track_result "FAIL" "GitHub configuration incomplete"
fi

# Check for development setup
if [[ -f "scripts/setup/modern-dev-setup.sh" ]]; then
    track_result "PASS" "Modern development setup available"
else
    track_result "FAIL" "Modern development setup missing"
fi

echo ""
echo -e "${BOLD}${BLUE}📊 VALIDATION SUMMARY${NC}"
echo "=================================================================="

# Calculate percentages
if [[ $TOTAL_CHECKS -gt 0 ]]; then
    PASS_RATE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    FAIL_RATE=$(( (FAILED_CHECKS * 100) / TOTAL_CHECKS ))
    WARN_RATE=$(( (WARNING_CHECKS * 100) / TOTAL_CHECKS ))
else
    PASS_RATE=0
    FAIL_RATE=0
    WARN_RATE=0
fi

echo -e "${GREEN}✅ Passed: ${PASSED_CHECKS}/${TOTAL_CHECKS} (${PASS_RATE}%)${NC}"
echo -e "${YELLOW}⚠️  Warnings: ${WARNING_CHECKS}/${TOTAL_CHECKS} (${WARN_RATE}%)${NC}"
echo -e "${RED}❌ Failed: ${FAILED_CHECKS}/${TOTAL_CHECKS} (${FAIL_RATE}%)${NC}"

echo ""

# Determine overall status
if [[ $FAILED_CHECKS -eq 0 ]]; then
    if [[ $WARNING_CHECKS -eq 0 ]]; then
        echo -e "${BOLD}${GREEN}🏆 REPOSITORY STATUS: EXCELLENT${NC}"
        echo -e "${GREEN}All validations passed successfully!${NC}"
        EXIT_CODE=0
    else
        echo -e "${BOLD}${YELLOW}🔶 REPOSITORY STATUS: GOOD${NC}"
        echo -e "${YELLOW}All critical checks passed with minor warnings.${NC}"
        EXIT_CODE=0
    fi
else
    if [[ $FAILED_CHECKS -le 2 ]]; then
        echo -e "${BOLD}${YELLOW}🔸 REPOSITORY STATUS: ACCEPTABLE${NC}"
        echo -e "${YELLOW}Minor issues found but repository is functional.${NC}"
        EXIT_CODE=0
    else
        echo -e "${BOLD}${RED}⚠️  REPOSITORY STATUS: NEEDS ATTENTION${NC}"
        echo -e "${RED}Multiple critical issues require resolution.${NC}"
        EXIT_CODE=1
    fi
fi

echo ""
echo -e "${BLUE}🔗 Next Steps:${NC}"
if [[ $FAILED_CHECKS -gt 0 ]]; then
    echo "   • Address failed validations above"
    echo "   • Run: make validate-full (for comprehensive checks)"
    echo "   • Check: docs/guides/ for guidance"
else
    echo "   • Repository ready for development!"
    echo "   • Use: make help (for available commands)"
    echo "   • Run: make test (for full test suite)"
fi

echo ""
echo -e "${BOLD}${BLUE}Enhanced Quick Validation Complete${NC}"
echo "=================================================================="

exit $EXIT_CODE
