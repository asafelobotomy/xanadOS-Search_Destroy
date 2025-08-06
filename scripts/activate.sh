#!/bin/bash
# Quick activation script for S&D development environment
echo "Activating S&D virtual environment..."
#!/bin/bash
# Activate the Python virtual environment

source .venv/bin/activate
echo "Virtual environment activated. Python path: $(which python)"
echo "  python app/main.py     - Run the application"
echo "  make run              - Run via Makefile"
echo "  make test             - Run tests"
echo "  deactivate            - Exit virtual environment"
