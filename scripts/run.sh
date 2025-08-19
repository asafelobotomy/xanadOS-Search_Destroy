#!/bin/bash
# Quick run script for S&D - Search & Destroy

# Get the script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# First check if we're in a venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "No virtual environment found. Please run 'make install' first."
        exit 1
    fi
fi

# Run the application
echo "Starting S&D - Search & Destroy..."
export PYTHONPATH="$PROJECT_ROOT/app:$PYTHONPATH"
python app/main.py
