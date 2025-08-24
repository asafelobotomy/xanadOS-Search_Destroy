#!/bin/bash
# Agent Workflow Validation Script
# Demonstrates the mandatory quality-first approach for all GitHub Copilot agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_failure() {
    echo -e "${RED}[✗]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Header
echo "======================================"
echo "Agent Workflow Validation System"
echo "Quality-First Approach Verification"
echo "======================================"
echo ""

print_status "Validating systematic workflow compliance..."
echo ""

# Phase 1: Instruction Discovery Validation
print_status "Phase 1: Instruction Discovery Validation"
echo ""

# Check if all instruction files exist
if [ -f ".github/instructions/agent-workflow.instructions.md" ]; then
    print_success "Agent workflow instructions found"
else
    print_failure "Missing agent workflow instructions"
fi

if [ -f ".github/instructions/file-organization.instructions.md" ]; then
    print_success "File organization policy found"
else
    print_failure "Missing file organization policy"
fi

if [ -f ".github/instructions/toolshed-usage.instructions.md" ]; then
    print_success "Toolshed usage instructions found"
else
    print_failure "Missing toolshed usage instructions"
fi

if [ -f ".github/instructions/documentation-awareness.instructions.md" ]; then
    print_success "Documentation awareness instructions found"
else
    print_failure "Missing documentation awareness instructions"
fi

echo ""

# Phase 2: File Organization Compliance
print_status "Phase 2: File Organization Compliance"
echo ""

# Check for root directory clutter (should only have essential files)
ROOT_FILES=($(ls -1 | grep -v "^[.]" | grep -v "^docs$" | grep -v "^scripts$" | grep -v "^archive$" | grep -v "^examples$" | wc -l))

if [ "$ROOT_FILES" -le 10 ]; then
    print_success "Root directory properly organized (${ROOT_FILES} files)"
else
    print_failure "Root directory cluttered (${ROOT_FILES} files - should be ≤10)"
fi

# Check for misplaced documentation files
MISPLACED_DOCS=$(find . -maxdepth 1 -name "*REFERENCE*.md" -o -name "*GUIDE*.md" -o -name "*MANUAL*.md" | wc -l)
if [ "$MISPLACED_DOCS" -eq 0 ]; then
    print_success "No misplaced documentation in root directory"
else
    print_failure "Found ${MISPLACED_DOCS} misplaced documentation files in root"
fi

# Check for misplaced scripts
MISPLACED_SCRIPTS=$(find . -maxdepth 1 -name "*.sh" -o -name "*.js" -o -name "*.py" | wc -l)
if [ "$MISPLACED_SCRIPTS" -eq 0 ]; then
    print_success "No misplaced scripts in root directory"
else
    print_failure "Found ${MISPLACED_SCRIPTS} misplaced script files in root"
fi

echo ""

# Phase 3: Toolshed Awareness Validation
print_status "Phase 3: Toolshed Awareness Validation"
echo ""

if [ -d "scripts/tools" ]; then
    TOOL_COUNT=$(find scripts/tools/ -name "*.sh" | wc -l)
    print_success "Toolshed available with ${TOOL_COUNT} tools"

    # Check for duplicate functionality
    if [ -f "scripts/tools/README.md" ]; then
        print_success "Toolshed documentation found"
    else
        print_failure "Missing toolshed documentation"
    fi
else
    print_failure "Toolshed directory missing"
fi

echo ""

# Phase 4: Documentation Repository Validation
print_status "Phase 4: Documentation Repository Validation"
echo ""

if [ -d "docs" ]; then
    DOC_COUNT=$(find docs/ -name "*.md" | wc -l)
    print_success "Documentation repository available with ${DOC_COUNT} documents"

    if [ -f "docs/README.md" ]; then
        print_success "Documentation index found"
    else
        print_failure "Missing documentation index"
    fi

    if [ -d "docs/guides" ]; then
        GUIDE_COUNT=$(find docs/guides/ -name "*.md" | wc -l)
        print_success "User guides directory found with ${GUIDE_COUNT} guides"
    else
        print_failure "Missing user guides directory"
    fi
else
    print_failure "Documentation repository missing"
fi

echo ""

# Phase 5: Quality Gates Validation
print_status "Phase 5: Quality Gates Validation"
echo ""

# Check for version control standards
if [ -f ".gitignore" ]; then
    print_success "Git ignore file found"
else
    print_failure "Missing .gitignore file"
fi

if [ -f "CHANGELOG.md" ]; then
    print_success "Changelog maintained"
else
    print_failure "Missing changelog"
fi

if [ -f "VERSION" ]; then
    print_success "Version file maintained"
else
    print_failure "Missing version file"
fi

# Check GitHub workflows
if [ -d ".github/workflows" ]; then
    WORKFLOW_COUNT=$(find .github/workflows/ -name "*.yml" -o -name "*.yaml" | wc -l)
    if [ "$WORKFLOW_COUNT" -gt 0 ]; then
        print_success "GitHub workflows configured (${WORKFLOW_COUNT} workflows)"
    else
        print_failure "No GitHub workflows found"
    fi
else
    print_failure "Missing GitHub workflows directory"
fi

echo ""

# Generate Final Report
echo "======================================"
echo "Agent Workflow Validation Report"
echo "======================================"
echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

PASS_PERCENTAGE=$((CHECKS_PASSED * 100 / TOTAL_CHECKS))
echo "Pass Rate: $PASS_PERCENTAGE%"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ ALL WORKFLOW STANDARDS MET!${NC}"
    echo -e "${GREEN}Repository demonstrates proper quality-first approach${NC}"
    echo ""
    echo "🎯 Quality-First Validation Successful:"
    echo "  • Systematic workflow instructions in place"
    echo "  • File organization policy enforced"
    echo "  • Toolshed awareness implemented"
    echo "  • Documentation repository organized"
    echo "  • Quality gates operational"
    exit 0
else
    echo ""
    echo -e "${RED}✗ WORKFLOW IMPROVEMENTS NEEDED${NC}"
    echo -e "${YELLOW}Agents must follow systematic quality-first approach${NC}"
    echo ""
    echo "🔧 Required Actions:"
    if [ $CHECKS_FAILED -gt 0 ]; then
        echo "  • Address ${CHECKS_FAILED} failed validation checks"
        echo "  • Review agent workflow instructions"
        echo "  • Implement missing quality gates"
        echo "  • Organize files according to policy"
    fi
    exit 1
fi
