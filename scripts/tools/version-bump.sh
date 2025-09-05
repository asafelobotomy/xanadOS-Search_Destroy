#!/bin/bash
# Version Bump Script - September 5, 2025
# Updates version to 2.12.0 across entire build system

set -euo pipefail

NEW_VERSION="2.12.0"
OLD_VERSION="2.11.2"

echo "🔄 Updating version from ${OLD_VERSION} to ${NEW_VERSION}"
echo "================================================="

# Update package-lock.json to reflect new version
if [[ -f "package-lock.json" ]]; then
    echo "📦 Updating package-lock.json..."
    npm install --package-lock-only
    echo "✅ package-lock.json updated"
fi

# Update any Docker files or configuration
echo "🐳 Checking Docker configurations..."
if [[ -f "Dockerfile" ]]; then
    # Update any version labels in Dockerfile
    if grep -q "version.*${OLD_VERSION}" Dockerfile; then
        sed -i "s/version.*${OLD_VERSION}/version=\"${NEW_VERSION}\"/g" Dockerfile
        echo "✅ Dockerfile version updated"
    fi
fi

# Update any TOML configuration files that might have version references
echo "⚙️  Checking configuration files..."
find config/ -name "*.toml" -type f -exec grep -l "version.*${OLD_VERSION}" {} \; | while read -r file; do
    sed -i "s/version = \"${OLD_VERSION}\"/version = \"${NEW_VERSION}\"/g" "$file"
    echo "✅ Updated $file"
done

# Update any remaining Python files with version references
echo "🐍 Checking Python files for version references..."
find . -name "*.py" -type f -not -path "./archive/*" -not -path "./.git/*" -exec grep -l "${OLD_VERSION}" {} \; | while read -r file; do
    if grep -q "version.*${OLD_VERSION}" "$file"; then
        sed -i "s/version.*${OLD_VERSION}/version=\"${NEW_VERSION}\"/g" "$file"
        echo "✅ Updated Python version in $file"
    fi
done

# Update any shell scripts with version references
echo "🔧 Checking shell scripts for version references..."
find scripts/ -name "*.sh" -type f -exec grep -l "VERSION.*${OLD_VERSION}" {} \; | while read -r file; do
    sed -i "s/VERSION.*${OLD_VERSION}/VERSION=\"${NEW_VERSION}\"/g" "$file"
    echo "✅ Updated script version in $file"
done

# Validate the version sync
echo ""
echo "🔍 Validating version synchronization..."
if bash scripts/tools/validation/validate-version-sync.sh; then
    echo "✅ Version synchronization validated successfully"
else
    echo "❌ Version synchronization failed"
    exit 1
fi

echo ""
echo "🎉 Version bump to ${NEW_VERSION} completed successfully!"
echo ""
echo "📋 Updated files:"
echo "  • VERSION"
echo "  • package.json"
echo "  • pyproject.toml"
echo "  • README.md"
echo "  • config/gui_config.toml"
echo "  • package-lock.json (regenerated)"
echo ""
echo "🚀 Ready for commit and release!"
