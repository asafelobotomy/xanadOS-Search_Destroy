#!/bin/bash
# Tool: install-optional-python.sh
# Purpose: Install optional Python packages for enhanced features (user scope by default)
# Usage: ./scripts/tools/setup/install-optional-python.sh [--group monitoring|gui|all] [--system] [--dry-run] [--verbose]

set -euo pipefail

GROUP="all"
SYSTEM=false
DRY_RUN=false
VERBOSE=false

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log_info(){ echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok(){ echo -e "${GREEN}[OK]${NC} $1"; }
log_warn(){ echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err(){ echo -e "${RED}[ERR]${NC} $1" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --group)
      GROUP="$2"; shift 2;;
    --system)
      SYSTEM=true; shift;;
    --dry-run|-n)
      DRY_RUN=true; shift;;
    --verbose|-v)
      VERBOSE=true; shift;;
    --help|-h)
      cat << EOF
Usage: $0 [options]

Options:
  --group NAME   monitoring|gui|all (default: all)
  --system       Use system install (may require sudo); default is user install
  --dry-run      Show commands without executing
  --verbose      Verbose pip output
  -h, --help     Show this help

Installs optional packages:
  monitoring: schedule watchdog inotify
  gui:        PyQt6 (if missing)
EOF
      exit 0;;
    *) log_err "Unknown option: $1"; exit 1;;
  esac
done

PY=python3
if command -v "$PY" >/dev/null 2>&1; then :; else PY=python; fi

pkgs_mon=(schedule watchdog inotify)
pkgs_gui=(PyQt6)

case "$GROUP" in
  monitoring) pkgs=("${pkgs_mon[@]}");;
  gui) pkgs=("${pkgs_gui[@]}");;
  all) pkgs=("${pkgs_mon[@]}" "${pkgs_gui[@]}");;
  *) log_err "Invalid group: $GROUP"; exit 1;;
esac

install_one(){
  local p="$1"
  if "$PY" - <<PYCODE >/dev/null 2>&1; then :; fi
import importlib, sys
sys.exit(0 if importlib.util.find_spec("$p") else 1)
PYCODE
  if [[ $? -eq 0 ]]; then
    log_ok "$p already installed"
    return 0
  fi
  local args=("-m" "pip" "install")
  "$SYSTEM" || args+=("--user")
  "$VERBOSE" || args+=("-q")
  args+=("$p")
  if "$DRY_RUN"; then
    log_info "DRY-RUN: $PY ${args[*]}"
  else
    log_info "Installing $p..."
    if "$PY" "${args[@]}"; then log_ok "$p installed"; else log_err "Failed to install $p"; fi
  fi
}

for p in "${pkgs[@]}"; do
  install_one "$p"
done

log_ok "Optional Python dependencies processed"
