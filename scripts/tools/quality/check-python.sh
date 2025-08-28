#!/usr/bin/env bash

# Tool: check-python.sh
# Purpose: Non-destructive Python validation (lint/format/type/tests optional)
# Usage:
#   ./check-python.sh                # run ruff/black/flake8 if available
#   ./check-python.sh --strict       # also run mypy and pytest -q
#   ./check-python.sh --no-black     # skip black --check
#   ./check-python.sh --no-ruff      # skip ruff checks
# Exit codes: 0 pass, 1 failures found, 2 setup error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

STRICT=false
RUN_BLACK=true
RUN_RUFF=true
RUN_FLAKE8=true
RUN_MYPY=false
RUN_PYTEST=false

for arg in "$@"; do
  case "$arg" in
    --strict)
      STRICT=true
      RUN_MYPY=true
      RUN_PYTEST=true
      shift || true
      ;;
    --no-black)
      RUN_BLACK=false
      shift || true
      ;;
    --no-ruff)
      RUN_RUFF=false
      shift || true
      ;;
    --no-flake8)
      RUN_FLAKE8=false
      shift || true
      ;;
  esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

failures=0

info() { echo -e "${YELLOW}[PY]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
err() { echo -e "${RED}[FAIL]${NC} $*"; failures=$((failures+1)); }

# Detect tools
has() { command -v "$1" >/dev/null 2>&1; }

PY_MSG_PREFIX="Python validation"

info "Starting $PY_MSG_PREFIX (strict=$STRICT)"

# In strict mode, skip Ruff to focus on mypy/pytest; Ruff runs in quick validations
if $STRICT; then
  RUN_RUFF=false
  RUFF_TARGETS=(".")
else
  RUFF_TARGETS=(".")
fi

# Ruff checks
if $RUN_RUFF; then
  if has ruff; then
    if ruff check --quiet "${RUFF_TARGETS[@]}"; then
      ok "ruff check passed"
    else
      err "ruff check found issues"
    fi
    # Format verification (non-destructive)
    if ! $STRICT; then
      if ruff format --check "${RUFF_TARGETS[@]}"; then
        ok "ruff format check passed"
      else
        err "ruff format check failed (run: ruff format)"
      fi
    else
      info "skipping ruff format check in strict mode (use non-strict to verify formatting)"
    fi
  else
    info "ruff not found; skipping"
  fi
fi

# Black check (optional alongside ruff)
if $RUN_BLACK; then
  if has black; then
    if black --check .; then
      ok "black --check passed"
    else
      err "black check failed (run: black .)"
    fi
  else
    info "black not found; skipping"
  fi
fi

# Flake8 (legacy guard; uses config from pyproject)
if $RUN_FLAKE8; then
  if has flake8; then
    if flake8 .; then
      ok "flake8 passed"
    else
      err "flake8 reported issues"
    fi
  else
    info "flake8 not found; skipping"
  fi
fi

# mypy type checking (strict mode only by default)
if $RUN_MYPY; then
  if has mypy; then
    # Capture output to handle the "no files" case gracefully
    MYPY_OUTPUT="$(mypy . 2>&1 || true)"
    if echo "$MYPY_OUTPUT" | grep -qi "There are no .py\[i\] files"; then
      ok "mypy skipped (no Python files matched config)"
    elif echo "$MYPY_OUTPUT" | grep -q '^Success:'; then
      ok "mypy passed"
    elif [ -z "$MYPY_OUTPUT" ]; then
      ok "mypy passed"
    else
      echo "$MYPY_OUTPUT"
      err "mypy reported type issues"
    fi
  else
    info "mypy not found; skipping"
  fi
fi

# pytest quick run (quiet, if tests directory exists)
if $RUN_PYTEST && [ -d "$REPO_ROOT/tests" ]; then
  if has pytest; then
    if pytest -q; then
      ok "pytest passed"
    else
      err "pytest failed"
    fi
  else
    info "pytest not found; skipping"
  fi
fi

if [ "$failures" -eq 0 ]; then
  ok "$PY_MSG_PREFIX passed"
  exit 0
else
  err "$PY_MSG_PREFIX found $failures issue(s)"
  exit 1
fi
