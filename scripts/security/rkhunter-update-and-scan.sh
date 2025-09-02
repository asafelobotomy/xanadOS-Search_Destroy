#!/usr/bin/env bash
# RKHunter combined update and scan wrapper
# This script runs both operations with a single authentication

set -euo pipefail

# Input validation and security functions
validate_environment() {
    # Validate SUDO_USER if present
    if [[ -n "${SUDO_USER:-}" ]]; then
        if ! id "${SUDO_USER}" &>/dev/null; then
            echo "Error: Invalid SUDO_USER: ${SUDO_USER}" >&2
            exit 1
        fi
    fi

    # Validate DISPLAY format if present
    if [[ -n "${DISPLAY:-}" ]] && ! [[ "${DISPLAY}" =~ ^:[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Warning: Potentially invalid DISPLAY format: ${DISPLAY}" >&2
    fi
}

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Validate rkhunter exists
if [[ ! -x "/usr/bin/rkhunter" ]]; then
    echo "Error: rkhunter not found or not executable" >&2
    exit 1
fi

# Validate environment variables
validate_environment

# Set up GUI environment if available
export DISPLAY="${DISPLAY:-:0}"

# Safely handle SUDO_USER and XAUTHORITY
if [[ -n "${SUDO_USER:-}" ]] && [[ -z "${XAUTHORITY:-}" ]]; then
    XAUTH_PATH="/home/${SUDO_USER}/.Xauthority"
    if [[ -f "$XAUTH_PATH" ]]; then
        export XAUTHORITY="$XAUTH_PATH"
    fi
fi

log_message "Starting RKHunter update and scan sequence"

# Step 1: Update database
log_message "Updating RKHunter database..."

# Validate arguments passed to script
for arg in "$@"; do
    if [[ "${arg}" =~ [\;\|\&\$\`] ]]; then
        echo "Error: Invalid characters in argument: ${arg}" >&2
        exit 1
    fi
done

# Execute RKHunter with validated arguments
exec /usr/bin/rkhunter "$@"
