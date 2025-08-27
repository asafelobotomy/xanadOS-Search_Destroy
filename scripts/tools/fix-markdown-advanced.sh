#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
echo "[DEPRECATED] Use scripts/tools/quality/fix-markdown.sh instead."
echo "Forwarding arguments..."
exec "$ROOT/quality/fix-markdown.sh" "$@"
