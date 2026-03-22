---
name: Test Files
applyTo: "**/*.test.*,**/*.spec.*,**/tests/**,**/test/**,**/__tests__/**"
description: "Conventions for test and spec files — naming, structure, mocking, and the arrange/act/assert pattern"
---

# Test File Instructions

- Testing framework: pytest
- Run tests: `uv run pytest`
- Name test files to mirror the source file they cover (e.g. `core/scanner.py` → `tests/test_scanner.py`).
- Each test should have a clear arrange/act/assert structure.
- Prefer testing behaviour over implementation details — avoid asserting internal state.
- Mock external dependencies; do not mock the module under test.
- Use descriptive test names that explain the expected behaviour, not the method name.
- When fixing a bug, write a failing test first, then fix the code.
