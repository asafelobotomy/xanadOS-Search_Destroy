#!/usr/bin/env bash
set -euo pipefail

echo "Verifying repository structure..."

status=0

require_dir() {
  local d="$1"; local why="$2"
  if [ ! -d "$d" ]; then
    echo "[STRUCTURE] Missing directory: $d — $why"
    status=1
  fi
}

suggest_dir() {
  local d="$1"; local why="$2"
  if [ ! -d "$d" ]; then
    echo "[SUGGESTION] Consider adding: $d — $why"
  fi
}

# Required core directories for most repos
suggest_dir src "Primary source code lives here; mirrors tests/."
suggest_dir tests "Put unit/integration tests here mirroring src/."
suggest_dir .github/workflows "CI workflows and automation."
suggest_dir docs "User/developer documentation."
suggest_dir scripts "Utility scripts; referenced by CI."

# Ensure Copilot repo instructions exist
if [ ! -f .github/copilot-instructions.md ] && [ ! -d .github/chatmodes ] && [ ! -d .github/prompts ]; then
  echo "[STRUCTURE] Add Copilot instructions: .github/copilot-instructions.md or .github/chatmodes/*.chatmode.md or .github/prompts/*.prompt.md"
  status=1
fi

exit $status
