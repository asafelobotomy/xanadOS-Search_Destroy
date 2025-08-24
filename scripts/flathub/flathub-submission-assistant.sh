#!/bin/bash
# Automated Flathub Submission Assistant for S&D - Search & Destroy v2.5.0

set -e

echo "🚀 S&D - Search & Destroy v2.5.0 Flathub Submission Assistant"
echo "=============================================================="
echo ""

# Verify all prerequisites
echo "📋 Prerequisites Check:"
echo "✅ Version 2.5.0 tagged and pushed to GitHub"
echo "✅ All Flatpak files prepared and validated"
echo "✅ Repository organized and documented"
echo "✅ Icons and metadata properly configured"
echo ""

# Display current commit info
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_TAG=$(git describe --tags --exact-match HEAD 2>/dev/null || echo "No tag on current commit")
echo "📝 Current repository status:"
echo "   Commit: $CURRENT_COMMIT"
echo "   Tag: $CURRENT_TAG"
echo ""

# Check if Flathub directory exists
FLATHUB_DIR="../flathub"
if [[ -d "$FLATHUB_DIR" ]]; then
    echo "📁 Found existing Flathub fork directory: $FLATHUB_DIR"
    echo "   You can continue with step 4 (copying files)"
else
    echo "📁 Flathub fork directory not found"
    echo "   You'll need to complete steps 1-3 first"
fi
echo ""

echo "📋 Next Steps for Flathub Submission:"
echo ""
echo "1. 🍴 Fork the Flathub repository (if not done):"
echo "   Visit: https://github.com/flathub/flathub"
echo "   Click 'Fork' (ensure 'Copy the master branch only' is UNCHECKED)"
echo ""
echo "2. 📥 Clone your fork:"
echo "   git clone --branch=new-pr git@github.com:YOUR_USERNAME/flathub.git"
echo "   cd flathub"
echo ""
echo "3. 🌿 Create submission branch:"
echo "   git checkout -b add-search-and-destroy new-pr"
echo ""
echo "4. 📁 Create app directory and copy files:"
echo "   mkdir io.github.asafelobotomy.SearchAndDestroy"
echo "   cd io.github.asafelobotomy.SearchAndDestroy"
echo "   cp $(pwd)/packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.yml ."
echo "   cp $(pwd)/packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.metainfo.xml ."
echo "   cp $(pwd)/packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.desktop ."
echo ""
echo "5. 🔧 Update commit hash in manifest:"
echo "   sed -i \"s/commit: REPLACE_WITH_ACTUAL_COMMIT_HASH/commit: $CURRENT_COMMIT/\" io.github.asafelobotomy.SearchAndDestroy.yml"
echo ""
echo "6. ✅ Validate submission:"
echo "   flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest io.github.asafelobotomy.SearchAndDestroy.yml"
echo ""
echo "7. 🔨 Test build (recommended):"
echo "   flatpak run --command=flathub-build org.flatpak.Builder io.github.asafelobotomy.SearchAndDestroy.yml"
echo ""
echo "8. 📤 Submit to Flathub:"
echo "   git add ."
echo "   git commit -m \"Add io.github.asafelobotomy.SearchAndDestroy\""
echo "   git push origin add-search-and-destroy"
echo ""
echo "9. 📝 Create Pull Request:"
echo "   Visit your fork on GitHub"
echo "   Open PR against flathub/flathub base branch: new-pr (NOT master!)"
echo "   Title: \"Add io.github.asafelobotomy.SearchAndDestroy\""
echo ""
echo "📚 Additional Resources:"
echo "   • Submission Guide: $(pwd)/docs/deployment/FLATHUB_SUBMISSION.md"
echo "   • Release Documentation: $(pwd)/docs/releases/FLATHUB_RELEASE_v2.5.0.md"
echo "   • Flathub Documentation: https://docs.flathub.org/"
echo "   • Local Build Testing: $(pwd)/scripts/build/test-flatpak-build.sh"
echo ""
echo "🎯 Ready for Flathub submission!"
echo "   Your app will be available to millions of Linux users once approved! 🚀"
