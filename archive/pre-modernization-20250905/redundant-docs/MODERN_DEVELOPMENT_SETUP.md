# Modern Development Environment Setup Guide

## Quick Start (Recommended)

### 1. Automatic Setup with Modern Tools

```bash
# One-command setup with modern package managers and tools
make setup

# Or run directly
chmod +x scripts/setup/modern-dev-setup.sh
./scripts/setup/modern-dev-setup.sh
```

### 2. Start Development

```bash
# Activate environment (automatic with direnv)
make dev

# Run application
make run

# Run tests
make test
```

## Modern Tools Integration

### Package Managers

- **uv**: 10-100x faster Python package management
- **pnpm**: 70% less disk space, 2-3x faster than npm
- **fnm**: 500x faster Node.js version management than nvm

### Environment Management

- **direnv**: Automatic environment activation when entering directory
- **Modern Makefile**: Comprehensive command shortcuts with colored output
- **Docker**: Containerized development environment

## Available Commands

### Core Development

```bash
make setup          # Modern setup with best practices
make dev            # Start development environment
make run            # Run the application
make test           # Run all tests
make validate       # Comprehensive validation
```

### Quality Assurance

```bash
make lint           # Run linting tools
make format         # Format code automatically
make type-check     # Run type checking
make audit          # Security audit
make pre-commit     # Run all pre-commit checks
```

### Docker Development

```bash
make docker-build   # Build Docker image
make docker-run     # Run in container
make docker-dev     # Development container

# Or use docker-compose
docker-compose up dev    # Full development environment
docker-compose up app    # Application only
```

### Maintenance

```bash
make clean          # Clean build artifacts
make update-deps    # Update all dependencies
make upgrade-tools  # Upgrade development tools
make check-env      # Check environment status
```

## Environment Files

### .envrc (direnv)

Automatically activates Python virtual environment and sets up development aliases
when you enter the directory.

### .nvmrc

Specifies Node.js version for consistent development across team members.

### Makefile.modern

Comprehensive build system with:

- Colored output and progress indicators
- Modern package manager detection
- Cross-platform compatibility
- Extensive help system

## Development Workflow

### 1. Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd xanadOS-Search_Destroy

# Setup development environment
make setup

# Allow direnv (automatic environment)
direnv allow
```

### 2. Daily Development

```bash
# Environment activates automatically with direnv
cd xanadOS-Search_Destroy

# Start coding
make dev

# Run tests frequently
make test

# Format and lint before commits
make pre-commit
```

### 3. Before Commits

```bash
# Run comprehensive validation
make validate

# Format code
make format

# Check types and security
make type-check
make audit
```

## Performance Features

### Modern Package Managers

- **uv sync**: Installs Python packages 10-100x faster
- **pnpm install**: Uses hard links, saves 70% disk space
- **fnm use**: Switches Node.js versions in milliseconds

### Caching

- Docker multi-stage builds with layer caching
- pnpm stores packages globally with hard links
- uv caches compiled wheels

### Parallel Operations

- Make supports parallel execution
- Docker builds use BuildKit for parallelization
- Modern tools use all CPU cores by default

## Security Features

### Automated Security

- ClamAV virus scanning with updated databases
- RKHunter rootkit detection
- Bandit Python security analysis
- Safety vulnerability checking
- npm/pnpm audit for JavaScript dependencies

### Container Security

- Non-root user in Docker containers
- Multi-stage builds minimize attack surface
- Health checks for container monitoring
- Security scanning in CI/CD pipeline

## IDE Integration

### VS Code

```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
```

### PyCharm

- Configure Python interpreter to use .venv/bin/python
- Enable type checking with mypy
- Configure code formatter to use black/ruff

## Troubleshooting

### Common Issues

#### Virtual Environment Not Found

```bash
# Recreate virtual environment
make clean-env
make setup
```

#### Node.js Version Issues

```bash
# Reset Node.js version
fnm install lts-latest
fnm use lts-latest
```

#### Permission Issues

```bash
# Fix file permissions
chmod +x scripts/setup/*.sh
chmod +x scripts/tools/**/*.sh
```

#### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up dev
```

### Performance Issues

#### Slow Package Installation

```bash
# Ensure modern package managers are used
make upgrade-tools
```

#### Slow Tests

```bash
# Run tests in parallel
pytest -n auto tests/
```

## Advanced Features

### Nix Development Environment

```bash
# For reproducible builds across all systems
make nix-setup
```

### Performance Profiling

```bash
# Profile application performance
make perf-profile
```

### DevContainer Support

```bash
# VS Code DevContainer setup
make devcontainer
```

## Migration from Legacy Setup

### From Old Setup Script

1. Run `make clean-env` to remove old environment
2. Run `make setup` for modern setup
3. Update your workflow to use `make` commands

### Benefits of Migration

- 10-100x faster package installation
- Automatic environment activation
- Comprehensive command shortcuts
- Modern security scanning
- Docker development support

## Contributing

### Code Style

- Python: Black + Ruff formatting, mypy type checking
- JavaScript: Prettier formatting, ESLint linting
- Shell: ShellCheck validation

### Testing

- Python: pytest with coverage reporting
- JavaScript: Jest or Vitest
- Integration: Docker-based testing

### Documentation

- Markdown with markdownlint
- API documentation with Sphinx
- README updates for new features

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [pnpm Documentation](https://pnpm.io/)
- [fnm Documentation](https://github.com/Schniz/fnm)
- [direnv Documentation](https://direnv.net/)
- [Make Documentation](https://www.gnu.org/software/make/manual/)

---

**Need Help?** Run `make help` for a quick command reference or `make info` for environment status.
