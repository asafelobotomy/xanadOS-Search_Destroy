#!/bin/bash
# Security Environment Verification Script
# xanadOS Search & Destroy - Post-Setup Validation
#
# This script verifies that the security environment is properly configured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 Security Environment Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

check_pass() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_fail() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️${NC}  $1"
    ((WARNING_CHECKS++))
    ((TOTAL_CHECKS++))
}

# ============================================================================
# Environment Variables
# ============================================================================

echo -e "${BLUE}▶ Checking Environment Variables${NC}"
echo ""

if [ -n "$MALWAREBAZAAR_API_KEY" ]; then
    check_pass "MALWAREBAZAAR_API_KEY is set (length: ${#MALWAREBAZAAR_API_KEY})"
else
    check_warn "MALWAREBAZAAR_API_KEY not set in current session"
fi

# Check shell config
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

if [ -n "$SHELL_CONFIG" ] && grep -q "MALWAREBAZAAR_API_KEY" "$SHELL_CONFIG" 2>/dev/null; then
    check_pass "API key configured in $SHELL_CONFIG"
else
    check_warn "API key not found in shell config"
fi

echo ""

# ============================================================================
# Directory Structure
# ============================================================================

echo -e "${BLUE}▶ Checking Directory Structure${NC}"
echo ""

REQUIRED_DIRS=(
    "$HOME/.config/search-and-destroy"
    "$HOME/.local/share/search-and-destroy"
    "$HOME/.local/share/search-and-destroy/security-logs"
    "$HOME/.cache/search-and-destroy"
    "$PROJECT_ROOT/models"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Directory exists: $dir"
    else
        check_fail "Directory missing: $dir"
    fi
done

echo ""

# ============================================================================
# Permissions
# ============================================================================

echo -e "${BLUE}▶ Checking Permissions${NC}"
echo ""

check_perms() {
    local path=$1
    local expected=$2

    if [ -e "$path" ]; then
        actual=$(stat -c %a "$path" 2>/dev/null || stat -f %A "$path" 2>/dev/null)
        if [ "$actual" = "$expected" ]; then
            check_pass "Permissions correct: $path ($expected)"
        else
            check_warn "Permissions mismatch: $path (expected $expected, got $actual)"
        fi
    fi
}

check_perms "$HOME/.config/search-and-destroy" "700"
check_perms "$HOME/.local/share/search-and-destroy/security-logs" "700"

if [ -f "models/trusted_hashes.json" ]; then
    check_perms "models/trusted_hashes.json" "600"
fi

echo ""

# ============================================================================
# Python Dependencies
# ============================================================================

echo -e "${BLUE}▶ Checking Python Dependencies${NC}"
echo ""

# Check for uv or pip
if command -v uv &> /dev/null; then
    check_pass "Package manager: uv"
elif command -v pip &> /dev/null; then
    check_warn "Package manager: pip (consider using uv)"
else
    check_fail "No package manager found (uv or pip)"
fi

# Check pinned versions
echo ""
echo -e "${BLUE}▶ Verifying Pinned Library Versions${NC}"
echo ""

check_version() {
    local package=$1
    local expected=$2

    if command -v uv &> /dev/null; then
        actual=$(uv pip list 2>/dev/null | grep "^$package " | awk '{print $2}')
    else
        actual=$(pip list 2>/dev/null | grep "^$package " | awk '{print $2}')
    fi

    if [ -n "$actual" ]; then
        if [ "$actual" = "$expected" ]; then
            check_pass "$package: $actual (pinned)"
        else
            check_warn "$package: $actual (expected $expected)"
        fi
    else
        check_fail "$package: not installed"
    fi
}

check_version "pefile" "2024.8.26"
check_version "pyelftools" "0.31"
check_version "lief" "0.15.1"

echo ""

# ============================================================================
# Security Modules
# ============================================================================

echo -e "${BLUE}▶ Testing Security Modules${NC}"
echo ""

python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

test_results = []

# Test SecureRandom
try:
    from app.utils.secure_random import SecureRandom
    token = SecureRandom.token_hex(32)
    test_results.append(("SecureRandom", True, f"Generated {len(token)} char token"))
except Exception as e:
    test_results.append(("SecureRandom", False, str(e)))

# Test ErrorSanitizer
try:
    from app.utils.error_sanitizer import sanitize_error
    result = sanitize_error("Test /home/user/file.txt and 192.168.1.1")
    has_redaction = "[REDACTED]" in result or "[IP_REDACTED]" in result
    test_results.append(("ErrorSanitizer", has_redaction, "Redaction working"))
except Exception as e:
    test_results.append(("ErrorSanitizer", False, str(e)))

# Test SecurityAuditLogger
try:
    from app.core.security_audit_logger import get_audit_logger
    logger = get_audit_logger()
    test_results.append(("SecurityAuditLogger", True, "Initialized"))
except Exception as e:
    test_results.append(("SecurityAuditLogger", False, str(e)))

# Test ModelSignatureVerifier
try:
    from app.ml.model_signature_verification import ModelSignatureVerifier
    verifier = ModelSignatureVerifier()
    test_results.append(("ModelSignatureVerifier", True, "Initialized"))
except Exception as e:
    test_results.append(("ModelSignatureVerifier", False, str(e)))

# Output results
for name, success, message in test_results:
    status = "PASS" if success else "FAIL"
    print(f"{status}|{name}|{message}")

sys.exit(0 if all(r[1] for r in test_results) else 1)
EOF

# Parse Python output
while IFS='|' read -r status name message; do
    if [ "$status" = "PASS" ]; then
        check_pass "$name: $message"
    else
        check_fail "$name: $message"
    fi
done < <(python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

test_results = []
try:
    from app.utils.secure_random import SecureRandom
    token = SecureRandom.token_hex(32)
    test_results.append(('SecureRandom', True, f'Generated {len(token)} char token'))
except Exception as e:
    test_results.append(('SecureRandom', False, str(e)))

try:
    from app.utils.error_sanitizer import sanitize_error
    result = sanitize_error('Test /home/user/file.txt and 192.168.1.1')
    has_redaction = '[REDACTED]' in result or '[IP_REDACTED]' in result
    test_results.append(('ErrorSanitizer', has_redaction, 'Redaction working'))
except Exception as e:
    test_results.append(('ErrorSanitizer', False, str(e)))

try:
    from app.core.security_audit_logger import get_audit_logger
    logger = get_audit_logger()
    test_results.append(('SecurityAuditLogger', True, 'Initialized'))
except Exception as e:
    test_results.append(('SecurityAuditLogger', False, str(e)))

try:
    from app.ml.model_signature_verification import ModelSignatureVerifier
    verifier = ModelSignatureVerifier()
    test_results.append(('ModelSignatureVerifier', True, 'Initialized'))
except Exception as e:
    test_results.append(('ModelSignatureVerifier', False, str(e)))

for name, success, message in test_results:
    status = 'PASS' if success else 'FAIL'
    print(f'{status}|{name}|{message}')
")

echo ""

# ============================================================================
# Files & Configuration
# ============================================================================

echo -e "${BLUE}▶ Checking Configuration Files${NC}"
echo ""

if [ -f "models/trusted_hashes.json" ]; then
    check_pass "Trusted hash registry exists"

    # Validate JSON
    if python3 -m json.tool models/trusted_hashes.json >/dev/null 2>&1; then
        check_pass "Trusted hash registry is valid JSON"
    else
        check_fail "Trusted hash registry has invalid JSON"
    fi
else
    check_warn "Trusted hash registry not yet created"
fi

if [ -f ".env.status" ]; then
    check_pass "Environment status file exists"
else
    check_warn "Environment status file not found"
fi

# Check .gitignore
required_entries=(".env" "data/malware/" "models/production/*.pkl")
for entry in "${required_entries[@]}"; do
    if grep -qF "$entry" .gitignore 2>/dev/null; then
        check_pass ".gitignore contains: $entry"
    else
        check_warn ".gitignore missing: $entry"
    fi
done

echo ""

# ============================================================================
# GitHub Configuration
# ============================================================================

echo -e "${BLUE}▶ Checking GitHub Configuration${NC}"
echo ""

if [ -f ".github/workflows/security-scan.yml" ]; then
    check_pass "Security scan workflow exists"
else
    check_fail "Security scan workflow missing"
fi

if [ -f ".github/workflows/train-models.yml" ]; then
    check_pass "Model training workflow exists"
else
    check_warn "Model training workflow not found"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Verification Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✨ All checks passed! Environment is fully configured.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Environment is functional but has $WARNING_CHECKS warning(s).${NC}"
        exit 0
    fi
else
    echo -e "${RED}❌ $FAILED_CHECKS check(s) failed. Please review and fix issues.${NC}"
    exit 1
fi
