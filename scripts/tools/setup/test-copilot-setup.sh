#!/bin/bash

# Test Copilot Setup Script
# Verifies that GitHub Copilot instructions are properly configured

set -euo pipefail

echo "🧪 Testing GitHub Copilot Setup..."
echo

# Check if copilot-instructions.md exists
if [[ -f ".github/copilot-instructions.md" ]]; then
    echo "✅ Found .github/copilot-instructions.md"
else
    echo "❌ Missing .github/copilot-instructions.md"
    exit 1
fi

# Validate the file content
if grep -q "applyTo.*\*\*\/\*" ".github/copilot-instructions.md"; then
    echo "✅ Copilot instructions file has proper frontmatter"
else
    echo "❌ Copilot instructions file missing applyTo frontmatter"
    exit 1
fi

# Check file size (should be reasonable)
file_size=$(wc -c < ".github/copilot-instructions.md")
if [[ $file_size -gt 100 ]] && [[ $file_size -lt 10000 ]]; then
    echo "✅ Copilot instructions file has reasonable size ($file_size bytes)"
else
    echo "⚠️  Copilot instructions file size is unusual ($file_size bytes)"
fi

# Test GitHub Copilot Chat command format
echo
echo "📝 Test your setup with GitHub Copilot Chat:"
echo "   Open VS Code in this directory"
echo "   Open Copilot Chat (Ctrl+Shift+I)"
echo "   Type: @github use .github/copilot-instructions.md"
echo

echo "🎉 Setup verification complete!"
echo "   Repository: $(git config --get remote.origin.url 2>/dev/null || echo 'No remote configured')"
echo "   Instructions: $(wc -l < .github/copilot-instructions.md) lines"
echo
