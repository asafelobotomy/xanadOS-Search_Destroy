#!/usr/bin/env bash
#
# validate-version-sync.sh - Ensure single source of truth for version
#
# Verifies that the version in pyproject.toml matches the root VERSION file.
# Prints a concise error and exits non-zero on mismatch.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

VERSION_FILE="${REPO_ROOT}/VERSION"
PYPROJECT_FILE="${REPO_ROOT}/pyproject.toml"

if [[ ! -f "${VERSION_FILE}" ]]; then
  echo "[version-sync] ERROR: VERSION file not found at ${VERSION_FILE}" >&2
  exit 2
fi

root_version="$(tr -d '\n' < "${VERSION_FILE}" | sed 's/^\s*//;s/\s*$//')"
if [[ -z "${root_version}" ]]; then
  echo "[version-sync] ERROR: VERSION file is empty" >&2
  exit 2
fi

if [[ ! -f "${PYPROJECT_FILE}" ]]; then
  echo "[version-sync] ERROR: pyproject.toml not found at ${PYPROJECT_FILE}" >&2
  exit 2
fi

py_version="$(grep -E '^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"' "${PYPROJECT_FILE}" | head -n1 | sed -E 's/^[^\"]*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/')"
if [[ -z "${py_version}" ]]; then
  echo "[version-sync] ERROR: Could not extract version from pyproject.toml" >&2
  exit 2
fi

if [[ "${py_version}" != "${root_version}" ]]; then
  echo "[version-sync] MISMATCH: VERSION=${root_version} vs pyproject.toml=${py_version}" >&2
  echo "[version-sync] Fix: update pyproject.toml [project].version to ${root_version} or edit VERSION accordingly." >&2
  exit 1
fi

echo "[version-sync] OK: ${root_version}"
