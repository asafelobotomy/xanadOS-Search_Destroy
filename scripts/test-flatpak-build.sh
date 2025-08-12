#!/bin/bash
# Local Flatpak build testing script for S&D - Search & Destroy

set -e

echo "🔨 Testing Flatpak build for S&D - Search & Destroy..."

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "❌ flatpak-builder is not installed. Please install it first:"
    echo "   sudo apt install flatpak-builder (Debian/Ubuntu)"
    echo "   sudo dnf install flatpak-builder (Fedora)"
    echo "   sudo pacman -S flatpak-builder (Arch)"
    exit 1
fi

# Check if org.flatpak.Builder is available
if ! flatpak list | grep -q "org.flatpak.Builder"; then
    echo "📦 Installing org.flatpak.Builder..."
    flatpak install -y flathub org.flatpak.Builder
fi

# Ensure Flathub remote is added
if ! flatpak remotes | grep -q "flathub"; then
    echo "📦 Adding Flathub remote..."
    flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
fi

# Clean previous builds
BUILD_DIR="build"
REPO_DIR="repo"
if [[ -d "$BUILD_DIR" ]]; then
    echo "🧹 Cleaning previous build directory..."
    rm -rf "$BUILD_DIR"
fi
if [[ -d "$REPO_DIR" ]]; then
    echo "🧹 Cleaning previous repo directory..."
    rm -rf "$REPO_DIR"
fi

# Change to packaging/flatpak directory
cd packaging/flatpak

# Run the build
echo "🔨 Building Flatpak package..."
flatpak run --command=flathub-build org.flatpak.Builder \
    --verbose \
    --ccache \
    --force-clean \
    --repo=../../repo \
    ../../build \
    org.xanados.SearchAndDestroy.yml

if [[ $? -eq 0 ]]; then
    echo "✅ Build successful!"
    
    # Add the local repo
    echo "📦 Adding local repository..."
    flatpak remote-add --user --no-gpg-verify search-and-destroy-local file://$(pwd)/../../repo
    
    # Install the application
    echo "📦 Installing application locally..."
    flatpak install --user -y search-and-destroy-local org.xanados.SearchAndDestroy
    
    echo ""
    echo "🎉 Build and install successful!"
    echo ""
    echo "🚀 To test the application, run:"
    echo "   flatpak run org.xanados.SearchAndDestroy"
    echo ""
    echo "🧹 To clean up after testing:"
    echo "   flatpak uninstall --user org.xanados.SearchAndDestroy"
    echo "   flatpak remote-delete --user search-and-destroy-local"
    echo "   rm -rf ../../build ../../repo"
    
else
    echo "❌ Build failed!"
    echo "Please check the output above for errors."
    exit 1
fi
