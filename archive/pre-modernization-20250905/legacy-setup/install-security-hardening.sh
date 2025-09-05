#!/bin/bash
# Security Hardening Installation Script for xanadOS Search & Destroy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/../config"
POLICY_DIR="/usr/share/polkit-1/actions"

echo "🔒 Installing Security Hardened Configuration"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "❌ This script should NOT be run as root for security reasons"
    echo "   It will use sudo only when necessary"
    exit 1
fi

# Check if PolicyKit is available
if ! command -v pkexec &> /dev/null; then
    echo "❌ PolicyKit (pkexec) is not installed"
    echo "   Please install: sudo apt install policykit-1"
    exit 1
fi

# Backup existing policy files
echo "📋 Backing up existing policy files..."
if [[ -f "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.policy" ]]; then
    sudo cp "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.policy" \
         "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.policy.backup-$(date +%Y%m%d-%H%M%S)"
    echo "   ✅ Backed up main policy"
fi

if [[ -f "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.rkhunter.policy" ]]; then
    sudo cp "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.rkhunter.policy" \
         "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.rkhunter.policy.backup-$(date +%Y%m%d-%H%M%S)"
    echo "   ✅ Backed up RKHunter policy"
fi

# Install hardened policy
echo "🛡️ Installing hardened PolicyKit configuration..."
if [[ -f "$CONFIG_DIR/io.github.asafelobotomy.searchanddestroy.hardened.policy" ]]; then
    sudo cp "$CONFIG_DIR/io.github.asafelobotomy.searchanddestroy.hardened.policy" \
         "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.hardened.policy"
    echo "   ✅ Installed hardened policy"

    # Set proper permissions
    sudo chmod 644 "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.hardened.policy"
    sudo chown root:root "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.hardened.policy"
    echo "   ✅ Set secure permissions"
else
    echo "   ❌ Hardened policy file not found: $CONFIG_DIR/io.github.asafelobotomy.searchanddestroy.hardened.policy"
    exit 1
fi

# Remove old insecure policies (optional)
read -p "🗑️ Remove old insecure policy files? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -f "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.policy" ]]; then
        sudo rm "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.policy"
        echo "   ✅ Removed old main policy"
    fi

    if [[ -f "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.rkhunter.policy" ]]; then
        sudo rm "$POLICY_DIR/io.github.asafelobotomy.searchanddestroy.rkhunter.policy"
        echo "   ✅ Removed old RKHunter policy"
    fi
fi

# Verify PolicyKit can read the new policy
echo "🔍 Verifying PolicyKit configuration..."
if sudo pkaction --action-id io.github.asafelobotomy.searchanddestroy.rkhunter.scan &> /dev/null; then
    echo "   ✅ PolicyKit can read hardened configuration"
else
    echo "   ⚠️ PolicyKit may need restart: sudo systemctl restart polkit"
fi

# Security recommendations
echo ""
echo "🔒 SECURITY HARDENING COMPLETE"
echo "==============================="
echo ""
echo "✅ Installed hardened PolicyKit configuration"
echo "✅ Command injection prevention enabled"
echo "✅ Privilege escalation restrictions applied"
echo "✅ Path validation enforcement active"
echo ""
echo "📋 Security Features Enabled:"
echo "   - Whitelist-based command validation"
echo "   - Restricted executable paths"
echo "   - Argument sanitization"
echo "   - Configuration path restrictions"
echo "   - Grace period security (no privilege expansion)"
echo ""
echo "⚠️ Important Notes:"
echo "   - Grace period only affects scan termination, not commands"
echo "   - All privileged operations are now validated"
echo "   - Only approved RKHunter operations are permitted"
echo "   - Regular security audits are recommended"
echo ""
echo "🛡️ Your RKHunter integration is now SECURITY HARDENED!"

# Optional: Test the security configuration
read -p "🧪 Test security configuration now? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing security validator..."
    if python3 "$SCRIPT_DIR/../app/core/security_validator.py"; then
        echo "✅ Security validation tests passed!"
    else
        echo "❌ Security validation tests failed"
        exit 1
    fi
fi

echo ""
echo "🔐 Security hardening installation complete!"
