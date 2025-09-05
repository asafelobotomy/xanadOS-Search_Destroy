#!/bin/bash
# Security setup script for xanadOS Search & Destroy
# Installs polkit policies and configures secure operations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
POLICY_FILE="$PROJECT_ROOT/config/io.github.asafelobotomy.searchanddestroy.policy"
POLICY_DEST="/usr/share/polkit-1/actions/io.github.asafelobotomy.searchanddestroy.policy"

echo "=== xanadOS Search & Destroy Security Setup ==="
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "ERROR: This script should not be run as root"
    echo "Please run as a regular user - it will request elevated privileges when needed"
    exit 1
fi

# Check if polkit is available
if ! command -v pkcheck >/dev/null 2>&1; then
    echo "WARNING: polkit (pkcheck) not found"
    echo "Some security features may not work properly"
    echo "Consider installing polkit for enhanced security"
    echo
fi

# Function to install polkit policy
install_policy() {
    echo "Installing polkit policy..."

    if [[ ! -f "$POLICY_FILE" ]]; then
        echo "ERROR: Policy file not found: $POLICY_FILE"
        return 1
    fi

    # Check if policy directory exists
    if [[ ! -d "/usr/share/polkit-1/actions" ]]; then
        echo "ERROR: polkit actions directory not found"
        echo "Please install polkit and try again"
        return 1
    fi

    # Install policy file
    if sudo cp "$POLICY_FILE" "$POLICY_DEST"; then
        sudo chmod 644 "$POLICY_DEST"
        sudo chown root:root "$POLICY_DEST"
        echo "✓ Policy file installed successfully"
        return 0
    else
        echo "✗ Failed to install policy file"
        return 1
    fi
}

# Function to create secure directories
setup_directories() {
    echo "Setting up secure directories..."

    local dirs=(
        "$HOME/.local/share/xanados-search-destroy"
        "$HOME/.local/share/xanados-search-destroy/quarantine"
        "$HOME/.local/share/xanados-search-destroy/quarantine/files"
        "$HOME/.local/share/xanados-search-destroy/quarantine/metadata"
        "$HOME/.local/share/xanados-search-destroy/logs"
        "$HOME/.local/share/xanados-search-destroy/reports"
        "$HOME/.config/xanados-search-destroy"
    )

    for dir in "${dirs[@]}"; do
        if mkdir -p "$dir"; then
            chmod 700 "$dir"  # Secure permissions
            echo "✓ Created: $dir"
        else
            echo "✗ Failed to create: $dir"
            return 1
        fi
    done

    return 0
}

# Function to validate ClamAV installation
check_clamav() {
    echo "Checking ClamAV installation..."

    if command -v clamscan >/dev/null 2>&1; then
        echo "✓ clamscan found: $(which clamscan)"
    else
        echo "✗ clamscan not found"
        echo "Please install ClamAV:"
        echo "  Ubuntu/Debian: sudo apt install clamav clamav-daemon"
        echo "  Fedora/RHEL:   sudo dnf install clamav clamav-update"
        echo "  Arch:          sudo pacman -S clamav"
        return 1
    fi

    if command -v freshclam >/dev/null 2>&1; then
        echo "✓ freshclam found: $(which freshclam)"
    else
        echo "✗ freshclam not found"
        echo "ClamAV appears to be installed but freshclam is missing"
        return 1
    fi

    return 0
}

# Function to update virus database
update_database() {
    echo "Updating virus database (this may take a while)..."

    if sudo freshclam; then
        echo "✓ Virus database updated successfully"
        return 0
    else
        echo "✗ Failed to update virus database"
        echo "You may need to configure freshclam manually"
        return 1
    fi
}

# Function to test security features
test_security() {
    echo "Testing security features..."

    # Test basic imports
    if python3 -c "from app.core import PathValidator, PrivilegeEscalationManager, SecureNetworkManager; print('✓ Security modules imported successfully')" 2>/dev/null; then
        echo "✓ Security modules working correctly"
    else
        echo "✗ Security module import failed"
        echo "Please ensure you've activated the virtual environment:"
        echo "  source .venv/bin/activate"
        return 1
    fi

    return 0
}

# Main setup process
main() {
    echo "Starting security setup for xanadOS Search & Destroy..."
    echo "This will configure secure operations and install necessary policies."
    echo

    # Change to project directory
    cd "$PROJECT_ROOT"

    # Setup directories
    if ! setup_directories; then
        echo "Failed to setup directories"
        exit 1
    fi
    echo

    # Check ClamAV
    if ! check_clamav; then
        echo "ClamAV setup required - please install ClamAV and run this script again"
        exit 1
    fi
    echo

    # Install polkit policy
    echo "The following step requires administrator privileges to install the polkit policy."
    echo "This allows the application to request elevated privileges securely."
    if read -p "Install polkit policy? [y/N]: " -n 1 -r; then
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if install_policy; then
                echo "✓ Polkit policy installed"
            else
                echo "✗ Failed to install polkit policy"
                echo "Some features may not work properly"
            fi
        fi
    fi
    echo

    # Update virus database
    echo "The following step requires administrator privileges to update the virus database."
    if read -p "Update virus database? [y/N]: " -n 1 -r; then
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if update_database; then
                echo "✓ Virus database updated"
            else
                echo "✗ Failed to update virus database"
            fi
        fi
    fi
    echo

    # Test security features
    if test_security; then
        echo "✓ Security setup completed successfully"
    else
        echo "✗ Security setup completed with warnings"
        echo "Please check the error messages above"
    fi

    echo
    echo "=== Setup Complete ==="
    echo "The application is now configured with enhanced security features."
    echo "You can run the application normally, and it will request privileges"
    echo "when needed for system operations."
    echo
    echo "Note: If you encounter permission issues, ensure you are a member"
    echo "of the appropriate groups and that polkit is properly configured."
}

# Run main function
main "$@"
