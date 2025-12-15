#!/bin/bash
# Build DEB package for xanadOS Search & Destroy
# Compatible with Debian, Ubuntu, Linux Mint, Pop!_OS, etc.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔧 Building DEB Package for xanadOS Search & Destroy${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if running on Debian-based system
if ! command -v dpkg-buildpackage &> /dev/null; then
    echo -e "${RED}❌ Error: dpkg-buildpackage not found${NC}"
    echo -e "${YELLOW}Installing DEB build tools...${NC}"
    sudo apt-get update
    sudo apt-get install -y build-essential debhelper devscripts dh-python python3-all \
        python3-setuptools python3-pip desktop-file-utils appstream
fi

# Get version from VERSION file
VERSION=$(cat VERSION | tr -d '\n' | tr -d ' ')
echo -e "${GREEN}📦 Version: ${VERSION}${NC}"

# Create build directory
BUILD_DIR="/tmp/xanados-search-destroy-${VERSION}"
echo -e "${YELLOW}Creating build directory: ${BUILD_DIR}${NC}"

# Clean old build directory if exists
if [ -d "${BUILD_DIR}" ]; then
    rm -rf "${BUILD_DIR}"
fi

# Copy source to build directory
echo -e "${YELLOW}Copying source files...${NC}"
mkdir -p "${BUILD_DIR}"
git archive HEAD | tar -x -C "${BUILD_DIR}"

# Copy debian directory
cp -r packaging/debian "${BUILD_DIR}/"

# Make rules executable
chmod +x "${BUILD_DIR}/debian/rules"

# Build package
echo -e "${YELLOW}Building DEB package...${NC}"
cd "${BUILD_DIR}"
dpkg-buildpackage -us -uc -b

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ DEB package built successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📦 Package created:${NC}"
    ls -lh /tmp/xanados-search-destroy_${VERSION}*.deb
    echo ""
    echo -e "${YELLOW}To install:${NC}"
    echo "  sudo dpkg -i /tmp/xanados-search-destroy_${VERSION}*.deb"
    echo "  sudo apt-get install -f  # If there are dependency issues"
    echo ""
    echo -e "${YELLOW}Or with APT:${NC}"
    echo "  sudo apt install /tmp/xanados-search-destroy_${VERSION}*.deb"
    echo ""
    echo -e "${BLUE}📝 Additional files:${NC}"
    ls -lh /tmp/xanados-search-destroy_${VERSION}*.{dsc,changes,buildinfo} 2>/dev/null || true
    echo ""
    
    # Copy to packaging output directory
    mkdir -p packaging/deb/output
    cp /tmp/xanados-search-destroy_${VERSION}*.deb packaging/deb/output/
    echo -e "${GREEN}Package also saved to: packaging/deb/output/${NC}"
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ DEB build failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
