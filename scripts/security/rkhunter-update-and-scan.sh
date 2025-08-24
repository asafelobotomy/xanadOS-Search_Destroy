#!/bin/bash
# RKHunter combined update and scan wrapper
# This script runs both operations with a single authentication

# Set up GUI environment if available
export DISPLAY="${DISPLAY:-:0}"
if [ -n "$SUDO_USER" ] && [ -z "$XAUTHORITY" ]; then
    # Try to find the XAUTHORITY file for the original user
    export XAUTHORITY="/home/$SUDO_USER/.Xauthority"
fi

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_message "Starting RKHunter update and scan sequence"

# Step 1: Update database
log_message "Updating RKHunter database..."
/usr/bin/rkhunter --update --quiet

update_result=$?
if [ $update_result -eq 0 ]; then
    log_message "Database update completed successfully"
else
    log_message "Database update failed with exit code $update_result (continuing anyway)"
fi

# Step 2: Run the scan with all passed arguments
log_message "Starting RKHunter scan..."
exec /usr/bin/rkhunter "$@"
