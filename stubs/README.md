# Type stubs for xanadOS Search & Destroy
# PEP 561 compliant type stubs for third-party packages

This directory contains type stub files (.pyi) for third-party packages that lack
complete type annotations. These stubs improve IDE autocomplete and mypy validation.

## Structure

```
stubs/
├── plotly-stubs/       # Type stubs for plotly
│   └── __init__.pyi
├── weasyprint-stubs/   # Type stubs for weasyprint
│   └── __init__.pyi
├── openpyxl-stubs/     # Type stubs for openpyxl
│   └── __init__.pyi
└── README.md           # This file
```

## Usage

These stubs are automatically discovered by mypy when running:
```bash
mypy app/ --config-file=config/mypy.ini
```

## Creating New Stubs

To create stubs for a new package:

1. Create a new directory: `{package}-stubs/`
2. Add `__init__.pyi` with type annotations
3. Follow PEP 561 conventions
4. Add to `pyproject.toml` under `[tool.mypy]`:
   ```toml
   mypy_path = "stubs"
   ```

## References

- [PEP 561 - Distributing and Packaging Type Information](https://peps.python.org/pep-0561/)
- [mypy documentation on stubs](https://mypy.readthedocs.io/en/stable/stubs.html)
