#!/bin/bash
# SSH Security Hardening Script
# Addresses RKHunter scan warnings for SSH configuration
# Date: September 5, 2025

set -euo pipefail

echo "🔒 SSH Security Hardening Script"
echo "================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo "✅ Running with root privileges"
else
    echo "❌ This script requires root privileges"
    echo "Please run with: sudo $0"
    exit 1
fi

# Backup original SSH configuration
SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP_FILE="${SSHD_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "📁 Creating backup of SSH configuration..."
cp "$SSHD_CONFIG" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Check current SSH configuration
echo ""
echo "📋 Current SSH Configuration Analysis:"
echo "======================================"

# Check PermitRootLogin setting
if grep -q "^PermitRootLogin" "$SSHD_CONFIG"; then
    CURRENT_ROOT_LOGIN=$(grep "^PermitRootLogin" "$SSHD_CONFIG" | awk '{print $2}')
    echo "PermitRootLogin: $CURRENT_ROOT_LOGIN"
else
    echo "PermitRootLogin: NOT SET (potentially vulnerable)"
    NEEDS_ROOT_FIX=true
fi

# Check Protocol setting
if grep -q "^Protocol" "$SSHD_CONFIG"; then
    CURRENT_PROTOCOL=$(grep "^Protocol" "$SSHD_CONFIG" | awk '{print $2}')
    echo "Protocol: $CURRENT_PROTOCOL"
else
    echo "Protocol: NOT SET (potentially vulnerable)"
    NEEDS_PROTOCOL_FIX=true
fi

echo ""
echo "🔧 Applying Security Fixes:"
echo "=========================="

# Fix PermitRootLogin if needed
if [[ "${NEEDS_ROOT_FIX:-false}" == "true" ]]; then
    echo "🔒 Setting PermitRootLogin to 'no'..."
    echo "PermitRootLogin no" >> "$SSHD_CONFIG"
    echo "✅ PermitRootLogin disabled"
else
    echo "ℹ️  PermitRootLogin already configured"
fi

# Fix Protocol if needed
if [[ "${NEEDS_PROTOCOL_FIX:-false}" == "true" ]]; then
    echo "🔒 Setting Protocol to '2' (SSH v2 only)..."
    echo "Protocol 2" >> "$SSHD_CONFIG"
    echo "✅ SSH Protocol v2 enforced"
else
    echo "ℹ️  SSH Protocol already configured"
fi

# Additional security hardening
echo ""
echo "🛡️  Applying Additional Security Hardening:"
echo "==========================================="

# Check and add additional security settings
SECURITY_SETTINGS=(
    "MaxAuthTries 3"
    "LoginGraceTime 60"
    "X11Forwarding no"
    "AllowTcpForwarding no"
    "ClientAliveInterval 300"
    "ClientAliveCountMax 2"
)

for setting in "${SECURITY_SETTINGS[@]}"; do
    SETTING_NAME=$(echo "$setting" | awk '{print $1}')
    if ! grep -q "^$SETTING_NAME" "$SSHD_CONFIG"; then
        echo "$setting" >> "$SSHD_CONFIG"
        echo "✅ Added: $setting"
    else
        echo "ℹ️  $SETTING_NAME already configured"
    fi
done

# Test SSH configuration
echo ""
echo "🧪 Testing SSH Configuration:"
echo "============================="

if sshd -t; then
    echo "✅ SSH configuration is valid"
else
    echo "❌ SSH configuration has errors!"
    echo "🔄 Restoring backup..."
    cp "$BACKUP_FILE" "$SSHD_CONFIG"
    echo "❌ Configuration restored from backup"
    exit 1
fi

# Restart SSH service
echo ""
echo "🔄 Restarting SSH Service:"
echo "========================="

if systemctl restart sshd; then
    echo "✅ SSH service restarted successfully"
else
    echo "❌ Failed to restart SSH service"
    echo "🔄 Restoring backup..."
    cp "$BACKUP_FILE" "$SSHD_CONFIG"
    systemctl restart sshd
    echo "❌ Configuration restored and SSH restarted"
    exit 1
fi

# Verify SSH is running
if systemctl is-active --quiet sshd; then
    echo "✅ SSH service is active and running"
else
    echo "❌ SSH service is not running properly"
    exit 1
fi

echo ""
echo "🎉 SSH Security Hardening Complete!"
echo "==================================="
echo "📋 Summary of changes:"
echo "• PermitRootLogin disabled"
echo "• SSH Protocol v2 enforced"
echo "• Maximum authentication attempts limited to 3"
echo "• Login grace time set to 60 seconds"
echo "• X11 forwarding disabled"
echo "• TCP forwarding disabled"
echo "• Client alive settings configured"
echo ""
echo "🔐 Your SSH service is now more secure!"
echo "📁 Backup saved as: $BACKUP_FILE"
