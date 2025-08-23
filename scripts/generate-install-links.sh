#!/bin/bash

# VS Code Installation URL Generator for GitHub Copilot Enhancement Framework
# Based on patterns from github/awesome-copilot

set -euo pipefail

# Configuration
REPO_BASE_URL="https://raw.githubusercontent.com/YOUR_ORG/YOUR_REPO/main"
VSCODE_BASE_URL="https://vscode.dev/redirect?url="
VSCODE_INSIDERS_BASE_URL="https://insiders.vscode.dev/redirect?url="

# Badge URLs
VSCODE_INSTALL_BADGE="https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white"
VSCODE_INSIDERS_INSTALL_BADGE="https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white"

# Function to generate install URLs
generate_install_urls() {
    local file_path="$1"
    local file_type="$2"

    # URL encode the file path
    local encoded_path=$(echo "${REPO_BASE_URL}/${file_path}" | sed 's/:/:%3A/g' | sed 's|/|%2F|g')

    # Generate VS Code URLs based on file type
    case "$file_type" in
        "chatmode")
            local vscode_url="${VSCODE_BASE_URL}vscode%3Achat-mode%2Finstall%3Furl%3D${encoded_path}"
            local vscode_insiders_url="${VSCODE_INSIDERS_BASE_URL}vscode-insiders%3Achat-mode%2Finstall%3Furl%3D${encoded_path}"
            ;;
        "prompt")
            local vscode_url="${VSCODE_BASE_URL}vscode%3Achat-prompt%2Finstall%3Furl%3D${encoded_path}"
            local vscode_insiders_url="${VSCODE_INSIDERS_BASE_URL}vscode-insiders%3Achat-prompt%2Finstall%3Furl%3D${encoded_path}"
            ;;
        "instructions")
            local vscode_url="${VSCODE_BASE_URL}vscode%3Achat-instructions%2Finstall%3Furl%3D${encoded_path}"
            local vscode_insiders_url="${VSCODE_INSIDERS_BASE_URL}vscode-insiders%3Achat-instructions%2Finstall%3Furl%3D${encoded_path}"
            ;;
        *)
            echo "Unknown file type: $file_type"
            return 1
            ;;
    esac

    # Generate markdown badges
    echo "[![Install in VS Code](${VSCODE_INSTALL_BADGE})](${vscode_url})"
    echo "[![Install in VS Code Insiders](${VSCODE_INSIDERS_INSTALL_BADGE})](${vscode_insiders_url})"
}

# Function to process a directory and generate badges
process_directory() {
    local dir="$1"
    local file_type="$2"
    local extension="$3"

    echo "## ${file_type^} Installation Badges"
    echo ""

    if [[ -d "$dir" ]]; then
        for file in "$dir"/*."$extension".md; do
            if [[ -f "$file" ]]; then
                local filename=$(basename "$file")
                local relative_path="${dir#./}/$filename"

                echo "### $filename"
                generate_install_urls "$relative_path" "$file_type"
                echo ""
            fi
        done
    else
        echo "Directory $dir not found"
    fi
}

# Main execution
main() {
    echo "# VS Code Installation Links"
    echo ""
    echo "This document contains direct installation links for VS Code and VS Code Insiders."
    echo ""

    # Process chatmodes
    process_directory ".github/chatmodes" "chatmode" "chatmode"

    # Process prompts
    process_directory ".github/prompts" "prompt" "prompt"

    # Process instructions
    process_directory ".github/instructions" "instructions" "instructions"
}

# Check if running from correct directory
if [[ ! -d ".github" ]]; then
    echo "Error: Must be run from repository root (directory containing .github folder)"
    exit 1
fi

# Generate the installation documentation
main > "INSTALL_LINKS.md"

echo "✅ Installation links generated in INSTALL_LINKS.md"
echo "📝 Remember to update REPO_BASE_URL in the script with your actual repository URL"
