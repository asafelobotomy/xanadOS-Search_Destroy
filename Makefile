# Makefile for S&D - Search & Destroy

.PHONY: all clean install build-flatpak install-flatpak run test clean-cache clean-all prepare verify

# Default target
all: build-flatpak

# Preparation and verification targets
prepare:
	./scripts/prepare-build.sh

verify:
	./scripts/verify-build.sh

# Clean build artifacts
clean:
	rm -rf build-dir .flatpak-builder

# Clean Python cache files
clean-cache:
	find ./app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find ./tests -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true

# Clean development files
clean-dev:
	@echo "Development files are organized in dev/ directory"
	@echo "Use 'make clean-dev-force' to remove dev/ directory entirely"

# Force clean development files (WARNING: removes dev/ directory)
clean-dev-force:
	rm -rf dev/

# Organize project structure
organize:
	@echo "Organizing project structure..."
	@mkdir -p dev/demos dev/test-scripts
	@find . -maxdepth 1 -name "demo_*.py" -exec mv {} dev/demos/ \; 2>/dev/null || true
	@find . -maxdepth 1 -name "test_*.py" -exec mv {} dev/test-scripts/ \; 2>/dev/null || true
	@echo "Project structure organized!"

# Clean everything (build + cache + temp files)
clean-all: clean clean-cache

# Traditional installation (with virtual environment)
install:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Build Flatpak
build-flatpak:
	flatpak-builder --force-clean build-dir packaging/flatpak/org.xanados.SearchAndDestroy.yml

# Install Flatpak locally
install-flatpak: build-flatpak
	flatpak install --user --reinstall build-dir org.xanados.SearchAndDestroy

# Run the application (traditional - requires proper module structure)
run:
	./run.sh

# Run the Flatpak version
run-flatpak:
	flatpak run org.xanados.SearchAndDestroy

# Test the application
test: clean-cache
	source .venv/bin/activate && python -m pytest tests/ -v

# Build and install everything
full-install: clean-all build-flatpak install-flatpak

# Development setup
dev-setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install pytest pycodestyle

# Code style check
check-style: clean-cache
	source .venv/bin/activate && pycodestyle app/

# Help
help:
	@echo "Available targets:"
	@echo "  all           - Build Flatpak (default)"
	@echo "  prepare       - Run build preparation script"
	@echo "  verify        - Run build verification script"
	@echo "  clean         - Clean build artifacts"
	@echo "  clean-cache   - Clean Python cache files"
	@echo "  clean-dev     - Info about development file cleanup"
	@echo "  clean-dev-force - Remove dev/ directory (WARNING: destructive)"
	@echo "  clean-all     - Clean everything (build + cache)"
	@echo "  organize      - Organize project structure"
	@echo "  install       - Install Python dependencies"
	@echo "  build-flatpak - Build Flatpak package"
	@echo "  install-flatpak - Install Flatpak locally"
	@echo "  run           - Run application (traditional)"
	@echo "  run-flatpak   - Run Flatpak version"
	@echo "  test          - Run tests"
	@echo "  full-install  - Build and install Flatpak"
	@echo "  dev-setup     - Setup development environment"
	@echo "  check-style   - Check code style"
	@echo "  help          - Show this help"
