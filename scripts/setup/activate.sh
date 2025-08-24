#!/bin/bash
# Quick activation script for S&D development environment

# Get the script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "Activating S&D virtual environment..."
source .venv/bin/activate
echo "Virtual environment activated. Python path: $(which python)"
echo "  python app/main.py     - Run the application"
echo "  make run              - Run via Makefile"
echo "  make test             - Run tests"
echo "  deactivate            - Exit virtual environment"
