# Makefile for S&D - Search & Destroy
# Industry Standards Implementation:
# - Proper variable definitions with :=
# - Consistent target organization
# - Error handling and dependency management
# - Silent/verbose operation support

# Configuration variables (use := for immediate expansion)
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Project configuration
PROJECT_NAME := xanadOS-Search_Destroy
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip

# Build configuration
BUILD_DIR := build-dir
FLATPAK_ID := org.xanados.SearchAndDestroy
FLATPAK_MANIFEST := packaging/flatpak/$(FLATPAK_ID).yml

# Directories
SRC_DIRS := app tests dev
DOCS_DIR := docs
SCRIPTS_DIR := scripts

# Tools configuration
BLACK_LINE_LENGTH := 100
FLAKE8_MAX_LINE_LENGTH := 100

# Make behavior
ifeq ($(V),1)
    Q :=
else
    Q := @
endif

# Declare all phony targets
.PHONY: all clean install build-flatpak install-flatpak run test clean-cache clean-all prepare verify \
        check-organization fix-organization install-hooks organize-legacy dev-setup check-style help \
        clean-dev clean-dev-force status update-deps lint format security-check type-check \
        run-flatpak full-install organize

# Default target (keep simple and informative)
all: help

# Build targets
build-flatpak: $(BUILD_DIR)
	$(Q)echo "📦 Building Flatpak package..."
	$(Q)flatpak-builder --force-clean $(BUILD_DIR) $(FLATPAK_MANIFEST)
	$(Q)echo "✅ Flatpak build complete"

$(BUILD_DIR):
	$(Q)mkdir -p $(BUILD_DIR)

# Preparation and verification targets
prepare:
	$(Q)echo "🔧 Running build preparation..."
	$(Q)$(SCRIPTS_DIR)/prepare-build.sh

verify:
	$(Q)echo "✅ Running build verification..."
	$(Q)$(SCRIPTS_DIR)/verify-build.sh

# Organization targets (NEW COMPREHENSIVE SYSTEM)
check-organization:
	$(Q)echo "🔍 Checking repository organization..."
	$(Q)python3 $(SCRIPTS_DIR)/check-organization.py

fix-organization:
	$(Q)echo "🔧 Fixing repository organization..."
	$(Q)python3 dev/organize_repository_comprehensive.py

install-hooks:
	$(Q)echo "🪝 Installing git hooks for organization..."
	$(Q)bash $(SCRIPTS_DIR)/install-hooks.sh

# Legacy organization (DEPRECATED - use fix-organization instead)
organize-legacy:
	$(Q)echo "⚠️  WARNING: This is the legacy organize target"
	$(Q)echo "⚠️  Use 'make fix-organization' for the new comprehensive system"
	$(Q)echo "Organizing project structure..."
	$(Q)mkdir -p dev/demos dev/test-scripts
	$(Q)find . -maxdepth 1 -name "demo_*.py" -exec mv {} dev/demos/ \; 2>/dev/null || true
	$(Q)find . -maxdepth 1 -name "test_*.py" -exec mv {} dev/test-scripts/ \; 2>/dev/null || true
	$(Q)echo "Project structure organized!"

# For backward compatibility (points to new system)
organize: fix-organization

# Clean targets with proper dependency handling
clean:
	$(Q)echo "🧹 Cleaning build artifacts..."
	$(Q)rm -rf $(BUILD_DIR) .flatpak-builder
	$(Q)rm -rf dist/ build/ *.egg-info/
	$(Q)echo "✅ Build artifacts cleaned"

clean-cache:
	$(Q)echo "🧹 Cleaning Python cache files..."
	$(Q)find $(SRC_DIRS) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	$(Q)find . -name "*.pyc" -delete 2>/dev/null || true
	$(Q)find . -name "*.pyo" -delete 2>/dev/null || true
	$(Q)find . -name "*.pyd" -delete 2>/dev/null || true
	$(Q)find . -name "*.so" -delete 2>/dev/null || true
	$(Q)find . -name ".coverage" -delete 2>/dev/null || true
	$(Q)find . -name "*.log" -delete 2>/dev/null || true
	$(Q)echo "✅ Python cache cleaned"

# Clean everything with proper dependencies
clean-all: clean clean-cache

# Clean development files (safe information)
clean-dev:
	$(Q)echo "Development files are organized in dev/ directory"
	$(Q)echo "Use 'make clean-dev-force' to remove dev/ directory entirely"

# Force clean development files (WARNING: removes dev/ directory)
clean-dev-force:
	$(Q)echo "⚠️  WARNING: This will remove the entire dev/ directory!"
	$(Q)echo "⚠️  This includes all test scripts and development tools!"
	$(Q)read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf dev/; \
		echo "🗑️  dev/ directory removed"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

# Error handling target
.DELETE_ON_ERROR:

# Pattern rules for debugging
debug-%: 
	$(Q)echo "Debug info for $*:"
	$(Q)echo "PROJECT_NAME = $(PROJECT_NAME)"
	$(Q)echo "VENV_DIR = $(VENV_DIR)"
	$(Q)echo "BUILD_DIR = $(BUILD_DIR)"
	$(Q)echo "SRC_DIRS = $(SRC_DIRS)"

# Development environment setup with proper dependencies
$(VENV_DIR):
	$(Q)echo "📦 Creating Python virtual environment..."
	$(Q)python3 -m venv $(VENV_DIR)
	$(Q)$(PIP) install --upgrade pip

install: $(VENV_DIR)
	$(Q)echo "📥 Installing dependencies..."
	$(Q)$(PIP) install -r requirements.txt
	$(Q)echo "✅ Installation complete"

dev-setup: install
	$(Q)echo "🛠️ Setting up development environment..."
	$(Q)$(PIP) install pytest pycodestyle black flake8 mypy bandit safety
	$(Q)echo "🪝 Installing git hooks..."
	$(Q)bash $(SCRIPTS_DIR)/install-hooks.sh
	$(Q)echo "✅ Development environment ready"

update-deps: $(VENV_DIR)
	$(Q)echo "🔄 Updating dependencies..."
	$(Q)$(PIP) install --upgrade pip
	$(Q)$(PIP) install --upgrade -r requirements.txt
	$(Q)echo "✅ Dependencies updated"

# Flatpak targets with dependencies
install-flatpak: build-flatpak
	$(Q)echo "📥 Installing Flatpak locally..."
	$(Q)flatpak install --user --reinstall $(BUILD_DIR) $(FLATPAK_ID)
	$(Q)echo "✅ Flatpak installed"

# Build and install everything
full-install: clean-all build-flatpak install-flatpak

# Runtime targets
run:
	$(Q)echo "🚀 Running application..."
	$(Q)./run.sh

run-flatpak:
	$(Q)echo "🚀 Running Flatpak version..."
	$(Q)flatpak run $(FLATPAK_ID)

# Quality assurance targets with proper dependencies
test: clean-cache | $(VENV_DIR)
	$(Q)echo "🧪 Running tests..."
	$(Q)if [ -f $(VENV_DIR)/bin/activate ]; then \
		source $(VENV_DIR)/bin/activate && python -m pytest tests/ -v; \
	else \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi

check-style: clean-cache | $(VENV_DIR)
	$(Q)echo "🎨 Checking code style..."
	$(Q)if [ -f $(VENV_DIR)/bin/activate ]; then \
		source $(VENV_DIR)/bin/activate && pycodestyle app/ --max-line-length=$(FLAKE8_MAX_LINE_LENGTH); \
	else \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi

format: | $(VENV_DIR)
	$(Q)echo "🎨 Formatting code with black..."
	$(Q)if [ -f $(VENV_DIR)/bin/activate ]; then \
		source $(VENV_DIR)/bin/activate && black $(SRC_DIRS) --line-length=$(BLACK_LINE_LENGTH); \
	else \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi

lint: | $(VENV_DIR)
	$(Q)echo "🔍 Linting code..."
	$(Q)if [ -f $(VENV_DIR)/bin/activate ]; then \
		source $(VENV_DIR)/bin/activate && flake8 app/ --max-line-length=$(FLAKE8_MAX_LINE_LENGTH); \
	else \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi

type-check: | $(VENV_DIR)
	$(Q)echo "🔍 Type checking..."
	$(Q)if [ -f $(VENV_DIR)/bin/activate ]; then \
		source $(VENV_DIR)/bin/activate && mypy app/ --ignore-missing-imports; \
	else \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi

security-check: | $(VENV_DIR)
	$(Q)echo "🔒 Checking for security issues..."
	$(Q)if [ -f $(VENV_DIR)/bin/activate ]; then \
		source $(VENV_DIR)/bin/activate && bandit -r app/ -f json -o security-report.json || true; \
		source $(VENV_DIR)/bin/activate && safety check; \
	else \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first."; \
		exit 1; \
	fi

# Comprehensive quality check
quality: test lint type-check security-check check-style
	$(Q)echo "✅ All quality checks passed"

# Development status with enhanced checks
status:
	$(Q)echo "📊 Repository Status"
	$(Q)echo "==================="
	$(Q)echo ""
	$(Q)echo "🔍 Organization Status:"
	$(Q)python3 $(SCRIPTS_DIR)/check-organization.py 2>/dev/null || echo "❌ Organization check failed"
	$(Q)echo ""
	$(Q)echo "📁 Directory Structure:"
	$(Q)echo "  app/: $$(find app -name '*.py' 2>/dev/null | wc -l) Python files"
	$(Q)echo "  tests/: $$(find tests -name '*.py' 2>/dev/null | wc -l) test files"
	$(Q)echo "  dev/: $$(find dev -name '*.py' 2>/dev/null | wc -l) development files"
	$(Q)echo "  docs/: $$(find docs -name '*.md' 2>/dev/null | wc -l) documentation files"
	$(Q)echo ""
	$(Q)echo "🔧 Development Environment:"
	$(Q)if [ -d $(VENV_DIR) ]; then echo "  ✅ Virtual environment exists"; else echo "  ❌ Virtual environment missing (run 'make dev-setup')"; fi
	$(Q)if [ -f .git/hooks/pre-commit ]; then echo "  ✅ Git hooks installed"; else echo "  ❌ Git hooks missing (run 'make install-hooks')"; fi
	$(Q)echo ""
	$(Q)echo "📦 Build Artifacts:"
	$(Q)if [ -d $(BUILD_DIR) ]; then echo "  📁 Flatpak build directory exists"; else echo "  📁 No Flatpak build directory"; fi
	$(Q)if [ -d .flatpak-builder ]; then echo "  📁 Flatpak builder cache exists"; else echo "  📁 No Flatpak builder cache"; fi

# Help system with better organization
help:
	$(Q)echo "📋 $(PROJECT_NAME) - Makefile Targets"
	$(Q)echo "====================================="
	$(Q)echo ""
	$(Q)echo "🏗️  BUILD TARGETS:"
	$(Q)echo "  build-flatpak      - Build Flatpak package"
	$(Q)echo "  install-flatpak    - Install Flatpak locally"
	$(Q)echo "  full-install       - Build and install Flatpak"
	$(Q)echo ""
	$(Q)echo "🛠️  DEVELOPMENT TARGETS:"
	$(Q)echo "  dev-setup          - Setup complete development environment"
	$(Q)echo "  install            - Install Python dependencies only"
	$(Q)echo "  update-deps        - Update Python dependencies"
	$(Q)echo "  status             - Show repository and environment status"
	$(Q)echo ""
	$(Q)echo "🧹 CLEANING TARGETS:"
	$(Q)echo "  clean              - Clean build artifacts"
	$(Q)echo "  clean-cache        - Clean Python cache files"
	$(Q)echo "  clean-dev          - Info about development file cleanup"
	$(Q)echo "  clean-dev-force    - Remove dev/ directory (WARNING: destructive)"
	$(Q)echo "  clean-all          - Clean everything (build + cache)"
	$(Q)echo ""
	$(Q)echo "🔍 QUALITY TARGETS:"
	$(Q)echo "  test               - Run tests"
	$(Q)echo "  check-style        - Check code style (pycodestyle)"
	$(Q)echo "  format             - Format code with black"
	$(Q)echo "  lint               - Lint code with flake8"
	$(Q)echo "  type-check         - Type checking with mypy"
	$(Q)echo "  security-check     - Security analysis with bandit & safety"
	$(Q)echo "  quality            - Run all quality checks"
	$(Q)echo ""
	$(Q)echo "📁 ORGANIZATION TARGETS:"
	$(Q)echo "  check-organization - Check repository organization"
	$(Q)echo "  fix-organization   - Fix repository organization issues"
	$(Q)echo "  install-hooks      - Install git hooks for organization"
	$(Q)echo "  organize           - Fix organization (same as fix-organization)"
	$(Q)echo ""
	$(Q)echo "🚀 RUN TARGETS:"
	$(Q)echo "  run                - Run application (traditional)"
	$(Q)echo "  run-flatpak        - Run Flatpak version"
	$(Q)echo ""
	$(Q)echo "🔧 UTILITY TARGETS:"
	$(Q)echo "  prepare            - Run build preparation script"
	$(Q)echo "  verify             - Run build verification script"
	$(Q)echo "  help               - Show this help"
	$(Q)echo "  debug-<var>        - Show debug info for variable"
	$(Q)echo ""
	$(Q)echo "💡 QUICK START:"
	$(Q)echo "  make dev-setup     # Set up development environment"
	$(Q)echo "  make test          # Run tests"
	$(Q)echo "  make quality       # Run all quality checks"
	$(Q)echo "  make build-flatpak # Build application"
	$(Q)echo ""
	$(Q)echo "🔧 CONFIGURATION:"
	$(Q)echo "  V=1                # Verbose output (make V=1 target)"
	$(Q)echo "  BLACK_LINE_LENGTH  # Black formatter line length (default: $(BLACK_LINE_LENGTH))"
	$(Q)echo "  FLAKE8_MAX_LINE_LENGTH # Flake8 max line length (default: $(FLAKE8_MAX_LINE_LENGTH))"
