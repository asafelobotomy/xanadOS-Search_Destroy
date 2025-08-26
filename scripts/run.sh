#!/bin/bash
# Wrapper script to launch S&D - Search & Destroy
# This script forwards execution to the main run script in scripts/

exec "$(dirname "$0")/scripts/run.sh" "$@"
