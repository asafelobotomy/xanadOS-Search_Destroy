---
applyTo: "scripts/**"
priority: "critical"
enforcement: "mandatory"
---

# Toolshed Usage Instructions - MANDATORY

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: All development tasks and script creation
- **Compliance**: Required before any automation work
- **Review Cycle**: Check toolshed first, always

## Executive Summary

All GitHub Copilot agents MUST check and utilize the existing toolshed in `scripts/tools/` before
creating any scripts, automation, or development tools. This prevents redundant work, ensures
consistency, and maintains quality standards across all projects.

## 🚨 **CRITICAL DIRECTIVE: Check Toolshed First**

Before writing ANY script or automation tool, agents MUST:

1. **Check `scripts/tools/README.md`** for existing tools
2. **Search the toolshed** for similar functionality
3. **Use existing tools** when available
4. **Extend existing tools** rather than creating duplicates
5. **Follow established patterns** for any new tools

## 📁 **Available Tool Categories**

### **Git Tools** (`scripts/tools/Git/`)

**Purpose**: Repository setup, workflow automation, release management

**Available Tools**:

- `setup-repository.sh` - Complete repository initialization with industry standards
- `workflow-helper.sh` - Advanced Git workflow automation (feature/release branches)

**Usage Example**:

````bash

## Instead of writing custom Git setup

./scripts/tools/Git/setup-repository.sh --help
./scripts/tools/Git/setup-repository.sh --dry-run

```text

### **Validation Tools** (`scripts/tools/validation/`)

**Purpose**: Repository structure validation, compliance checking

**Available Tools**:

- `validate-structure.sh` - Comprehensive repository validation (97% compliance checking)
- `validate-instructions.sh` - GitHub Copilot instruction file validation

**Usage Example**:

```bash

## Instead of writing custom validation

./scripts/tools/validation/validate-structure.sh --category Git
./scripts/tools/validation/validate-structure.sh --JSON --output results.JSON

```text

### **Quality Tools** (`scripts/tools/quality/`)

**Purpose**: Code quality checking, automated fixes, standards enforcement

**Available Tools**:

- `check-quality.sh` - Comprehensive quality validation with auto-fix capabilities

**Usage Example**:

```bash

## Instead of writing custom quality checks

./scripts/tools/quality/check-quality.sh --check Markdown --fix
./scripts/tools/quality/check-quality.sh --format JSON --report quality.JSON

```text

### **Repository Tools** (`scripts/tools/repository/`)

**Purpose**: Repository management, backup, organization

**Available Tools**:

- `backup-repository.sh` - Comprehensive repository backup and archiving

**Usage Example**:

```bash

## Instead of writing custom backup scripts

./scripts/tools/repository/backup-repository.sh

```text

### **Documentation Tools** (`scripts/tools/documentation/`)

**Purpose**: Documentation generation, maintenance, automation

**Available Tools**:

- `generate-docs.sh` - Automated documentation generation system

**Usage Example**:

```bash

## Instead of writing custom documentation generators

./scripts/tools/documentation/generate-docs.sh

```text

### **Deployment Tools** (`scripts/tools/deployment/`)

**Purpose**: Complete toolshed deployment to new repositories

**Available Tools**:

- `implement-toolshed.sh` - Deploy complete toolshed to any repository

**Usage Example**:

```bash

## Instead of manually copying tools

./scripts/tools/deployment/implement-toolshed.sh --category Git
./scripts/tools/deployment/implement-toolshed.sh --auto-commit

```text

### **Hooks & Automation Tools** (`scripts/tools/hooks/`)

**Purpose**: Pre-commit automation, quality gates, workflow automation

**Available Tools**:

- `setup-pre-commit.sh` - Comprehensive pre-commit hook configuration with multi-language support

**Usage Example**:

```bash

## Instead of writing custom pre-commit setups

./scripts/tools/hooks/setup-pre-commit.sh --languages Python,JavaScript
./scripts/tools/hooks/setup-pre-commit.sh --security-scanning --dry-run

```text

### **Security Tools** (`scripts/tools/security/`)

**Purpose**: Vulnerability scanning, security analysis, compliance checking

**Available Tools**:

- `security-scan.sh` - Comprehensive security scanning (SAST, dependency scanning, container security)

**Usage Example**:

```bash

## Instead of writing custom security scanners

./scripts/tools/security/security-scan.sh --sast-only
./scripts/tools/security/security-scan.sh --output JSON --severity high

```text

### **Dependency Management Tools** (`scripts/tools/dependencies/`)

**Purpose**: Package management, vulnerability monitoring, automated updates

**Available Tools**:

- `dependency-manager.sh` - Multi-language dependency management with security scanning

**Usage Example**:

```bash

## Instead of writing custom dependency tools

./scripts/tools/dependencies/dependency-manager.sh --update --strategy minor
./scripts/tools/dependencies/dependency-manager.sh --security-only --backup

```text

### **Performance Monitoring Tools** (`scripts/tools/monitoring/`)

**Purpose**: Application performance monitoring, system resource analysis

**Available Tools**:

- `performance-monitor.sh` - Comprehensive performance monitoring and profiling

**Usage Example**:

```bash

## Instead of writing custom monitoring scripts

./scripts/tools/monitoring/performance-monitor.sh --duration 300
./scripts/tools/monitoring/performance-monitor.sh --benchmark --report-only

```text

### **Container Management Tools** (`scripts/tools/containers/`)

**Purpose**: Docker container management, optimization, security

**Available Tools**:

- `Docker-manager.sh` - Complete Docker lifecycle management and optimization

**Usage Example**:

```bash

## Instead of writing custom Docker scripts

./scripts/tools/containers/Docker-manager.sh --build --security-scan
./scripts/tools/containers/Docker-manager.sh --optimize --cleanup

```text

### **Database Tools** (`scripts/tools/database/`)

**Purpose**: Database backup, optimization, health monitoring

**Available Tools**:

- `database-manager.sh` - Multi-database management (MySQL, PostgreSQL, MongoDB, SQLite)

**Usage Example**:

```bash

## Instead of writing custom database scripts

./scripts/tools/database/database-manager.sh --backup --type mysql
./scripts/tools/database/database-manager.sh --health-check --type postgresql

```text

- `implement-toolshed.sh` - Deploy complete toolshed to any repository

**Usage Example**:

```bash

## Instead of manually copying tools 2

./scripts/tools/implement-toolshed.sh --category Git
./scripts/tools/implement-toolshed.sh --auto-commit

```text

## 🎯 **Mandatory Usage Workflow**

### **Step 1: Always Check First**

```bash

## Before ANY script creation, check

ls scripts/tools/
cat scripts/tools/README.md
find scripts/tools/ -name "*.sh" -exec basename {} \;

```text

### **Step 2: Use Existing Tools**

```bash

## Example: Repository setup

./scripts/tools/Git/setup-repository.sh

## Example: Validation

./scripts/tools/validation/validate-structure.sh

## Example: Quality checking

./scripts/tools/quality/check-quality.sh --fix

```text

### **Step 3: Get Help for Any Tool**

```bash

## Every tool has comprehensive help

./scripts/tools/[category]/[tool-name].sh --help
./scripts/tools/[category]/[tool-name].sh --version

```text

### **Step 4: Extend, Don't Duplicate**

If existing tools don't meet requirements:

- **Extend existing tools** with new options
- **Follow established patterns** for new tools
- **Document new functionality** in the tool itself
- **Update the toolshed README** with new capabilities

## 🔍 **Tool Discovery Commands**

```bash

## List all available tools

find scripts/tools/ -name "*.sh" | sort

## Get summary of all tools

grep -r "^# Purpose:" scripts/tools/ | sed 's/.*://' | sort

## Check tool functionality

for tool in $(find scripts/tools/ -name "*.sh"); do
    echo "=== $tool ==="

    grep "^# Purpose:" "$tool" || echo "No description"
done

```text

## 📋 **Quality Standards for Tool Usage**

### **Required Checks Before Script Creation**

1. ✅ Checked `scripts/tools/README.md`
2. ✅ Searched existing tools with `find scripts/tools/ -name "_keyword_"`
3. ✅ Tested relevant tools with `--help`and`--dry-run`
4. ✅ Confirmed no existing tool meets the requirement
5. ✅ Planned to extend existing tool or follow patterns

### **Validation Commands**

```bash

## Verify toolshed is available

test -d scripts/tools && echo "✅ Toolshed available" || echo "❌ Toolshed missing"

## Count available tools

find scripts/tools/ -name "*.sh" | wc -l

## Validate tool execution

./scripts/tools/validation/validate-structure.sh --quick

```text

## 🚨 **Enforcement Policy**

### **MANDATORY Requirements**

1. **Pre-Creation Check**: Always check toolshed before writing scripts
2. **Use Existing Tools**: Utilize available tools when applicable
3. **Consistent Interface**: All tools support `--help`, `--verbose`, `--dry-run`
4. **Documentation**: Update README when extending or adding tools
5. **Quality Gates**: All tools must pass validation checks

### **Compliance Validation**

```bash

## Check if toolshed is being used properly

./scripts/tools/validation/validate-structure.sh
./scripts/tools/quality/check-quality.sh --check scripts

## Verify no duplicate functionality exists

grep -r "setup.*repository" scripts/ --exclude-dir=tools
grep -r "validate.*structure" scripts/ --exclude-dir=tools

```text

## 💡 **Best Practices for Agents**

### **Tool Selection Priority**

1. **First**: Use exact matching tool from toolshed
2. **Second**: Extend existing tool with new options
3. **Third**: Create new tool following established patterns
4. **Never**: Recreate functionality that exists in toolshed

### **Integration Patterns**

```bash

## Standard tool integration approach

if [[-f "scripts/tools/Git/setup-repository.sh"]]; then

## Use existing tool

    ./scripts/tools/Git/setup-repository.sh "$@"
else

## Fallback only if toolshed unavailable

    echo "Toolshed not available, implementing basic setup..."
fi

```text

## 📊 **Success Metrics**

### **Compliance Indicators**

- ✅ 100% toolshed awareness before script creation
- ✅ 90%+ reuse rate of existing tools
- ✅ Zero duplicate functionality across projects
- ✅ Consistent tool interfaces and quality

### **Quality Assurance**

- All agents check toolshed first
- Existing tools are extended rather than duplicated
- New tools follow established patterns
- Documentation is maintained and updated

## 🆘 **Quick Reference Card**

### **Essential Commands**

```bash

## ALWAYS RUN THESE FIRST

ls scripts/tools/                           # See available categories
cat scripts/tools/README.md                 # Read full tool catalog
./scripts/tools/implement-toolshed.sh --help  # Deploy to new repos

## CORE TOOLS

./scripts/tools/Git/setup-repository.sh     # Git setup
./scripts/tools/validation/validate-structure.sh  # Validation
./scripts/tools/quality/check-quality.sh    # Quality checks

```text

### **When in Doubt**

1. Check `scripts/tools/README.md`
2. Run `find scripts/tools/ -name "*.sh"`
3. Test with `--help` flag
4. Use `--dry-run` to preview changes

---

**This toolshed usage is MANDATORY for all GitHub Copilot agents to ensure efficient,
consistent, and high-quality automation across all projects.**
````
