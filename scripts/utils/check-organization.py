#!/usr/bin/env python3
"""Deprecated duplicate of scripts/check-organization.py.

Kept for backwards compatibility with older docs or scripts.
This shim imports and delegates to the canonical checker to avoid mypy duplicate module errors.
"""
from pathlib import Path
import sys

# Add repo root to sys.path to import the canonical checker
_this_file = Path(__file__).resolve()
_repo_root = _this_file.parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from scripts.check_organization import check_organization  # type: ignore  # noqa: E402


if __name__ == "__main__":
    sys.exit(0 if check_organization() else 1)
