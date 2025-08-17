#!/bin/bash
# VS Code File Restoration Prevention Script
# This script helps prevent VS Code from restoring deleted files

echo "🔍 Checking for deleted files that are still tracked in git..."

# Check for files that are deleted but still in git index
DELETED_FILES=$(git ls-files --deleted 2>/dev/null)

if [ -n "$DELETED_FILES" ]; then
    echo "⚠️  Found files deleted from filesystem but still tracked in git:"
    echo "$DELETED_FILES"
    echo ""
    echo "These files may be automatically restored by VS Code."
    echo "To permanently remove them from git tracking, run:"
    echo ""
    for file in $DELETED_FILES; do
        echo "  git rm \"$file\""
    done
    echo ""
    echo "Then commit the changes:"
    echo "  git commit -m \"Remove deleted files from git tracking\""
    echo ""
    exit 1
else
    echo "✅ No deleted files found in git index."
fi

# Check VS Code workspace storage for this project
WORKSPACE_ID=$(find ~/.config/Code/User/workspaceStorage -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | grep -v "workspaceStorage" | head -1)

if [ -n "$WORKSPACE_ID" ]; then
    echo "🧹 Cleaning VS Code workspace cache for project..."
    
    # Remove any cached file references that might cause restoration
    find ~/.config/Code/User/workspaceStorage/$WORKSPACE_ID -name "*recent*" -type f -delete 2>/dev/null
    find ~/.config/Code/User/workspaceStorage/$WORKSPACE_ID -name "*history*" -type f -delete 2>/dev/null
    
    echo "✅ VS Code workspace cache cleaned."
fi

echo "✅ File restoration prevention check complete!"
