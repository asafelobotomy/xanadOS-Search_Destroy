---
applyTo: "**/*.py"
priority: 70
category: "language-specific"

---

# Python-specific Copilot Instructions

- Use `src/`+`tests/`layout with`pytest` where applicable.
- Prefer type hints (PEP 484) and run `mypy` if configured.
- Follow `ruff`/`flake8`/`black` if present; don’t reformat unrelated files.
- Place fixtures in `tests/conftest.py` when shared.
- Avoid network calls in tests; use `responses`or`pytest` monkeypatching.
- Use dataclasses or Pydantic for structured data.
- Prefer pathlib over os.path for file operations.
- Use context managers for resource management.
- Follow PEP 8 naming: snake_case for functions/variables, PascalCase for classes.
- Use `pytest` for all unit and integration tests.
- Use `ruff`for linting,`black`for formatting, and`mypy` for type checking.

## Error Handling

- Use exceptions for exceptional cases.
- Return Result types for expected failures.
- Log errors with structured logging.
