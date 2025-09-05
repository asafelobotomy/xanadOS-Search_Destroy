#!/bin/bash
# Pre-commit hook to automatically sync versions with VERSION file
# Usage: Add this to your pre-commit hooks or run manually before commits

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
cd "$REPO_ROOT"

echo "🔄 Pre-commit: Syncing versions with VERSION file..."

# Run version sync
python scripts/tools/version_manager.py --sync

# Check if any files were modified
if git diff --quiet; then
    echo "✅ All versions already synchronized"
else
    echo "📝 Version files updated - staging changes..."

    # Stage updated files
    git add package.json pyproject.toml README.md config/*.toml

    echo "✅ Version synchronization complete and staged"
fi
