#!/usr/bin/env bash
# RKHunter execution wrapper with GUI environment support
# This script runs with root privileges via pkexec

set -euo pipefail

# Input validation function
validate_rkhunter_args() {
    local args=("$@")

    # Check for dangerous arguments
    for arg in "${args[@]}"; do
        # Prevent command injection attempts
        if [[ "$arg" =~ [;\|\&\$\`] ]]; then
            echo "Error: Invalid characters in argument: $arg" >&2
            exit 1
        fi

        # Only allow known safe rkhunter options
        if [[ "$arg" =~ ^- ]] && ! [[ "$arg" =~ ^--(check|update|propupd|version|help|config-check)$ ]]; then
            if ! [[ "$arg" =~ ^-[cuvh]$ ]]; then
                echo "Warning: Potentially unsafe argument: $arg" >&2
            fi
        fi
    done
}

# Validate rkhunter exists and is executable
if [[ ! -x "/usr/bin/rkhunter" ]]; then
    echo "Error: rkhunter not found or not executable at /usr/bin/rkhunter" >&2
    exit 1
fi

# Set up GUI environment if available
export DISPLAY="${DISPLAY:-:0}"

# Safely handle SUDO_USER environment variable
if [[ -n "${SUDO_USER:-}" ]] && [[ -z "${XAUTHORITY:-}" ]]; then
    # Validate SUDO_USER is a real username (basic validation)
    if id "$SUDO_USER" &>/dev/null; then
        # Try to find the XAUTHORITY file for the original user
        XAUTH_PATH="/home/$SUDO_USER/.Xauthority"
        if [[ -f "$XAUTH_PATH" ]]; then
            export XAUTHORITY="$XAUTH_PATH"
        fi
    fi
fi

# Validate arguments before execution
validate_rkhunter_args "$@"

# Execute RKHunter with validated arguments
exec /usr/bin/rkhunter "$@"
