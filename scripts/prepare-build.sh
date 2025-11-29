#!/usr/bin/env bash
set -euo pipefail

# Prepare local environment for Flatpak builds

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
FLATPAK_ID="io.github.asafelobotomy.SearchAndDestroy"
MANIFEST_PATH="${REPO_ROOT}/packaging/flatpak/${FLATPAK_ID}.yml"
BUILD_DIR="${REPO_ROOT}/build/flatpak"

print_section() {
    echo -e "\n\033[1;36m➡️  $1\033[0m"
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo -e "\033[0;31m❌ Missing dependency: $1\033[0m" >&2
        echo "Install it and re-run this script." >&2
        exit 1
    fi
    echo -e "\033[0;32m✅ $1 found\033[0m"
}

print_section "Checking required commands"
require_cmd flatpak
require_cmd flatpak-builder

print_section "Ensuring Flathub remote is configured"
if flatpak remote-list | grep -q "^flathub"; then
    echo -e "\033[0;32m✅ Flathub remote already present\033[0m"
else
    flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    echo -e "\033[0;32m✅ Flathub remote added\033[0m"
fi

print_section "Validating Flatpak manifest"
if [ -f "${MANIFEST_PATH}" ]; then
    echo -e "\033[0;32m✅ Manifest found at ${MANIFEST_PATH}\033[0m"
else
    echo -e "\033[0;31m❌ Manifest not found at ${MANIFEST_PATH}\033[0m" >&2
    exit 1
fi

print_section "Preparing build directories"
mkdir -p "${BUILD_DIR}"
echo -e "\033[0;32m✅ Build directory ready at ${BUILD_DIR}\033[0m"

echo -e "\n\033[1;32m🎉 Environment is ready for Flatpak builds!\033[0m"
