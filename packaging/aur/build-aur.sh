#!/bin/bash
# Build AUR package for xanadOS Search & Destroy
# For Arch Linux, Manjaro, EndeavourOS, etc.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔧 Building AUR Package for xanadOS Search & Destroy${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if running on Arch-based system
if ! command -v makepkg &> /dev/null; then
    echo -e "${RED}❌ Error: makepkg not found${NC}"
    echo -e "${YELLOW}This script should be run on Arch Linux or derivatives${NC}"
    exit 1
fi

# Get version from VERSION file
VERSION=$(cat VERSION | tr -d '\n' | tr -d ' ')
echo -e "${GREEN}📦 Version: ${VERSION}${NC}"

# Create build directory
BUILD_DIR="/tmp/xanados-search-destroy-aur"
echo -e "${YELLOW}Creating AUR build directory: ${BUILD_DIR}${NC}"

# Clean old build directory if exists
if [ -d "${BUILD_DIR}" ]; then
    rm -rf "${BUILD_DIR}"
fi

# Copy PKGBUILD and related files
mkdir -p "${BUILD_DIR}"
cp packaging/aur/PKGBUILD "${BUILD_DIR}/"
cp packaging/aur/.SRCINFO "${BUILD_DIR}/" 2>/dev/null || true

# Update version in PKGBUILD if needed
cd "${BUILD_DIR}"
sed -i "s/^pkgver=.*/pkgver=${VERSION}/" PKGBUILD

# Generate .SRCINFO
echo -e "${YELLOW}Generating .SRCINFO...${NC}"
makepkg --printsrcinfo > .SRCINFO

# Build package
echo -e "${YELLOW}Building AUR package...${NC}"
makepkg -sf --noconfirm

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ AUR package built successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📦 Package created:${NC}"
    ls -lh "${BUILD_DIR}"/xanados-search-destroy-*.pkg.tar.zst
    echo ""
    echo -e "${YELLOW}To install:${NC}"
    echo "  sudo pacman -U ${BUILD_DIR}/xanados-search-destroy-${VERSION}*.pkg.tar.zst"
    echo ""
    echo -e "${YELLOW}To publish to AUR:${NC}"
    echo "  1. Copy PKGBUILD and .SRCINFO to your AUR repository"
    echo "  2. Update checksums: updpkgsums"
    echo "  3. Test build: makepkg -si"
    echo "  4. Commit and push to AUR"
    echo ""
    
    # Copy back to packaging directory
    mkdir -p "$(git rev-parse --show-toplevel)/packaging/aur/output"
    cp "${BUILD_DIR}"/xanados-search-destroy-*.pkg.tar.zst "$(git rev-parse --show-toplevel)/packaging/aur/output/"
    cp "${BUILD_DIR}"/.SRCINFO "$(git rev-parse --show-toplevel)/packaging/aur/"
    echo -e "${GREEN}Package and .SRCINFO saved to: packaging/aur/${NC}"
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ AUR build failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
