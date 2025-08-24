#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHATMODES_DIR="$ROOT_DIR/.github/chatmodes"
SCHEMA_FILE="$ROOT_DIR/.github/schemas/chatmode.schema.json"

if [[ ! -d "$CHATMODES_DIR" ]]; then
  echo "No chatmodes directory found at $CHATMODES_DIR. Skipping."
  exit 0
fi

# Default required headings (can be overridden via schema)
mapfile -t REQUIRED < <(jq -r '.properties.requiredHeadings.default[]' "$SCHEMA_FILE" 2>/dev/null || echo -e "# \n## Description\n## Role\n## Response Style\n## Examples\n## Constraints")

shopt -s nullglob
failures=0
for file in "$CHATMODES_DIR"/*.md; do
  [[ -e "$file" ]] || continue
  missing=()
  for h in "${REQUIRED[@]}"; do
    if ! grep -qiE "^${h//\\/\\\\}" "$file"; then
      missing+=("$h")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    echo "[FAIL] $file is missing required sections:" >&2
    for m in "${missing[@]}"; do echo "  - $m" >&2; done
    ((failures++))
  else
    echo "[OK] $file"
  fi
done

if (( failures > 0 )); then
  echo "Chatmode validation failed ($failures file(s))." >&2
  exit 1
fi

echo "All chatmode files passed section checks."
