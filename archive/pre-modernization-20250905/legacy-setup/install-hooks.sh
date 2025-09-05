#!/bin/bash
# Install git hooks for repository organization.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Check repository organization before commit

python3 scripts/check-organization.py
if [ $? -ne 0 ]; then
    echo "❌ Please fix organization issues before committing"
    echo "💡 Run: python3 dev/organize_repository_comprehensive.py"
    exit 1
fi
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "✅ Installed git hooks for repository organization"
