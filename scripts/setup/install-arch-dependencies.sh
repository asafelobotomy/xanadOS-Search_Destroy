#!/bin/bash
# System Dependencies Installation Script for Arch Linux
# xanadOS Search & Destroy - Security Application

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Installing System Dependencies for xanadOS Search & Destroy${NC}"
echo "=================================================================="

# Check if running on Arch Linux
if ! command -v pacman &> /dev/null; then
    echo -e "${RED}❌ This script is for Arch Linux systems only${NC}"
    echo "   For other distributions, check docs/user/Installation.md"
    exit 1
fi

# Check if not running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}❌ This script should NOT be run as root${NC}"
    echo "   It will use sudo only when necessary"
    exit 1
fi

echo -e "${YELLOW}📋 Installing Core Security Tools...${NC}"

# Install ClamAV antivirus engine
echo -e "${BLUE}🦠 Installing ClamAV antivirus engine...${NC}"
sudo pacman -S --needed --noconfirm clamav

# Install RKHunter rootkit scanner
echo -e "${BLUE}🔍 Installing RKHunter rootkit scanner...${NC}"
sudo pacman -S --needed --noconfirm rkhunter

# Install PolicyKit for privilege escalation
echo -e "${BLUE}🔐 Installing PolicyKit for secure privilege escalation...${NC}"
sudo pacman -S --needed --noconfirm polkit

# Install system monitoring and firewall tools
echo -e "${BLUE}🛡️ Installing system monitoring and firewall tools...${NC}"
sudo pacman -S --needed --noconfirm \
    ufw \
    net-tools \
    iproute2 \
    bind \
    which

# Install Python build dependencies
echo -e "${BLUE}🐍 Installing Python development dependencies...${NC}"
sudo pacman -S --needed --noconfirm \
    python \
    python-pip \
    python-virtualenv \
    base-devel

# Install Qt6 dependencies (already done, but ensure completeness)
echo -e "${BLUE}🖥️ Ensuring Qt6 GUI dependencies are installed...${NC}"
sudo pacman -S --needed --noconfirm \
    qt6-base \
    qt6-wayland \
    xcb-util-cursor \
    libxkbcommon-x11

echo -e "${YELLOW}🔧 Configuring Services...${NC}"

# Enable and start ClamAV freshclam service for virus definition updates
echo -e "${BLUE}📡 Setting up ClamAV virus definition updates...${NC}"
sudo systemctl enable clamav-freshclam.service
sudo systemctl start clamav-freshclam.service

# Update virus definitions
echo -e "${BLUE}📥 Updating virus definitions (this may take a while)...${NC}"
sudo freshclam || echo -e "${YELLOW}⚠️ Virus definitions update may have been delayed - will retry automatically${NC}"

# Update RKHunter database
echo -e "${BLUE}🔄 Updating RKHunter database...${NC}"
sudo rkhunter --update || echo -e "${YELLOW}⚠️ RKHunter update may have failed - continuing anyway${NC}"

# Enable UFW firewall but don't start it (user choice)
echo -e "${BLUE}🔥 Setting up UFW firewall (enabling but not starting)...${NC}"
sudo ufw --force enable

echo -e "${YELLOW}🔍 Verifying Installation...${NC}"

# Verify installations
echo -e "${BLUE}✅ Verifying ClamAV installation...${NC}"
if clamscan --version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ ClamAV: $(clamscan --version | head -n1)${NC}"
else
    echo -e "${RED}❌ ClamAV installation failed${NC}"
fi

echo -e "${BLUE}✅ Verifying RKHunter installation...${NC}"
if rkhunter --version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ RKHunter: $(rkhunter --version | head -n1)${NC}"
else
    echo -e "${RED}❌ RKHunter installation failed${NC}"
fi

echo -e "${BLUE}✅ Verifying PolicyKit installation...${NC}"
if pkexec --version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PolicyKit: Available${NC}"
else
    echo -e "${RED}❌ PolicyKit installation failed${NC}"
fi

echo -e "${BLUE}✅ Verifying UFW firewall...${NC}"
if ufw --version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ UFW: $(ufw --version | head -n1)${NC}"
else
    echo -e "${RED}❌ UFW installation failed${NC}"
fi

echo -e "${GREEN}🎉 System Dependencies Installation Complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Install Python dependencies: make install"
echo "2. Run the application: make run"
echo "3. Check system status in the application dashboard"
echo ""
echo -e "${YELLOW}🔧 Optional Configuration:${NC}"
echo "• Install security policies: ./scripts/setup/install-security-hardening.sh"
echo "• Configure firewall rules manually if needed"
echo "• Set up scheduled scans in the application"
echo ""
echo -e "${BLUE}📚 For more information, see docs/user/Installation.md${NC}"
