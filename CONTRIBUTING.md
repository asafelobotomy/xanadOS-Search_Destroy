# Contributing

Thanks for contributing to **xanadOS Search & Destroy**! This repository contains a comprehensive
Linux security scanner and system protection suite.

## Before you start

- Review implementation guide: `docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md`
- Understand security architecture: `docs/project/SECURITY_PERFORMANCE_REPORT.md`
- Install Python dependencies: `pip install -e .[dev]`
- Review available tools: `scripts/tools/README.md`

## Workflow

### Security Application Changes

1. Create a feature branch for your security enhancement
2. Write or update tests in `tests/` matching `app/` structure
3. Follow Python security best practices (see `app/core/input_validation.py` examples)
4. Ensure `python -m pytest tests/` passes locally
5. Test with the GUI: `python -m app.main`
6. Update security documentation if needed

### General Guidelines

1. Make focused changes; avoid unrelated formatting
2. Write clear commit messages following conventional commits
3. Open a PR with concise description, assumptions, and tradeoffs
4. Update `CHANGELOG.md` for notable changes

## Development Environment

### Python Application Setup

```bash
# RECOMMENDED: Modern setup (includes all dependencies)
make setup

# OR: Manual Python dependency installation
pip install -e .[dev]

# Install system dependencies (Ubuntu/Debian)
sudo apt install clamav clamav-daemon

# Run tests
python -m pytest tests/

# Launch application
make run  # OR: python -m app.main
```

**Recent Improvements**:

- Comprehensive packaging system for RPM, DEB, and AUR distributions
- Enhanced scan display with real-time file size information
- Fixed ClamAV definition update issues with daemon detection
- Improved scan safety with concurrent scan prevention
- Type annotation modernization for Python 3.13+
- Real-time protection performance optimizations

## Notes

### Security Considerations

- All user inputs must be validated (see `app/core/input_validation.py`)
- Command execution must use safe methods (see `app/core/privilege_escalation.py`)
- Follow PolicyKit security patterns for privilege escalation
- Test security features thoroughly with edge cases

### Code Quality

- Prefer reusing existing functions and following established patterns
- Document public APIs with inputs/outputs and error modes
- Follow existing code style and security patterns
- Update type hints and docstrings for new code

### Documentation

- Update user documentation for new security features
- Update AI framework docs for new development tools
- Include examples and usage patterns
- Keep documentation current with code changes
