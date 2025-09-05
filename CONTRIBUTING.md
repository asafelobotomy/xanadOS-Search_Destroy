# Contributing

Thanks for contributing to **xanadOS Search & Destroy**! This repository contains a Linux security
application with AI-enhanced development tools.

## Before you start

### For Security Application Development

- Review security guidelines: `.github/instructions/security.instructions.md`
- Check implementation guide: `docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md`
- Understand security architecture: `docs/project/SECURITY_PERFORMANCE_REPORT.md`
- Install Python dependencies: `pip install -r requirements-dev.txt`

### For Development Tool Usage

- Read `.github/copilot-instructions.md` for AI development guidance
- Review available tools: `scripts/tools/README.md`
- Install Node.js dependencies: `npm install` (for validation tools)
- Follow quality guidelines: `.github/instructions/code-quality.instructions.md`

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

### AI Framework Setup

```bash
# Install Node.js dependencies (for development tools)
npm install

# Run validation tools
npm run quick:validate

# Use development tools
./scripts/tools/quality/check-quality.sh --fix
./scripts/tools/validation/validate-structure.sh
```

**Recent Improvements (v2.13.1)**:

- Fixed recurring "First Time Setup" dialog issue
- Enhanced setup wizard with auto-recovery logic
- Improved security with `run_secure()` in setup processes
- Added comprehensive validation and quality tools

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
