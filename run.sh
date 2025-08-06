#!/bin/bash
# Quick run script for S&D - Search & Destroy

# First check if we're in a venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "No virtual environment found. Please run 'make install' first."
        exit 1
    fi
fi

# Run the application
echo "Starting S&D - Search & Destroy..."
export PYTHONPATH="$PWD/app:$PYTHONPATH"
python app/main.py
