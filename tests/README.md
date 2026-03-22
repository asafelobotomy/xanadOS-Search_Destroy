# Tests Directory
This directory contains the active automated test suite for xanadOS Search & Destroy.

Top-level test modules cover cross-cutting features that do not fit a dedicated subpackage yet.

## Running Tests

Use the repository standard commands from the project root.

## Structure
- security/: security-focused regression tests
- test_api/: API-facing tests
- test_core/: core engine and automation tests
- test_gui/: dashboard and GUI-focused tests
- test_reporting/: reporting module tests
uv run pytest
uv run pytest tests/test_core/
uv run pytest tests/test_reporting/
uv run pytest tests/test_api/test_ml_inference.py
```

## Notes

- Keep manual demos, ad hoc validation scripts, and generated test outputs out of tests/.
- Prefer deterministic pytest modules over script-style runners.
- Add new tests near the code area they exercise.
