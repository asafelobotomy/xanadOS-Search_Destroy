#!/bin/bash
# RKHunter execution wrapper with GUI environment support
# This script runs with root privileges via pkexec

# Set up GUI environment if available
export DISPLAY="${DISPLAY:-:0}"
if [ -n "$SUDO_USER" ] && [ -z "$XAUTHORITY" ]; then
    # Try to find the XAUTHORITY file for the original user
    export XAUTHORITY="/home/$SUDO_USER/.Xauthority"
fi

# Execute RKHunter with all passed arguments
exec /usr/bin/rkhunter "$@"
