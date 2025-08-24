#!/bin/bash

# Flathub Submission Script for Search & Destroy
# This script automates the submission process to your existing Flathub fork

set -e

APP_ID="io.github.asafelobotomy.SearchAndDestroy"
VERSION="2.11.0"
COMMIT_HASH="1259106378521bfec9492f5d14d5f0e999dba772"

echo "🚀 Search & Destroy v${VERSION} - Flathub Submission"
echo "=============================================="
echo ""

# Get the current directory (should be the repo root)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "📁 Repository root: ${REPO_ROOT}"

# Check if required files exist
echo "📋 Checking required files..."
REQUIRED_FILES=(
    "packaging/flatpak/${APP_ID}.yml"
    "packaging/flatpak/${APP_ID}.metainfo.xml"
    "packaging/flatpak/${APP_ID}.desktop"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "${REPO_ROOT}/${file}" ]]; then
        echo "✅ Found: ${file}"
    else
        echo "❌ Missing: ${file}"
        exit 1
    fi
done

echo ""
echo "🍴 Setting up Flathub submission..."

# Ask for GitHub username
read -p "🔑 Enter your GitHub username: " GITHUB_USERNAME
if [[ -z "$GITHUB_USERNAME" ]]; then
    echo "❌ GitHub username is required"
    exit 1
fi

# Create a temporary working directory
WORK_DIR="/tmp/flathub-submission-$$"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "📥 Cloning your Flathub fork..."
if git clone "git@github.com:${GITHUB_USERNAME}/flathub.git" 2>/dev/null; then
    echo "✅ Cloned via SSH"
elif git clone "https://github.com/${GITHUB_USERNAME}/flathub.git"; then
    echo "✅ Cloned via HTTPS"
else
    echo "❌ Failed to clone your fork. Please check:"
    echo "   1. Your fork exists at: https://github.com/${GITHUB_USERNAME}/flathub"
    echo "   2. The repository is accessible"
    exit 1
fi

cd flathub

echo "🔧 Setting up upstream and branches..."
git remote add upstream https://github.com/flathub/flathub.git
git fetch upstream

# Check if new-pr branch exists locally or remotely
if git show-ref --verify --quiet refs/heads/new-pr; then
    echo "✅ Found local new-pr branch"
    git checkout new-pr
elif git show-ref --verify --quiet refs/remotes/origin/new-pr; then
    echo "✅ Found remote new-pr branch"
    git checkout -b new-pr origin/new-pr
elif git show-ref --verify --quiet refs/remotes/upstream/new-pr; then
    echo "✅ Creating new-pr from upstream"
    git checkout -b new-pr upstream/new-pr
    git push origin new-pr
else
    echo "⚠️  new-pr branch not found, using master as base"
    git checkout master
fi

echo "🌿 Creating submission branch..."
if git show-ref --verify --quiet refs/heads/add-search-and-destroy; then
    echo "⚠️  Branch add-search-and-destroy already exists, using it"
    git checkout add-search-and-destroy
else
    git checkout -b "add-search-and-destroy"
fi

echo "📁 Creating app directory..."
mkdir -p "$APP_ID"
cd "$APP_ID"

echo "📄 Copying submission files..."
cp "${REPO_ROOT}/packaging/flatpak/${APP_ID}.yml" .
cp "${REPO_ROOT}/packaging/flatpak/${APP_ID}.metainfo.xml" .
cp "${REPO_ROOT}/packaging/flatpak/${APP_ID}.desktop" .

echo "🔧 Verifying commit hash in manifest..."
if grep -q "$COMMIT_HASH" "${APP_ID}.yml"; then
    echo "✅ Commit hash verified in manifest"
else
    echo "⚠️  Updating commit hash in manifest..."
    sed -i "s/commit: .*/commit: ${COMMIT_HASH}/" "${APP_ID}.yml"
fi

echo "📋 Files ready for submission:"
ls -la

echo ""
echo "🔍 Validating submission (optional but recommended)..."
echo "You can run these commands to validate:"
echo "  flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest ${APP_ID}.yml"
echo ""

# Add and commit
echo "📤 Committing submission..."
git add .
git commit -m "Add ${APP_ID}

This submission adds Search & Destroy v${VERSION}, a comprehensive malware detection and system security tool.

Key features:
- Real-time malware detection with ClamAV integration
- System hardening and vulnerability assessment
- Network security monitoring and firewall management
- Sandboxed Flatpak application with secure permissions

App ID: ${APP_ID}
Version: ${VERSION}
Repository: https://github.com/asafelobotomy/xanadOS-Search_Destroy
License: MIT"

echo "🚀 Pushing to your fork..."
if git push origin add-search-and-destroy; then
    echo "✅ Successfully pushed to your fork"
else
    echo "⚠️  Push failed, but files are ready. You can manually push:"
    echo "   git push origin add-search-and-destroy"
fi

echo ""
echo "🎉 Submission prepared successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Visit: https://github.com/${GITHUB_USERNAME}/flathub"
echo "2. Create a Pull Request:"
echo "   - From branch: add-search-and-destroy"
echo "   - To repository: flathub/flathub"
if git show-ref --verify --quiet refs/remotes/upstream/new-pr; then
    echo "   - Base branch: new-pr"
else
    echo "   - Base branch: master"
fi
echo "   - Title: Add ${APP_ID}"
echo ""
echo "📋 Alternative: Create PR directly via URL:"
if git show-ref --verify --quiet refs/remotes/upstream/new-pr; then
    echo "   https://github.com/flathub/flathub/compare/new-pr...${GITHUB_USERNAME}:add-search-and-destroy"
else
    echo "   https://github.com/flathub/flathub/compare/master...${GITHUB_USERNAME}:add-search-and-destroy"
fi
echo ""
echo "🧹 Cleaning up temporary files..."
cd /
rm -rf "$WORK_DIR"

echo ""
echo "✅ Ready for Flathub submission!"
echo "🌍 Your app will soon be available to millions of Linux users!"
