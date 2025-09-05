# xanadOS Search & Destroy - Modern Development Makefile
# Enhanced with 2025 best practices and modern tooling

.PHONY: help setup setup-modern setup-full clean test validate install-deps
.PHONY: dev dev-gui run run-tests benchmark security-scan docs
.PHONY: docker-build docker-run docker-dev update-deps check-env
.PHONY: pre-commit format lint type-check audit release

# Default goal
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color
BOLD := \033[1m

# Project configuration
PROJECT_NAME := xanadOS-Search_Destroy
VERSION := $(shell cat VERSION 2>/dev/null || echo "2.12.0")
PYTHON_VERSION := 3.11
NODE_VERSION := lts

# Directory paths
SCRIPTS_DIR := scripts
TOOLS_DIR := $(SCRIPTS_DIR)/tools
SETUP_DIR := $(SCRIPTS_DIR)/setup
DOCS_DIR := docs
TESTS_DIR := tests

# Package managers and tools
PYTHON := python3
UV := uv
PNPM := pnpm
FNM := fnm

# Environment detection
SHELL_NAME := $(shell basename $$SHELL)
OS := $(shell uname -s)
ARCH := $(shell uname -m)

##@ Help

help: ## Display this help
	@echo -e "$(BOLD)$(CYAN)🚀 xanadOS Search & Destroy - Development Commands$(NC)"
	@echo ""
	@echo -e "$(BOLD)Usage:$(NC) make [target]"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Environment Setup

setup: ## Quick setup with modern tools (recommended)
	@echo -e "$(BOLD)$(GREEN)🔧 Setting up modern development environment...$(NC)"
	@chmod +x $(SETUP_DIR)/modern-dev-setup.sh
	@$(SETUP_DIR)/modern-dev-setup.sh

setup-modern: setup ## Alias for modern setup

setup-full: ## Full setup with all optional components
	@echo -e "$(BOLD)$(GREEN)🔧 Setting up complete development environment...$(NC)"
	@chmod +x $(SCRIPTS_DIR)/setup-dev-environment.sh
	@$(SCRIPTS_DIR)/setup-dev-environment.sh
	@make setup-modern

setup-legacy: ## Legacy setup (fallback)
	@echo -e "$(BOLD)$(YELLOW)⚠️  Running legacy setup...$(NC)"
	@chmod +x $(SCRIPTS_DIR)/setup-dev-environment.sh
	@$(SCRIPTS_DIR)/setup-dev-environment.sh

##@ Development

dev: install-deps ## Start development environment
	@echo -e "$(BOLD)$(GREEN)🚀 Starting development environment...$(NC)"
	@if command -v direnv >/dev/null 2>&1; then \
		echo -e "$(CYAN)Using direnv for automatic environment activation$(NC)"; \
		direnv allow; \
	else \
		echo -e "$(YELLOW)Activating Python virtual environment...$(NC)"; \
		if [ -d ".venv" ]; then source .venv/bin/activate; fi; \
	fi

dev-gui: install-deps ## Start GUI development environment
	@echo -e "$(BOLD)$(GREEN)🖥️  Starting GUI development environment...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m app.main; \
	else \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

run: ## Run the application
	@echo -e "$(BOLD)$(GREEN)🎯 Running xanadOS Search & Destroy...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m app.main; \
	else \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

##@ Dependencies

install-deps: check-env ## Install all dependencies with modern package managers
	@echo -e "$(BOLD)$(GREEN)📦 Installing dependencies...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		echo -e "$(CYAN)Installing Python dependencies with uv...$(NC)"; \
		$(UV) sync --all-extras; \
	else \
		echo -e "$(YELLOW)Installing Python dependencies with pip...$(NC)"; \
		pip install -e .; \
	fi
	@if [ -f "package.json" ] && command -v $(PNPM) >/dev/null 2>&1; then \
		echo -e "$(CYAN)Installing JavaScript dependencies with pnpm...$(NC)"; \
		$(PNPM) install; \
	elif [ -f "package.json" ]; then \
		echo -e "$(YELLOW)Installing JavaScript dependencies with npm...$(NC)"; \
		npm install; \
	fi

update-deps: ## Update all dependencies
	@echo -e "$(BOLD)$(GREEN)🔄 Updating dependencies...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) sync --upgrade; \
	fi
	@if [ -f "package.json" ] && command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) update; \
	elif [ -f "package.json" ]; then \
		npm update; \
	fi

##@ Quality Assurance

validate: ## Run comprehensive validation (recommended)
	@echo -e "$(BOLD)$(GREEN)✅ Running comprehensive validation...$(NC)"
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) run quick:validate; \
	else \
		npm run quick:validate; \
	fi

test: run-tests ## Run tests

run-tests: ## Run all tests
	@echo -e "$(BOLD)$(GREEN)🧪 Running tests...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m pytest $(TESTS_DIR) -v; \
	else \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

benchmark: ## Run performance benchmarks
	@echo -e "$(BOLD)$(GREEN)📊 Running performance benchmarks...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m pytest $(TESTS_DIR) -v --benchmark-only; \
	fi

lint: ## Run linting tools
	@echo -e "$(BOLD)$(GREEN)🔍 Running linting tools...$(NC)"
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) run lint; \
	else \
		npm run lint; \
	fi
	@if [ -d ".venv" ] && command -v ruff >/dev/null 2>&1; then \
		source .venv/bin/activate && ruff check .; \
	fi

format: ## Format code
	@echo -e "$(BOLD)$(GREEN)✨ Formatting code...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate; \
		if command -v ruff >/dev/null 2>&1; then \
			ruff format .; \
		elif command -v black >/dev/null 2>&1; then \
			black .; \
		fi; \
		if command -v isort >/dev/null 2>&1; then \
			isort .; \
		fi; \
	fi
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) run lint:fix; \
	elif [ -f "package.json" ]; then \
		npm run lint:fix; \
	fi

type-check: ## Run type checking
	@echo -e "$(BOLD)$(GREEN)🔍 Running type checking...$(NC)"
	@if [ -d ".venv" ] && command -v mypy >/dev/null 2>&1; then \
		source .venv/bin/activate && mypy app/; \
	fi

audit: ## Run security audit
	@echo -e "$(BOLD)$(GREEN)🔒 Running security audit...$(NC)"
	@if [ -d ".venv" ] && command -v bandit >/dev/null 2>&1; then \
		source .venv/bin/activate && bandit -r app/; \
	fi
	@if [ -d ".venv" ] && command -v safety >/dev/null 2>&1; then \
		source .venv/bin/activate && safety check; \
	fi
	@if [ -f "package.json" ] && command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) audit; \
	elif [ -f "package.json" ]; then \
		npm audit; \
	fi

##@ Security

security-scan: ## Run comprehensive security scan
	@echo -e "$(BOLD)$(GREEN)🛡️  Running security scan...$(NC)"
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) run security:check; \
	else \
		npm run security:check; \
	fi
	@chmod +x $(TOOLS_DIR)/security/security-scan.sh
	@$(TOOLS_DIR)/security/security-scan.sh --quick

pre-commit: format lint type-check ## Run pre-commit checks
	@echo -e "$(BOLD)$(GREEN)✅ Pre-commit checks completed$(NC)"

##@ Documentation

docs: ## Generate documentation
	@echo -e "$(BOLD)$(GREEN)📚 Generating documentation...$(NC)"
	@if [ -d ".venv" ] && command -v sphinx-build >/dev/null 2>&1; then \
		source .venv/bin/activate && make -C docs html; \
	fi

docs-serve: docs ## Serve documentation locally
	@echo -e "$(BOLD)$(GREEN)🌐 Serving documentation at http://localhost:8000$(NC)"
	@if [ -d ".venv" ] && command -v python >/dev/null 2>&1; then \
		source .venv/bin/activate && cd docs/_build/html && python -m http.server 8000; \
	fi

##@ Docker

docker-build: ## Build Docker image
	@echo -e "$(BOLD)$(GREEN)🐳 Building Docker image...$(NC)"
	@docker build -t $(PROJECT_NAME):$(VERSION) .

docker-run: docker-build ## Run application in Docker
	@echo -e "$(BOLD)$(GREEN)🐳 Running application in Docker...$(NC)"
	@docker run --rm -it \
		-v $(PWD):/workspace \
		-p 8080:8080 \
		$(PROJECT_NAME):$(VERSION)

docker-dev: ## Run development environment in Docker
	@echo -e "$(BOLD)$(GREEN)🐳 Starting development environment in Docker...$(NC)"
	@docker run --rm -it \
		-v $(PWD):/workspace \
		-w /workspace \
		-p 8080:8080 \
		--entrypoint /bin/bash \
		$(PROJECT_NAME):$(VERSION)

##@ Maintenance

clean: ## Clean build artifacts and caches
	@echo -e "$(BOLD)$(YELLOW)🧹 Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage .tox/ 2>/dev/null || true
	@if [ -d "node_modules" ]; then rm -rf node_modules; fi
	@if [ -f "package-lock.json" ]; then rm -f package-lock.json; fi
	@echo -e "$(GREEN)✅ Cleanup completed$(NC)"

clean-env: ## Remove virtual environment
	@echo -e "$(BOLD)$(YELLOW)🗑️  Removing virtual environment...$(NC)"
	@if [ -d ".venv" ]; then rm -rf .venv; fi
	@echo -e "$(GREEN)✅ Virtual environment removed$(NC)"

reset: clean clean-env ## Reset environment completely
	@echo -e "$(BOLD)$(YELLOW)🔄 Resetting environment...$(NC)"
	@echo -e "$(GREEN)✅ Environment reset completed$(NC)"

##@ Utilities

check-env: ## Check environment status
	@echo -e "$(BOLD)$(CYAN)🔍 Environment Status$(NC)"
	@echo -e "$(BOLD)System Information:$(NC)"
	@echo -e "  OS: $(CYAN)$(OS) $(ARCH)$(NC)"
	@echo -e "  Shell: $(CYAN)$(SHELL_NAME)$(NC)"
	@echo ""
	@echo -e "$(BOLD)Package Managers:$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		echo -e "  uv: $(GREEN)✅ $(shell $(UV) --version)$(NC)"; \
	else \
		echo -e "  uv: $(RED)❌ Not installed$(NC)"; \
	fi
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		echo -e "  pnpm: $(GREEN)✅ $(shell $(PNPM) --version)$(NC)"; \
	else \
		echo -e "  pnpm: $(RED)❌ Not installed$(NC)"; \
	fi
	@if command -v $(FNM) >/dev/null 2>&1; then \
		echo -e "  fnm: $(GREEN)✅ $(shell $(FNM) --version)$(NC)"; \
	else \
		echo -e "  fnm: $(RED)❌ Not installed$(NC)"; \
	fi
	@if command -v node >/dev/null 2>&1; then \
		echo -e "  Node.js: $(GREEN)✅ $(shell node --version)$(NC)"; \
	else \
		echo -e "  Node.js: $(RED)❌ Not installed$(NC)"; \
	fi
	@if command -v $(PYTHON) >/dev/null 2>&1; then \
		echo -e "  Python: $(GREEN)✅ $(shell $(PYTHON) --version)$(NC)"; \
	else \
		echo -e "  Python: $(RED)❌ Not installed$(NC)"; \
	fi
	@echo ""
	@echo -e "$(BOLD)Virtual Environment:$(NC)"
	@if [ -d ".venv" ]; then \
		echo -e "  Status: $(GREEN)✅ Active$(NC)"; \
	else \
		echo -e "  Status: $(RED)❌ Not found$(NC)"; \
	fi

version: ## Show version information (from VERSION file)
	@echo -e "$(BOLD)$(CYAN)📋 Version Information$(NC)"
	@echo -e "  Project: $(CYAN)$(PROJECT_NAME)$(NC)"
	@echo -e "  Version: $(CYAN)$(VERSION)$(NC)"
	@echo -e "  Python Target: $(CYAN)$(PYTHON_VERSION)+$(NC)"
	@echo -e "  Node Target: $(CYAN)$(NODE_VERSION)$(NC)"

version-get: ## Get current version from VERSION file
	@python scripts/tools/version_manager.py --get

version-sync: ## Synchronize all files with VERSION file
	@echo -e "$(BOLD)$(GREEN)🔄 Synchronizing versions...$(NC)"
	@python scripts/tools/version_manager.py --sync

version-info: ## Show detailed version information
	@python scripts/tools/version_manager.py --version-info

upgrade-tools: ## Upgrade development tools
	@echo -e "$(BOLD)$(GREEN)⬆️  Upgrading development tools...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		$(PNPM) add -g pnpm; \
	fi
	@if command -v $(FNM) >/dev/null 2>&1; then \
		curl -fsSL https://fnm.vercel.app/install | bash; \
	fi

info: check-env version ## Show comprehensive environment information

##@ Release

release: version-sync validate test ## Prepare release with version sync
	@echo -e "$(BOLD)$(GREEN)🚀 Preparing release $(VERSION)...$(NC)"
	@echo -e "$(CYAN)Running final validation...$(NC)"
	@make validate
	@echo -e "$(GREEN)✅ Release $(VERSION) is ready$(NC)"

# Advanced targets for power users
##@ Advanced

nix-setup: ## Setup Nix development environment (experimental)
	@echo -e "$(BOLD)$(CYAN)❄️  Setting up Nix development environment...$(NC)"
	@if command -v nix >/dev/null 2>&1; then \
		echo "use flake" > .envrc; \
		direnv allow; \
	else \
		echo -e "$(RED)❌ Nix not installed. Install Nix first.$(NC)"; \
		exit 1; \
	fi

devcontainer: ## Setup VS Code DevContainer
	@echo -e "$(BOLD)$(CYAN)📦 Setting up VS Code DevContainer...$(NC)"
	@mkdir -p .devcontainer
	@if [ ! -f ".devcontainer/devcontainer.json" ]; then \
		echo '{"name": "xanadOS Dev", "image": "mcr.microsoft.com/devcontainers/python:3.11", "features": {"ghcr.io/devcontainers/features/node:1": {}}}' > .devcontainer/devcontainer.json; \
	fi

perf-profile: ## Profile application performance
	@echo -e "$(BOLD)$(GREEN)📈 Profiling application performance...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m cProfile -o profile.stats -m app.main; \
		python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"; \
	fi

# Make sure we can run setup even without make
bootstrap: ## Bootstrap development environment (no deps)
	@echo -e "$(BOLD)$(GREEN)🥾 Bootstrapping development environment...$(NC)"
	@chmod +x $(SETUP_DIR)/modern-dev-setup.sh
	@$(SETUP_DIR)/modern-dev-setup.sh
