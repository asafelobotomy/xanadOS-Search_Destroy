# xanadOS Search & Destroy - Modern Development Makefile
# Enhanced with 2025 best practices and modern tooling

.PHONY: help setup install-deps validate test check-env run run-debug dev clean lint format

# Default goal
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color
BOLD := \033[1m
WHITE := \033[1;37m
BLUE := \033[0;34m

# Tool commands
UV := uv
PNPM := pnpm
FNM := fnm

help: ## Show this help message
	@echo -e "$(BOLD)$(GREEN)🚀 xanadOS Search & Destroy - Development Commands$(NC)"
	@echo -e "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo -e "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

setup: ## Complete unified setup process (ONE COMMAND DOES EVERYTHING)
	@echo -e "$(BOLD)$(GREEN)🚀 Running Complete Setup - One Command Does Everything!$(NC)"
	@echo -e "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@$(MAKE) setup-quick

setup-quick: ## Quick setup using Makefile targets
	@echo -e "$(BOLD)$(CYAN)🚀 Quick Setup Process$(NC)"
	@$(MAKE) check-env
	@$(MAKE) setup-python-env
	@$(MAKE) install-deps
	@echo -e "$(BOLD)$(GREEN)✅ Quick setup completed!$(NC)"

setup-python-env: ## Setup Python virtual environment
	@echo -e "$(BOLD)$(BLUE)🐍 Setting up Python environment...$(NC)"
	@if [ ! -d ".venv" ]; then \
		if command -v $(UV) >/dev/null 2>&1; then \
			echo -e "$(CYAN)Creating virtual environment with uv...$(NC)"; \
			$(UV) venv .venv --python python3; \
		else \
			echo -e "$(CYAN)Creating virtual environment with python...$(NC)"; \
			python3 -m venv .venv; \
		fi; \
	else \
		echo -e "$(GREEN)✅ Virtual environment already exists$(NC)"; \
	fi

setup-full: ## Full setup using the bash script
	@echo -e "$(BOLD)$(GREEN)🚀 Running Full Setup Script...$(NC)"
	@echo -e "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@bash scripts/setup.sh
	@echo -e "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

setup-force: ## Force complete reinstallation of everything
	@echo -e "$(BOLD)$(YELLOW)🔄 Force Reinstalling Everything...$(NC)"
	@bash scripts/setup.sh --force

setup-minimal: ## Minimal setup (essential dependencies only)
	@echo -e "$(BOLD)$(BLUE)⚡ Running Minimal Setup...$(NC)"
	@bash scripts/setup.sh --minimal

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

validate: ## Run comprehensive validation
	@echo -e "$(BOLD)$(GREEN)✅ Running comprehensive validation...$(NC)"
	@npm run quick:validate

test: ## Run tests
	@echo -e "$(BOLD)$(GREEN)🧪 Running tests...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m pytest tests/ -v; \
	else \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

check-env: ## Check environment status
	@echo -e "$(BOLD)$(CYAN)🔍 Environment Status$(NC)"
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
	@if command -v python >/dev/null 2>&1; then \
		echo -e "  Python: $(GREEN)✅ $(shell python --version)$(NC)"; \
	else \
		echo -e "  Python: $(RED)❌ Not installed$(NC)"; \
	fi
	@echo -e "$(BOLD)Virtual Environment:$(NC)"
	@if [ -d ".venv" ]; then \
		if [ -n "$$VIRTUAL_ENV" ]; then \
			echo -e "  Status: $(GREEN)✅ Active$(NC)"; \
		else \
			echo -e "  Status: $(YELLOW)⚠️  Not active$(NC)"; \
			echo -e "  $(CYAN)💡 Run: source .venv/bin/activate.fish$(NC)"; \
		fi; \
	else \
		echo -e "  Status: $(RED)❌ Not found$(NC)"; \
		echo -e "  $(CYAN)💡 Run: make setup-python-env$(NC)"; \
	fi

setup-tools: ## Install required package managers manually
	@echo -e "$(BOLD)$(BLUE)🛠️  Installing development tools...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo -e "$(CYAN)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo -e "$(GREEN)✅ uv already installed$(NC)"; \
	fi
	@if ! command -v $(PNPM) >/dev/null 2>&1; then \
		echo -e "$(CYAN)Installing pnpm...$(NC)"; \
		curl -fsSL https://get.pnpm.io/install.sh | sh -; \
	else \
		echo -e "$(GREEN)✅ pnpm already installed$(NC)"; \
	fi
	@if ! command -v $(FNM) >/dev/null 2>&1; then \
		echo -e "$(CYAN)Installing fnm...$(NC)"; \
		curl -fsSL https://fnm.vercel.app/install | bash; \
	else \
		echo -e "$(GREEN)✅ fnm already installed$(NC)"; \
	fi
	@echo -e "$(BOLD)$(GREEN)✅ Tool installation completed!$(NC)"
	@echo -e "$(CYAN)💡 You may need to restart your terminal or run:$(NC)"
	@echo -e "$(CYAN)   source ~/.config/fish/config.fish$(NC)"

clean: ## Clean up build artifacts and temporary files
	@echo -e "$(BOLD)$(YELLOW)🧹 Cleaning up build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .coverage archive/testing-coverage/ .pytest_cache/ .tox/
	@rm -rf node_modules/.cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo -e "$(GREEN)✅ Cleanup completed!$(NC)"

dev: ## Start development environment
	@echo -e "$(BOLD)$(BLUE)🚀 Starting development environment...$(NC)"
	@if [ ! -d ".venv" ]; then \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)💡 Virtual environment ready!$(NC)"
	@echo -e "$(CYAN)💡 Run: source .venv/bin/activate.fish$(NC)"
	@echo -e "$(CYAN)💡 Then: python -m app.main$(NC)"
	@if [ -d ".venv" ]; then \
		echo -e "  Virtual Environment: $(GREEN)✅ Active$(NC)"; \
	else \
		echo -e "  Virtual Environment: $(YELLOW)⚠️  Not active$(NC)"; \
	fi

run: ## Run the application
	@echo -e "$(BOLD)$(GREEN)🚀 Starting xanadOS Search & Destroy...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m app.main; \
	else \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

run-debug: ## Run with debug logging enabled
	@echo -e "$(BOLD)$(GREEN)🔧 Starting with debug logging...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && DEBUG=1 PYTHONPATH=. python -m app.main; \
	else \
		echo -e "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

lint: ## Run code quality checks
	@echo -e "$(BOLD)$(GREEN)🧪 Running code quality checks...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m ruff check . || true; \
	else \
		echo -e "$(YELLOW)⚠️  Virtual environment not found. Install with 'make setup'$(NC)"; \
	fi

format: ## Format code with ruff
	@echo -e "$(BOLD)$(GREEN)🧪 Formatting code...$(NC)"
	@if [ -d ".venv" ]; then \
		source .venv/bin/activate && python -m ruff format . || true; \
	else \
		echo -e "$(YELLOW)⚠️  Virtual environment not found. Install with 'make setup'$(NC)"; \
	fi
