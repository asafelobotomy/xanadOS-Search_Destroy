#!/bin/bash
# Import Fix Script for xanadOS-Search_Destroy (safe mode)
# Converts explicit package-relative imports to absolute `app.*` imports.

set -euo pipefail

DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -h|--help)
            cat <<EOF
Usage: $0 [--dry-run] [--verbose]

Safely rewrites top-level imports:
    from core.*       -> from app.core.*
    from gui.*        -> from app.gui.*
    from utils.*      -> from app.utils.*
    from monitoring.* -> from app.monitoring.*

Notes:
    - Anchored to the beginning of the line, preserves leading whitespace.
    - Skips already-correct imports (no-op if already has app.).
    - Creates a timestamped backup copy of modified files (unless --dry-run).
EOF
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="backups/import-fix-${TS}"

echo "� Running import fix (dry-run=$DRY_RUN, verbose=$VERBOSE)"

mapfile -d '' PY_FILES < <(find app/ -type f -name "*.py" -print0)

modified_count=0
for f in "${PY_FILES[@]}"; do
    # Build a sed script with anchored patterns; preserve leading indentation
    SED_SCRIPT=$'s/^([[:space:]]*)from[[:space:]]+core\./\1from app.core./;'
    SED_SCRIPT+=$' s/^([[:space:]]*)from[[:space:]]+gui\./\1from app.gui./;'
    SED_SCRIPT+=$' s/^([[:space:]]*)from[[:space:]]+utils\./\1from app.utils./;'
    SED_SCRIPT+=$' s/^([[:space:]]*)from[[:space:]]+monitoring\./\1from app.monitoring./;'

    # Use perl for extended regex with capture groups portability
    if perl -0777 -pe "${SED_SCRIPT//$/\n}" <"$f" | cmp -s - "$f"; then
        $VERBOSE && echo "  = ${f} (no changes)"
        continue
    fi

    echo "  * ${f}"
    modified_count=$((modified_count+1))

    if [[ "$DRY_RUN" == "true" ]]; then
        continue
    fi

    mkdir -p "$BACKUP_DIR/$(dirname "${f#app/}")"
    cp "$f" "$BACKUP_DIR/${f#./}"

    # Apply changes
    perl -0777 -pe "${SED_SCRIPT//$/\n}" -i "$f"
done

echo "✅ Import scan complete. Files modified: $modified_count"

echo "🧪 Import smoke tests..."
if python3 -c "from app.main import main" 2>/dev/null; then
    echo "  ✓ app.main import OK"
else
    echo "  ✗ app.main import failed" >&2
fi

if python3 -c "from app.gui.main_window import MainWindow" 2>/dev/null; then
    echo "  ✓ app.gui.main_window import OK"
else
    echo "  ✗ app.gui.main_window import failed (may be expected if GUI deps missing)"
fi

if [[ "$DRY_RUN" == "false" ]] && [[ $modified_count -gt 0 ]]; then
    echo "📦 Backups: $BACKUP_DIR"
fi
