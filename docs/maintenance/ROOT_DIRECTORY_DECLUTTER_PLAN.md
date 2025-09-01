# Root Directory Decluttering Plan - Based on Research

**Date:** August 26, 2025
**Objective:** Modernize and declutter the root directory following best practices

## 🔍 **Research Findings - Modern Repository Organization**

### **Industry Best Practices:**

1. **Minimal Root Directory** - Only essential project files
2. **Consolidate Configuration** - Use `pyproject.toml` for Python tools
3. **Hidden Files Organization** - Reduce `.dotfile` clutter
4. **GitHub Standards** - Follow GitHub repository conventions

### **Modern Python Projects Should Have:**

- `pyproject.toml` (central configuration)
- `README.md`, `LICENSE`, `CONTRIBUTING.md`
- `.gitignore` (essential git config)
- Minimal other files

## 📊 **Current Issues Analysis**

### **MAJOR CLUTTER: 14 Configuration Files**

**Problem:** Each tool has its own config file = root directory chaos

**Files to Consolidate:**

- `.flake8` → `pyproject.toml` (via Ruff)
- `.pylintrc` → `pyproject.toml` (via Ruff)
- `.ruff.toml` → `pyproject.toml`
- `.markdownlint.json` → `pyproject.toml` or `.github/`
- `.prettierrc` & `.prettierignore` → `pyproject.toml` or consolidate
- `.cspell.json` & `cspell.json` → consolidate duplicates
- Various ignore files → consolidate

**Tools That Support pyproject.toml:**

- Ruff (replaces flake8, pylint, black, isort)
- Black, isort, mypy
- pytest, coverage
- Many other modern Python tools

## 🎯 **Modernization Strategy**

### **Phase 1: Create Modern pyproject.toml**

- Consolidate Python tool configurations
- Replace legacy setup files
- Centralize project metadata

### **Phase 2: Configuration Consolidation**

- Move appropriate configs to `.github/`
- Eliminate duplicate files
- Reduce dotfile clutter

### **Phase 3: Tool Modernization**

- Replace multiple linters with Ruff
- Standardize on modern Python tooling
- Update CI/CD configurations

### **Phase 4: File Organization**

- Move misplaced files (CLEANUP_PLAN.md)
- Create `.github/` structure
- Organize remaining configs

## 📋 **Target Root Directory Structure**

### **ESSENTIAL FILES (8-10 files maximum):**

```
/
├── README.md                 # Project overview
├── LICENSE                   # Legal requirements
├── CONTRIBUTING.md           # Contribution guide
├── CHANGELOG.md              # Version history
├── pyproject.toml           # Modern Python configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .gitignore              # Git configuration
├── .editorconfig           # Cross-platform editor settings
└── VERSION                 # Version information
```

### **CONFIGURATION ORGANIZATION:**

```
.github/
├── workflows/              # CI/CD
├── ISSUE_TEMPLATE/        # Issue templates
├── PULL_REQUEST_TEMPLATE/ # PR templates
└── linters/               # Tool-specific configs that can't be in pyproject.toml
    ├── .markdownlint.json
    ├── .prettierrc
    └── spellings/
        └── cspell.json
```

## 🚀 **Expected Benefits**

1. **Reduced Clutter:** 26 files → ~10 files (60% reduction)
2. **Modern Standards:** Following Python PEP 518/621
3. **Easier Maintenance:** Central configuration
4. **Better Developer Experience:** Less configuration sprawl
5. **Industry Compliance:** Matches modern Python project standards

## 🔧 **Implementation Steps**

1. Create comprehensive `pyproject.toml`
2. Move GitHub-specific files to `.github/`
3. Consolidate and eliminate duplicate configs
4. Remove legacy configuration files
5. Update tooling to use modern approaches
6. Test and validate all tools still work

## 📖 **References**

- PEP 518: Build System Requirements
- PEP 621: Project Metadata
- Ruff: Modern Python linting/formatting
- GitHub: Repository best practices
- Modern Python project structure guidelines
