# Installation Guide

This guide covers installation methods for **S&D - Search & Destroy** on Linux systems.

## System Requirements

### Hardware Requirements

- **Processor**: 64-bit x86/x64 processor
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 500 MB free disk space for application, additional space for virus definitions
- **Network**: Internet connection for virus definition updates

### Software Requirements

| Component            | Requirement                                           | Installation Command                    |
| -------------------- | ----------------------------------------------------- | --------------------------------------- |
| **Operating System** | Linux (tested on Ubuntu/Debian, Fedora, Arch)        | N/A                                     |
| **Python**           | Python 3.10 or higher                                 | `sudo apt install python3 python3-pip`  |
| **ClamAV Engine**    | ClamAV antivirus engine                               | `sudo apt install clamav clamav-daemon` |
| **GUI Framework**    | PyQt6                                                 | `pip install PyQt6>=6.5.0`              |
| **RKHunter**         | Rootkit scanner (optional)                            | `sudo apt install rkhunter`             |

## Installation Methods

### Method 1: DEB Package (Recommended for Debian/Ubuntu)

The easiest installation method for Debian-based distributions.

\`\`\`bash
# Download the latest .deb package from releases
wget https://github.com/asafelobotomy/xanadOS-Search_Destroy/releases/latest/download/xanados-search-destroy_3.0.0_amd64.deb

# Install the package
sudo dpkg -i xanados-search-destroy_3.0.0_amd64.deb

# Install dependencies if needed
sudo apt install -f

# Run the application
xanados-search-destroy
\`\`\`

### Method 2: Build from Source

For development or maximum control.

\`\`\`bash
# Clone repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Install system dependencies (Debian/Ubuntu)
sudo apt update
sudo apt install python3 python3-pip python3-venv clamav clamav-daemon rkhunter

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python app/main.py
\`\`\`

## Post-Installation Setup

### 1. Update Virus Definitions

\`\`\`bash
# Update ClamAV definitions
sudo freshclam
\`\`\`

### 2. Configure RKHunter (Optional)

\`\`\`bash
# Update RKHunter database
sudo rkhunter --update
sudo rkhunter --propupd
\`\`\`

## Support

For installation issues, check the [GitHub Issues](https://github.com/asafelobotomy/xanadOS-Search_Destroy/issues).
