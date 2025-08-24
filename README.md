# 🚀 GitHub Copilot Enhancement Framework

[![CI](https://github.com/asafelobotomy/agent-instructions-co-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/asafelobotomy/agent-instructions-co-pilot/actions/workflows/ci.yml)
[![Spellcheck](https://github.com/asafelobotomy/agent-instructions-co-pilot/actions/workflows/spellcheck.yml/badge.svg)](https://github.com/asafelobotomy/agent-instructions-co-pilot/actions/workflows/spellcheck.yml)
[![Link Check](https://github.com/asafelobotomy/agent-instructions-co-pilot/actions/workflows/link-check.yml/badge.svg)](https://github.com/asafelobotomy/agent-instructions-co-pilot/actions/workflows/link-check.yml)

**A comprehensive enterprise-grade system for AI-assisted development with specialized
chatmodes, prompt templates, and advanced instructions.**

_Quality Score: **98.9%** | Enterprise Excellence Level | Production Ready_

## Start here

- Read first: `.github/instructions/agent-workflow.instructions.md`
- Instruction map: `.github/instructions/INDEX.md`
- Toolshed overview: `scripts/tools/README.md`
- Validate quickly: `npm run quick:validate`
- Placeholder log: `docs/reports/PLACEHOLDERS.md`

## 🛠️ **IMPORTANT: Ready-to-Use Toolshed Available**

**⚡ This repository includes a complete toolshed of pre-built scripts that GitHub
Copilot agents should ALWAYS use instead of recreating functionality.**

### 🔧 **Essential Tools for Immediate Use:**

```bash
# Repository setup with industry standards (instead of manual setup)
./scripts/tools/git/setup-repository.sh

# Comprehensive validation (instead of custom checks)
./scripts/tools/validation/validate-structure.sh

# Code quality with auto-fix (instead of manual review)
./scripts/tools/quality/check-quality.sh --fix

# Deploy complete toolshed to any repository
./scripts/tools/implement-toolshed.sh
```

**📖 Complete Tool Catalog**: `scripts/tools/README.md` (20+ tools across 6 categories)

**🎯 Always check the toolshed first!** Avoid recreating existing functionality.

## 📚 **IMPORTANT: Comprehensive Documentation Repository**

**📖 This repository includes a complete documentation system in `/docs/` that
GitHub Copilot agents should ALWAYS use instead of creating redundant
documentation.**

### 📖 **Essential Documentation for Immediate Use:**

```bash
# Framework overview and capabilities (instead of creating new guides)
cat /docs/guides/ENHANCEMENTS.md

# Repository structure documentation (instead of custom structure docs)
cat /docs/guides/PROJECT_STRUCTURE.md

# Enterprise deployment guide (instead of setup instructions)
cat /docs/guides/organization-custom-instructions.md

# AI model targeting guide (instead of model-specific docs)
cat /docs/guides/model-targeting-guide.md
```

**📚 Complete Documentation Index**: `/docs/README.md` (6+ guides, templates, reports)

**🎯 Always check existing documentation first!** Avoid recreating content.

---

## 🎯 What This Repository Does

This framework transforms your GitHub Copilot experience by providing:

- **11 Specialized Chatmodes** - From architect to security specialist,
  each optimized for specific development tasks

- **7 Professional Prompt Templates** - Reusable, battle-tested prompts for common scenarios
- **Path-Specific Instructions** - Advanced targeting with `applyTo` frontmatter for file-specific guidance
- **Enterprise Validation System** - Comprehensive quality assurance with automated testing
- **Complete Script Toolshed** - 20+ pre-built tools for common development tasks
- **Advanced Model Support** - Optimized for GitHub Copilot 2025, GPT-5, Claude Sonnet 4,
  and Gemini Pro

## 🏗️ Repository Structure

### 📁 Core Framework Components

```text
📦 agent-instructions-co-pilot/
├── 🤖 .github/                    # GitHub Copilot Enhancement Framework
│   ├── 💬 chatmodes/             # 11 Specialized interaction modes
│   ├── 🎯 prompts/               # 7 Reusable prompt templates
│   ├── 📋 instructions/          # Path-specific development guidance
│   ├── 🔧 mcp/                   # Model Context Protocol integration
│   └── ✅ validation/            # Enterprise quality assurance
├── 📊 reports/                    # Development reports and analysis
│   ├── 📈 stages/                # Stage completion reports
│   ├── 🔍 analysis/              # Enhancement analysis reports
│   └── 🛡️ quality/               # Quality assurance reports
├── 🛠️ scripts/                   # Automation and utility scripts
│   ├── 🎭 stages/                # Stage implementation scripts
│   ├── ✨ quality/               # Quality enhancement tools
│   ├── ✅ validation/            # Structure and policy validation
│   └── 🔧 utils/                 # General utility scripts
├── 📚 docs/                      # Comprehensive documentation
├── 🗄️ archive/                   # Historical files and backups
└── 📋 repo-template/             # Ready-to-deploy template
```

### 🎯 Chatmode System

```text
.github/chatmodes/
├── architect.chatmode.md          # System design and architecture
├── elite-engineer.chatmode.md     # Advanced coding and optimization
├── security.chatmode.md           # Security analysis and hardening
├── testing.chatmode.md            # Test-driven development
├── performance.chatmode.md        # Performance optimization
├── documentation.chatmode.md      # Professional documentation
├── gpt5-elite-developer.chatmode.md      # GPT-5 optimized development
├── claude-sonnet4-architect.chatmode.md  # Claude Sonnet 4 architecture
├── gemini-pro-specialist.chatmode.md     # Gemini Pro specialization
├── o1-preview-reasoning.chatmode.md      # Advanced reasoning mode
└── advanced-task-planner.chatmode.md    # Complex task planning
```

### 🎯 Prompt Templates

```text
.github/prompts/
├── security-review.prompt.md      # Comprehensive security analysis
├── performance-optimization.prompt.md  # System performance enhancement
├── tdd-implementation.prompt.md   # Test-driven development
├── code-refactoring.prompt.md     # Code improvement strategies
├── api-design.prompt.md           # RESTful API design patterns
├── database-optimization.prompt.md # Database performance tuning
└── deployment-strategy.prompt.md  # Production deployment planning
```

### 📋 Advanced Instructions

```text
.github/instructions/
├── security.instructions.md       # Security-first development (all code files)
├── testing.instructions.md        # Testing excellence (test files)
└── debugging.instructions.md      # Comprehensive debugging guidance
└── 3 more instruction sets...
```

## 🚀 Quick Start

### 🎯 **One-Click VS Code Setup**

<!-- markdownlint-disable MD013 -->

**⚡ Choose your preferred setup method:**

| Method | Description | Action |
|--------|-------------|---------|
| **VS Code Web** | Open in browser-based VS Code | [![Open in VS Code](https://img.shields.io/badge/Open%20in-VS%20Code-007ACC?style=flat-square&logo=visual-studio-code&logoColor=white)](https://vscode.dev/github/asafelobotomy/agent-instructions-co-pilot) |
<!-- markdown-link-check-disable -->
| **Clone Directly** | Clone to VS Code desktop | [![Clone in VS Code](https://img.shields.io/badge/Clone%20in-VS%20Code-007ACC?style=flat-square&logo=visual-studio-code&logoColor=white)](vscode://vscode.git/clone?url=https://github.com/asafelobotomy/agent-instructions-co-pilot.git) |
<!-- markdown-link-check-enable -->
| **GitHub Codespaces** | Cloud development environment | [![Open in Codespaces](https://img.shields.io/badge/Open%20in-Codespaces-24292e?style=flat-square&logo=github&logoColor=white)](https://codespaces.new/asafelobotomy/agent-instructions-co-pilot) |
| **Essential Files Only** | Copy key files to existing project | See command below ⬇️ |

<!-- markdownlint-enable MD013 -->

### 📦 **Essential Files Quick Deploy**

**Add GitHub Copilot enhancement files to your existing project:**

```bash
# Copy essential files to current directory
curl -sSL https://git.io/copilot-essentials | bash -s -- --essential-only
```

### Installation Options

#### Option 1: **VS Code Integration** (Recommended)

   1. **Click the "Clone in VS Code" button above** ⬆️
   2. VS Code will open and prompt you to clone the repository
   3. Choose your workspace location
   4. The essential files will be available immediately

#### Option 2: **Manual Clone**

   ```bash
   git clone https://github.com/asafelobotomy/agent-instructions-co-pilot.git
   cd agent-instructions-co-pilot
   ```

#### Option 3: **Essential Files Only**

   <!-- markdownlint-disable MD013 -->
   ```bash
   # Alternative: Use full URL
   curl -sSL \
     https://raw.githubusercontent.com/asafelobotomy/agent-instructions-co-pilot/main/scripts/tools/quick-setup.sh \
     | bash -s -- --essential-only
   ```
   <!-- markdownlint-enable MD013 -->

### ✅ **Validate Setup**

```bash
# Quick lint + validation
npm run quick:validate

# Or run structure validator directly
./scripts/validation/validate-structure.sh
```

Tip:

- In VS Code, run “Tasks: Run Task” → quick:validate
- In Codespaces, validations run fast on the prebuilt container

### 🎯 **Start Using Chatmodes**

   1. **Open VS Code** to your project directory
   2. **Navigate** to `.github/chatmodes/` in the Explorer
   3. **Copy content** from any `.chatmode.md` file
   4. **Paste into GitHub Copilot Chat** in VS Code
   5. **Start developing** with enhanced AI assistance!

### Usage Examples

#### System Architecture (architect.chatmode.md)

```text
Perfect for: API design, database schema, microservices planning
```

#### Security Analysis (security.chatmode.md)

```text
Perfect for: Vulnerability assessment, secure coding, compliance
```

#### Code Optimization (elite-engineer.chatmode.md)

```text
Perfect for: Performance tuning, refactoring, advanced algorithms
```

## 📚 Documentation

- 📖 [Complete Documentation](docs/README.md) — guides and references
- 🚀 [Project Structure Guide](docs/guides/PROJECT_STRUCTURE.md) — repository layout
- 🔧 [Copilot Instructions Guide](docs/guides/COPILOT-INSTRUCTIONS-GUIDE.md) — setup
- 🛠️ [Toolshed Reference](docs/guides/TOOLSHED-REFERENCE.md) — tools and utilities
- 🧪 [MCP Examples Index](docs/guides/MCP-EXAMPLES.md) — offline MCP demos
- 📘 [Agent Runbooks](.github/runbooks/) — step-by-step workflows

## 🏆 Enterprise Features

### Code Quality

- ✅ **ShellCheck** validation for all scripts
- ✅ **Prettier** formatting for consistent code style
- ✅ **Markdown linting** for documentation quality
- ✅ **EditorConfig** for cross-platform consistency

### Organization

- ✅ **Professional structure** following GitHub best practices
- ✅ **Archive system** for version management
- ✅ **Implementation reports** with detailed progress tracking
- ✅ **Automated validation** with 21 mandatory checks

### Model Support

- 🤖 **GPT-5** - Latest OpenAI model with advanced reasoning
- 🧠 **Claude Sonnet 4** - Anthropic's most capable model
- ⚡ **Gemini Pro** - Google's enterprise AI solution
- 🔄 **Cross-platform** compatibility

## 📊 Repository Snapshot

- Specialized chatmodes for common engineering scenarios
- Prompt templates for reusable AI interactions
- Instruction sets covering best practices and standards
- Validation and linting with automated checks
- Enterprise-grade docs with categorized reports

## 🤝 Contributing

This framework follows enterprise development standards:

1. **Code Quality**: All contributions must pass validation checks
2. **Documentation**: Updates require corresponding documentation
3. **Testing**: Changes must include appropriate test coverage
4. **Security**: OWASP Top 10 2024/2025 compliance required

## 📄 License

This project is open source and available under standard licensing terms.

---

**🎯 Ready to enhance your GitHub Copilot experience?** Start with the
[Project Structure Guide](docs/guides/PROJECT_STRUCTURE.md) or explore our
[specialized chatmodes](.github/chatmodes/).
