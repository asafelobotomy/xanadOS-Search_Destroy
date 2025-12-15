#!/bin/bash
# Build RPM package for xanadOS Search & Destroy
# Compatible with Fedora, RHEL, CentOS, openSUSE

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔧 Building RPM Package for xanadOS Search & Destroy${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if running on RPM-based system
if ! command -v rpmbuild &> /dev/null; then
    echo -e "${RED}❌ Error: rpmbuild not found${NC}"
    echo -e "${YELLOW}Installing RPM build tools...${NC}"
    
    if [ -f /etc/fedora-release ]; then
        sudo dnf install -y rpm-build rpmdevtools
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y rpm-build rpmdevtools
    elif [ -f /etc/SuSE-release ] || [ -f /etc/SUSE-brand ]; then
        sudo zypper install -y rpm-build
    else
        echo -e "${RED}❌ Error: Unsupported distribution for RPM building${NC}"
        exit 1
    fi
fi

# Get version from VERSION file
VERSION=$(cat VERSION | tr -d '\n' | tr -d ' ')
echo -e "${GREEN}📦 Version: ${VERSION}${NC}"

# Setup RPM build directories
echo -e "${YELLOW}Setting up RPM build environment...${NC}"
rpmdev-setuptree 2>/dev/null || mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copy spec file
echo -e "${YELLOW}Copying spec file...${NC}"
cp packaging/rpm/xanados-search-destroy.spec ~/rpmbuild/SPECS/

# Create source tarball
echo -e "${YELLOW}Creating source tarball...${NC}"
TARBALL="xanados-search-destroy-${VERSION}.tar.gz"
git archive --format=tar.gz --prefix="xanados-search-destroy-${VERSION}/" HEAD > ~/rpmbuild/SOURCES/${TARBALL}

# Build RPM
echo -e "${YELLOW}Building RPM package...${NC}"
cd ~/rpmbuild/SPECS
rpmbuild -ba xanados-search-destroy.spec

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ RPM package built successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📦 Packages created:${NC}"
    ls -lh ~/rpmbuild/RPMS/noarch/xanados-search-destroy*.rpm
    echo ""
    echo -e "${BLUE}📦 Source RPM:${NC}"
    ls -lh ~/rpmbuild/SRPMS/xanados-search-destroy*.src.rpm
    echo ""
    echo -e "${YELLOW}To install:${NC}"
    echo "  sudo rpm -ivh ~/rpmbuild/RPMS/noarch/xanados-search-destroy-${VERSION}-1.*.noarch.rpm"
    echo ""
    echo -e "${YELLOW}Or with DNF/YUM:${NC}"
    echo "  sudo dnf install ~/rpmbuild/RPMS/noarch/xanados-search-destroy-${VERSION}-1.*.noarch.rpm"
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ RPM build failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
