#!/bin/bash
# Flathub submission preparation script for S&D - Search & Destroy

set -e

echo "🚀 Preparing S&D - Search & Destroy for Flathub submission..."

# Check if we're in the correct directory
if [[ ! -f "app/main.py" ]]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Verify required files exist
echo "📋 Checking required files..."
required_files=(
    "packaging/flatpak/org.xanados.SearchAndDestroy.yml"
    "packaging/flatpak/org.xanados.SearchAndDestroy.desktop"
    "packaging/flatpak/org.xanados.SearchAndDestroy.metainfo.xml"
    "packaging/flatpak/python3-requirements.json"
    "packaging/flatpak/flathub.json"
    "packaging/flatpak/search-and-destroy.sh"
    "packaging/icons/org.xanados.SearchAndDestroy.svg"
    "LICENSE"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Check icon files
echo "🖼️  Checking icon files..."
icon_sizes=(16 32 48 64 128)
for size in "${icon_sizes[@]}"; do
    icon_file="packaging/icons/org.xanados.SearchAndDestroy-${size}.png"
    if [[ -f "$icon_file" ]]; then
        echo "✅ Found: $icon_file"
    else
        echo "⚠️  Missing icon: $icon_file (optional but recommended)"
    fi
done

# Get current commit hash
COMMIT_HASH=$(git rev-parse HEAD)
echo "📝 Current commit hash: $COMMIT_HASH"

# Update VERSION
VERSION=$(cat VERSION | tr -d '\n')
echo "📦 Current version: $VERSION"

# Create tag if it doesn't exist
TAG_NAME="v${VERSION}"
if ! git tag | grep -q "^${TAG_NAME}$"; then
    echo "🏷️  Creating tag: $TAG_NAME"
    git tag -a "$TAG_NAME" -m "Release version $VERSION for Flathub"
    echo "⚠️  Don't forget to push the tag: git push origin $TAG_NAME"
else
    echo "✅ Tag $TAG_NAME already exists"
fi

# Update the manifest with the correct commit hash
echo "🔧 Updating manifest with commit hash..."
sed -i "s/commit: REPLACE_WITH_ACTUAL_COMMIT_HASH/commit: $COMMIT_HASH/" packaging/flatpak/org.xanados.SearchAndDestroy.yml

echo ""
echo "🎉 Flathub preparation complete!"
echo ""
echo "📋 Next steps for Flathub submission:"
echo "1. Ensure your repository is pushed to GitHub with the latest changes"
echo "2. Push the tag if created: git push origin $TAG_NAME"
echo "3. Fork the Flathub repository: https://github.com/flathub/flathub"
echo "4. Clone your fork and checkout the new-pr branch"
echo "5. Copy the following files to the new app directory:"
echo "   - org.xanados.SearchAndDestroy.yml"
echo "   - org.xanados.SearchAndDestroy.metainfo.xml"
echo "   - org.xanados.SearchAndDestroy.desktop"
echo "   - python3-requirements.json"
echo "   - flathub.json"
echo "6. Test the build locally with flatpak-builder"
echo "7. Submit a pull request to Flathub"
echo ""
echo "📚 Documentation: https://docs.flathub.org/docs/for-app-authors/submission"
echo ""
echo "Files ready for submission in: packaging/flatpak/"
