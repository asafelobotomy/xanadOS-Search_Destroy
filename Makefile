# Makefile for xanadOS Search & Destroy - 2025 Edition
# Modern Python security application with comprehensive development workflow

# === Configuration ===
PROJECT_NAME := xanadOS-Search-Destroy
VERSION := $(shell cat VERSION 2>/dev/null || echo "2.11.2")

# Environment Setup
PYTHON := python3
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Directory Structure
SRC_DIR := app
TEST_DIR := tests
DOCS_DIR := docs
TOOLS_DIR := scripts/tools

# Tool Detection
HAS_VENV := $(shell test -d $(VENV_DIR) && echo true || echo false)
HAS_UV := $(shell command -v uv >/dev/null 2>&1 && echo true || echo false)
HAS_NPM := $(shell command -v npm >/dev/null 2>&1 && echo true || echo false)

# Python Commands (auto-detect environment)
ifeq ($(HAS_VENV),true)
	PY := $(VENV_PYTHON)
	PIP := $(VENV_PIP)
else
	PY := $(PYTHON)
	PIP := $(PYTHON) -m pip
endif

# Colors for better UX
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
BOLD := \033[1m
NC := \033[0m

# === Main Targets ===
.PHONY: help setup install run test lint build clean status

help: ## 📖 Show this help message
	@echo "$(BOLD)$(BLUE)$(PROJECT_NAME) v$(VERSION)$(NC)"
	@echo "$(CYAN)Comprehensive development workflow for modern Python$(NC)"
	@echo ""
	@echo "$(BOLD)$(YELLOW)🚀 Quick Start:$(NC)"
	@echo "  $(GREEN)make setup$(NC)     - Complete development environment setup"
	@echo "  $(GREEN)make install$(NC)   - Install dependencies (basic/dev/advanced/all)"
	@echo "  $(GREEN)make run$(NC)       - Run the application"
	@echo "  $(GREEN)make test$(NC)      - Run comprehensive test suite"
	@echo "  $(GREEN)make build$(NC)     - Build distribution packages"
	@echo ""
	@echo "$(BOLD)$(YELLOW)🔧 Development:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🔧/ {gsub(/.*🔧 /, "", $$2); printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BOLD)$(YELLOW)🧪 Quality & Testing:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🧪/ {gsub(/.*🧪 /, "", $$2); printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BOLD)$(YELLOW)🔒 Security:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🔒/ {gsub(/.*🔒 /, "", $$2); printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BOLD)$(YELLOW)📊 Information:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*📊/ {gsub(/.*📊 /, "", $$2); printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BOLD)$(YELLOW)⚡ Modernization:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*⚡/ {gsub(/.*⚡ /, "", $$2); printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# === Environment Setup ===
setup: ## 🔧 Complete development environment setup (UV-based)
	@echo "$(BOLD)$(BLUE)🔧 Setting up development environment...$(NC)"
	@$(MAKE) _install-uv-if-needed
	@$(MAKE) _create-venv
	@$(MAKE) install-dev
	@$(MAKE) validate-deps
	@echo "$(GREEN)✅ Development environment ready!$(NC)"
	@echo "$(CYAN)💡 Next: make run (to start app) or make test (to run tests)$(NC)"

setup-standard: ## 🔧 Standard Python venv setup (no UV)
	@echo "$(BLUE)Setting up standard Python environment...$(NC)"
	@$(MAKE) _create-venv-standard
	@$(MAKE) install-dev
	@echo "$(GREEN)✅ Standard environment ready!$(NC)"

# === Installation Targets ===
install: ## 🔧 Install runtime dependencies only
	@echo "$(BLUE)Installing runtime dependencies...$(NC)"
	@$(MAKE) _ensure-venv
	@if [ "$(HAS_UV)" = "true" ]; then \
		echo "$(CYAN)Using UV for fast dependency installation...$(NC)"; \
		uv pip install -e .; \
	else \
		$(PIP) install --use-pep517 -e .; \
	fi
	@echo "$(GREEN)✅ Runtime dependencies installed$(NC)"
	@echo "$(CYAN)💡 Includes: numpy, schedule, aiohttp, inotify for core functionality$(NC)"

install-dev: ## 🔧 Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@$(MAKE) _ensure-venv
	@if [ "$(HAS_UV)" = "true" ]; then \
		echo "$(CYAN)Using UV for fast dependency installation...$(NC)"; \
		uv pip install -e ".[dev]"; \
	else \
		$(PIP) install --use-pep517 -e ".[dev]"; \
	fi
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

install-advanced: ## 🔧 Install advanced features (pandas, ML, analytics, cloud)
	@echo "$(BOLD)$(BLUE)Installing advanced features...$(NC)"
	@$(MAKE) _ensure-venv
	@if [ "$(HAS_UV)" = "true" ]; then \
		uv pip install -e ".[advanced]"; \
	else \
		$(PIP) install --use-pep517 -e ".[advanced]"; \
	fi
	@echo "$(GREEN)✅ Advanced features available:$(NC)"
	@echo "  - Data Analytics (pandas), ML (scikit-learn), Cloud (boto3)"

install-all: ## 🔧 Install all dependencies (complete feature set)
	@echo "$(BOLD)$(BLUE)Installing complete feature set...$(NC)"
	@$(MAKE) _ensure-venv
	@if [ "$(HAS_UV)" = "true" ]; then \
		uv pip install -e ".[dev,advanced,security,malware-analysis]"; \
	else \
		$(PIP) install --use-pep517 -e ".[dev,advanced,security,malware-analysis]"; \
	fi
	@echo "$(GREEN)✅ All features installed$(NC)"

# Add a new target for dependency validation
validate-deps: ## 🧪 Validate all critical dependencies are working
	@echo "$(BLUE)Validating critical dependencies...$(NC)"
	@$(MAKE) _ensure-venv
	@./scripts/setup/ensure-deps.sh --validate-only || { \
		echo "$(YELLOW)Dependencies not fully validated. Run './scripts/setup/ensure-deps.sh' to fix.$(NC)"; \
		exit 1; \
	}

# === Application Execution ===
run: ## 🚀 Run the application
	@echo "$(BOLD)$(BLUE)Starting $(PROJECT_NAME)...$(NC)"
	@$(MAKE) _ensure-venv
	$(PY) -m app.main

run-debug: ## 🔧 Run with debug logging enabled
	@echo "$(BLUE)Starting with debug logging...$(NC)"
	@$(MAKE) _ensure-venv
	DEBUG=1 PYTHONPATH=. $(PY) -m app.main

run-console: ## 🔧 Run in console mode (no GUI)
	@echo "$(BLUE)Starting in console mode...$(NC)"
	@$(MAKE) _ensure-venv
	CONSOLE_MODE=1 $(PY) -m app.main

# === Testing & Quality ===
test: ## 🧪 Run comprehensive test suite
	@echo "$(BOLD)$(BLUE)Running comprehensive test suite...$(NC)"
	@$(MAKE) _ensure-venv
	$(PY) -m pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-quick: ## 🧪 Quick smoke tests
	@echo "$(BLUE)Running quick tests...$(NC)"
	@$(MAKE) _ensure-venv
	$(PY) -m pytest $(TEST_DIR)/ -x --tb=line -q

test-gui: ## 🧪 GUI-specific tests
	@echo "$(BLUE)Running GUI tests...$(NC)"
	@$(MAKE) _ensure-venv
	$(PY) -m pytest $(TEST_DIR)/test_gui.py -v

lint: ## 🧪 Complete code quality check (ruff + type + security)
	@echo "$(BOLD)$(BLUE)Running comprehensive code quality checks...$(NC)"
	@$(MAKE) _ensure-venv
	@echo "$(CYAN)🔍 Ruff linting...$(NC)"
	@$(PY) -m ruff check $(SRC_DIR) $(TEST_DIR) --fix || true
	@echo "$(CYAN)🎨 Code formatting...$(NC)"
	@$(PY) -m ruff format $(SRC_DIR) $(TEST_DIR)
	@echo "$(CYAN)🔍 Type checking...$(NC)"
	@$(PY) -m mypy $(SRC_DIR) --ignore-missing-imports || true
	@echo "$(CYAN)🔒 Security scan...$(NC)"
	@$(PY) -m bandit -r $(SRC_DIR) -f json -o security-report.json || true
	@echo "$(GREEN)✅ Code quality check complete$(NC)"

format: ## 🧪 Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(MAKE) _ensure-venv
	$(PY) -m ruff format $(SRC_DIR) $(TEST_DIR)
	$(PY) -m ruff check $(SRC_DIR) $(TEST_DIR) --fix

# === Security & Analysis ===
security: ## 🔒 Comprehensive security analysis
	@echo "$(BOLD)$(BLUE)Running security analysis...$(NC)"
	@$(MAKE) _ensure-venv
	@echo "$(CYAN)🔍 Dependency vulnerabilities...$(NC)"
	@$(PY) -m pip_audit --format=json --output=security-report.json || true
	@echo "$(CYAN)🔍 Code security scan...$(NC)"
	@$(PY) -m bandit -r $(SRC_DIR) -ll || true
	@if command -v semgrep >/dev/null 2>&1; then \
		echo "$(CYAN)🔍 Advanced code analysis...$(NC)"; \
		semgrep --config=auto $(SRC_DIR) --json --output=semgrep-report.json || true; \
	fi
	@echo "$(GREEN)✅ Security analysis complete$(NC)"

deps-check: ## 🔒 Check dependencies for updates and vulnerabilities
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@$(MAKE) _ensure-venv
	$(PIP) list --outdated
	@$(PY) -m pip_audit || echo "$(YELLOW)⚠️  Install pip-audit for vulnerability scanning$(NC)"

deps-diagnose: ## 📊 Diagnose missing dependencies
	@echo "$(BOLD)$(BLUE)🔍 Dependency Diagnostics$(NC)"
	@$(MAKE) _ensure-venv
	@$(PY) -c "import numpy; print('✅ numpy: Available')" 2>/dev/null || echo "❌ numpy: Missing"
	@$(PY) -c "import schedule; print('✅ schedule: Available')" 2>/dev/null || echo "❌ schedule: Missing"
	@$(PY) -c "import aiohttp; print('✅ aiohttp: Available')" 2>/dev/null || echo "❌ aiohttp: Missing"
	@$(PY) -c "import dns.resolver; print('✅ dnspython: Available')" 2>/dev/null || echo "❌ dnspython: Missing"
	@$(PY) -c "import inotify; print('✅ inotify: Available')" 2>/dev/null || echo "❌ inotify: Missing"
	@echo ""
	@echo "$(CYAN)📦 Solutions: make install-advanced | make install-all$(NC)"

# === Build & Distribution ===
build: ## 📦 Build distribution packages
	@echo "$(BOLD)$(BLUE)Building distribution packages...$(NC)"
	@$(MAKE) _ensure-venv
	@$(MAKE) clean
	$(PY) -m build
	@echo "$(GREEN)✅ Packages built in dist/$(NC)"

clean: ## 🧹 Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build dist *.egg-info
	rm -rf $(SRC_DIR)/__pycache__ $(TEST_DIR)/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -f security-report.json semgrep-report.json
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# === Information & Status ===
status: ## 📊 Show project and environment status
	@echo "$(BOLD)$(BLUE)📊 Project Status$(NC)"
	@echo ""
	@echo "$(BOLD)$(CYAN)📦 Project$(NC)"
	@echo "  Name: $(PROJECT_NAME)"
	@echo "  Version: $(GREEN)$(VERSION)$(NC)"
	@echo "  Location: $(shell pwd)"
	@echo ""
	@echo "$(BOLD)$(CYAN)🐍 Python Environment$(NC)"
	@echo "  Python: $(shell $(PY) --version 2>/dev/null || echo 'Not available')"
	@echo "  Virtual Env: $(if $(filter true,$(HAS_VENV)),$(GREEN)✅ Active$(NC) ($(VENV_DIR)),$(RED)❌ Not found$(NC))"
	@echo "  Package Manager: $(if $(filter true,$(HAS_UV)),$(GREEN)UV available$(NC),$(YELLOW)UV not installed$(NC))"
	@echo ""
	@echo "$(BOLD)$(CYAN)🔧 Development Tools$(NC)"
	@printf "  Node.js/npm: "; command -v npm >/dev/null && echo "$(GREEN)✅ Available$(NC)" || echo "$(YELLOW)Not installed$(NC)"
	@printf "  Ruff: "; command -v ruff >/dev/null && echo "$(GREEN)✅ Available$(NC)" || echo "$(YELLOW)Not installed$(NC)"
	@printf "  MyPy: "; $(PY) -c "import mypy" 2>/dev/null && echo "$(GREEN)✅ Available$(NC)" || echo "$(YELLOW)Not installed$(NC)"
	@echo ""
	@echo "$(BOLD)$(CYAN)🔒 Security Tools$(NC)"
	@printf "  Bandit: "; $(PY) -c "import bandit" 2>/dev/null && echo "$(GREEN)✅ Available$(NC)" || echo "$(YELLOW)Not installed$(NC)"
	@printf "  pip-audit: "; command -v pip-audit >/dev/null && echo "$(GREEN)✅ Available$(NC)" || echo "$(YELLOW)Not installed$(NC)"
	@printf "  Semgrep: "; command -v semgrep >/dev/null && echo "$(GREEN)✅ Available$(NC)" || echo "$(YELLOW)Not installed$(NC)"

version: ## 📊 Show version information
	@echo "$(BOLD)$(BLUE)$(PROJECT_NAME) v$(VERSION)$(NC)"
	@echo "Python: $(shell $(PY) --version 2>/dev/null || echo 'Not available')"
	@echo "Location: $(shell pwd)"

# === Modernization Tools ===
modernize-check: ## ⚡ Check for deprecated patterns and suggest upgrades
	@echo "$(BOLD)$(BLUE)🔍 Modernization Analysis$(NC)"
	@echo ""
	@echo "$(BOLD)$(CYAN)📋 Build System$(NC)"
	@[ -f "pyproject.toml" ] && echo "  $(GREEN)✅ pyproject.toml present$(NC)" || echo "  $(RED)❌ Missing pyproject.toml$(NC)"
	@echo ""
	@echo "$(BOLD)$(CYAN)📦 Package Management$(NC)"
	@[ "$(HAS_UV)" = "true" ] && echo "  $(GREEN)✅ UV available$(NC)" || echo "  $(YELLOW)💡 Consider installing UV$(NC)"
	@echo ""
	@echo "$(BOLD)$(CYAN)🔧 Development Tools$(NC)"
	@command -v ruff >/dev/null && echo "  $(GREEN)✅ Ruff available$(NC)" || echo "  $(YELLOW)💡 Install ruff$(NC)"
	@[ -f ".pre-commit-config.yaml" ] && echo "  $(GREEN)✅ Pre-commit configured$(NC)" || echo "  $(YELLOW)💡 Add pre-commit hooks$(NC)"
	@echo ""
	@echo "$(CYAN)💡 Run 'make migrate-to-modern' for automated fixes$(NC)"

migrate-to-modern: ## ⚡ Automatically apply modern Python practices
	@echo "$(BOLD)$(BLUE)🚀 Applying modernization...$(NC)"
	@$(MAKE) _install-uv-if-needed
	@$(MAKE) _setup-precommit-if-needed
	@$(MAKE) install-dev
	@echo "$(GREEN)✅ Modernization complete$(NC)"

deprecation-check: ## ⚡ Check for Python deprecation warnings
	@echo "$(BLUE)Checking for deprecation warnings...$(NC)"
	@$(MAKE) _ensure-venv
	@PYTHONWARNINGS=default $(PY) -Wd -c "import $(SRC_DIR)" 2>&1 | \
		grep -E "(DeprecationWarning|FutureWarning)" || echo "$(GREEN)✅ No deprecation warnings$(NC)"

# === Development Workflows ===
dev: ## 🔧 Complete development workflow (setup + test + lint)
	@echo "$(BOLD)$(BLUE)🔧 Development workflow...$(NC)"
	@$(MAKE) setup
	@$(MAKE) test-quick
	@$(MAKE) lint
	@echo "$(GREEN)🎉 Development workflow complete$(NC)"

quick: ## ⚡ Quick validation (lint + quick tests)
	@echo "$(BLUE)Quick validation...$(NC)"
	@$(MAKE) _ensure-venv
	@$(MAKE) format
	@$(MAKE) test-quick
	@echo "$(GREEN)✅ Quick validation complete$(NC)"

pre-commit: ## 🧪 Run all pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	@$(MAKE) format
	@$(MAKE) test-quick
	@$(MAKE) security
	@echo "$(GREEN)✅ Pre-commit checks complete$(NC)"

ci-test: ## 🧪 CI/CD test suite
	@echo "$(BLUE)Running CI test suite...$(NC)"
	@$(MAKE) _ensure-venv
	@$(MAKE) modernize-check
	@$(MAKE) deprecation-check
	@$(PY) -m pytest $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=xml --maxfail=3
	@echo "$(GREEN)✅ CI tests complete$(NC)"

release-check: ## 📊 Comprehensive release preparation validation
	@echo "$(BOLD)$(BLUE)🔍 Release validation...$(NC)"
	@$(MAKE) clean
	@$(MAKE) modernize-check
	@$(MAKE) ci-test
	@$(MAKE) build
	@echo "$(GREEN)🎉 Release validation complete$(NC)"

# === Internal Helper Targets ===
_ensure-venv:
	@if [ "$(HAS_VENV)" != "true" ]; then \
		echo "$(RED)❌ Virtual environment not found$(NC)"; \
		echo "$(CYAN)💡 Run 'make setup' first$(NC)"; \
		exit 1; \
	fi

_create-venv:
	@if [ "$(HAS_UV)" = "true" ]; then \
		echo "$(CYAN)Creating UV-based virtual environment...$(NC)"; \
		uv venv $(VENV_DIR) --python $(PYTHON); \
	else \
		$(MAKE) _create-venv-standard; \
	fi

_create-venv-standard:
	@echo "$(CYAN)Creating standard virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)

_install-uv-if-needed:
	@if [ "$(HAS_UV)" != "true" ]; then \
		echo "$(CYAN)Installing UV package manager...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)✅ UV installed$(NC)"; \
	fi

_setup-precommit-if-needed:
	@if [ ! -f ".pre-commit-config.yaml" ]; then \
		echo "$(CYAN)Setting up pre-commit hooks...$(NC)"; \
		echo 'repos:' > .pre-commit-config.yaml; \
		echo '  - repo: https://github.com/astral-sh/ruff-pre-commit' >> .pre-commit-config.yaml; \
		echo '    rev: v0.1.8' >> .pre-commit-config.yaml; \
		echo '    hooks:' >> .pre-commit-config.yaml; \
		echo '      - id: ruff' >> .pre-commit-config.yaml; \
		echo '      - id: ruff-format' >> .pre-commit-config.yaml; \
		echo "$(GREEN)✅ Pre-commit configured$(NC)"; \
	fi

# === Special Targets ===
.DEFAULT_GOAL := help

# Declare all targets as phony to prevent conflicts
.PHONY: help setup setup-standard install install-dev install-advanced install-all
.PHONY: run run-debug run-console test test-quick test-gui lint format security
.PHONY: deps-check deps-diagnose build clean status version
.PHONY: modernize-check migrate-to-modern deprecation-check
.PHONY: dev quick pre-commit ci-test release-check
.PHONY: _ensure-venv _create-venv _create-venv-standard _install-uv-if-needed _setup-precommit-if-needed
