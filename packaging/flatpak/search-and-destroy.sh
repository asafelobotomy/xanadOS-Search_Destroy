#!/bin/bash
# Launcher script for S&D - Search & Destroy Flatpak

export PYTHONPATH="/app/lib/search-and-destroy/app:$PYTHONPATH"
cd /app/lib/search-and-destroy || exit 1
exec python3 app/main.py "$@"
