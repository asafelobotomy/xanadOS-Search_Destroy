---
applyTo: "**/*"
priority: "framework"
---

# GitHub Copilot Enhancement Framework - Complete Instructions

This is the comprehensive GitHub Copilot Enhancement Framework that includes specialized instructions, chat modes, and tools for enhanced AI-assisted development.

## 🎯 Framework Overview

This framework provides:
- **Core Repository Instructions** - Base functionality and guidelines
- **11 Specialized Instruction Sets** - Domain-specific guidance (security, testing, docs, etc.)
- **11 Chat Modes** - Specialized AI personalities for different development tasks
- **Validation Systems** - Quality assurance and compliance checking
- **Toolshed Integration** - Pre-built scripts and utilities

## 📋 Specialized Instructions (Contextual Loading)

### Core Development
- **Agent Workflow**: Systematic "Check First, Act Second" methodology
- **Code Quality**: Standards for maintainable, clean code
- **Security**: Security-first development practices
- **Testing**: Test-driven development and validation
- **Documentation**: Technical writing and docs standards

### Repository Management
- **File Organization**: Directory structure and placement rules
- **Version Control**: Git workflows and branch management
- **Toolshed Usage**: Leveraging existing scripts and tools
- **Archive Policy**: Managing deprecated and legacy content
- **Documentation Awareness**: Finding and using existing docs

### Quality Assurance
- **Debugging**: Systematic troubleshooting approaches
- **Docs Policy**: Documentation consistency and standards

## 🤖 Specialized Chat Modes

### Architecture & Design
- **Architect** - System design and architecture planning
- **Claude Sonnet 4 Architect** - Advanced architectural reasoning
- **Advanced Task Planner** - Complex project planning and breakdown

### Development Specialization
- **Elite Engineer** - Advanced development practices and patterns
- **GPT-5 Elite Developer** - Cutting-edge development techniques
- **O1 Preview Reasoning** - Deep reasoning and problem-solving

### Domain Expertise
- **Security** - Security-focused development and auditing
- **Testing** - Test-driven development and quality assurance
- **Performance** - Optimization and performance tuning
- **Documentation** - Technical writing and documentation

### AI Model Specialization
- **Gemini Pro Specialist** - Gemini-optimized development workflows

## 🔧 Quick Setup for New Projects

### Essential Commands
```bash
# Repository setup with industry standards
./scripts/tools/git/setup-repository.sh

# Comprehensive validation
./scripts/tools/validation/validate-structure.sh

# Code quality with auto-fix
./scripts/tools/quality/check-quality.sh --fix

# Quick validation pipeline
npm run quick:validate
```

### GitHub Copilot Chat Usage

**Load specific instruction sets:**
```
@github use .github/instructions/security.instructions.md
@github use .github/instructions/testing.instructions.md
@github use .github/instructions/code-quality.instructions.md
```

**Activate specialized chat modes:**
```
@github use .github/chatmodes/architect.chatmode.md
@github use .github/chatmodes/security.chatmode.md
@github use .github/chatmodes/elite-engineer.chatmode.md
```

**Complete framework installation:**
```bash
# Run the comprehensive setup script
./scripts/tools/setup/install-copilot-framework.sh
```

## 📁 Repository Structure Integration

### Instructions Directory (.github/instructions/)
- `agent-workflow.instructions.md` - Core workflow methodology
- `code-quality.instructions.md` - Code standards and practices
- `security.instructions.md` - Security guidelines
- `testing.instructions.md` - Testing methodology
- `docs-policy.instructions.md` - Documentation standards
- `documentation-awareness.instructions.md` - Using existing docs
- `file-organization.instructions.md` - Directory structure rules
- `toolshed-usage.instructions.md` - Leveraging existing tools
- `version-control.instructions.md` - Git workflows
- `debugging.instructions.md` - Troubleshooting practices
- `archive-policy.instructions.md` - Managing legacy content

### Chat Modes Directory (.github/chatmodes/)
- `architect.chatmode.md` - System architecture and design
- `elite-engineer.chatmode.md` - Advanced development practices
- `documentation.chatmode.md` - Technical writing focus
- `security.chatmode.md` - Security-first development
- `testing.chatmode.md` - Test-driven development
- `performance.chatmode.md` - Optimization focus
- `advanced-task-planner.chatmode.md` - Project planning
- `claude-sonnet4-architect.chatmode.md` - Claude-specific workflows
- `gemini-pro-specialist.chatmode.md` - Gemini-optimized development
- `gpt5-elite-developer.chatmode.md` - GPT-5 development patterns
- `o1-preview-reasoning.chatmode.md` - Deep reasoning mode

### Toolshed Directory (scripts/tools/)
- Git utilities and repository setup
- Validation and quality checking scripts
- Documentation generation tools
- Testing and compliance scripts

## 🎯 Core Workflow Philosophy

**"Check First, Act Second" Methodology:**

1. **📚 Discovery Phase** - Read ALL relevant instructions
2. **🔍 Analysis Phase** - Understand requirements and constraints  
3. **✅ Validation Phase** - Verify planned actions against instructions
4. **🎯 Execution Phase** - Execute with full compliance
5. **🔄 Verification Phase** - Confirm successful completion

### Quality-First Principles
- **Thoroughness Over Speed** - Taking time upfront prevents rework
- **Prevention Over Correction** - Follow instructions to avoid mistakes
- **Systematic Over Reactive** - Use established workflows consistently
- **Quality Over Quantity** - Better to do fewer things correctly

## 📊 Quick Reference Commands

### Validation Pipeline
```bash
npm run lint                    # Markdown linting
npm run validate               # Template and structure validation
npm run quick:validate         # Complete validation pipeline
```

### Setup and Installation
```bash
./scripts/tools/setup/install-copilot-framework.sh  # Complete framework setup
./scripts/tools/git/setup-repository.sh             # Repository standards
./scripts/tools/validation/validate-structure.sh    # Structure validation
```

### Quality Assurance
```bash
./scripts/tools/quality/check-quality.sh --fix     # Auto-fix quality issues
```

## 🚀 Getting Started

1. **For VS Code Users**: This file provides the complete framework when loaded
2. **For Script Users**: Run `./scripts/tools/setup/install-copilot-framework.sh`
3. **For Manual Setup**: Follow the installation guide in README.md

## 📖 Additional Resources

- **Complete Documentation**: `docs/guides/COPILOT-INSTRUCTIONS-GUIDE.md`
- **Repository Organization**: `docs/REPOSITORY_ORGANIZATION.md`
- **Toolshed Overview**: `scripts/tools/README.md`
- **Validation Reports**: Generated in `.github/validation/reports/`

---

**Framework Version**: Comprehensive GitHub Copilot Enhancement Framework  
**Components**: Core + 11 Specialized Instructions + 11 Chat Modes + Validation + Toolshed  
**Philosophy**: Quality-first, systematic development with AI assistance
