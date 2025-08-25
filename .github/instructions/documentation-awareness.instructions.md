---
applyTo: "docs/**"
priority: "critical"
enforcement: "mandatory"

---

# Documentation Awareness Instructions - MANDATORY

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: All documentation creation and maintenance tasks
- **Compliance**: Required before creating any documentation
- **Review Cycle**: Check existing documentation first, always

## Executive Summary

All GitHub Copilot agents MUST check and utilize the existing comprehensive
documentation system in `/docs/` before creating any documentation files. This
prevents redundant documentation creation, ensures consistency, and maintains
quality standards across all projects.

## 🚨 **CRITICAL DIRECTIVE: Check Documentation Repository First**

Before writing ANY documentation, guides, or README files, agents MUST:

1. **Check `/docs/README.md`** for existing documentation index
2. **Search the documentation system** for similar content
3. **Use existing documentation** when available
4. **Update existing documentation** rather than creating duplicates
5. **Follow established patterns** for any new documentation

## 📁 **Available Documentation Repository**

### **Core Documentation Structure** (`/docs/`)

**Purpose**: Comprehensive documentation system with enterprise-grade organization

**Available Categories**:

- `/docs/guides/` - User guides and setup instructions (6 comprehensive guides)
- `/docs/implementation-reports/` - Technical implementation documentation
- `/docs/ORGANIZATION.md` - Repository organization standards
- `/docs/REPOSITORY_ORGANIZATION.md` - Detailed structure documentation

**Usage Example**:

```bash

## Instead of writing custom documentation

ls /docs/
cat /docs/README.md                          # Documentation index
ls /docs/guides/                             # Available user guides

```text

### **User Guides** (`/docs/guides/`)

**Purpose**: Comprehensive user and developer guidance

**Available Guides**:

- `ENHANCEMENTS.md` - Framework features and capabilities overview
- `MCP.md` - Model Context Protocol integration guide
- `model-targeting-guide.md` - Advanced AI model targeting (GPT-5, Claude Sonnet 4, Gemini Pro)
- `organization-custom-instructions.md` - Enterprise deployment and organization setup
- `INSTALL_LINKS.md` - VS Code extension installation and integration
- `PROJECT_STRUCTURE.md` - Repository organization and structure guide

**Usage Example**:

```bash

## Instead of writing custom user guides

cat /docs/guides/ENHANCEMENTS.md             # Framework overview
cat /docs/guides/model-targeting-guide.md    # AI model guidance
cat /docs/guides/organization-custom-instructions.md  # Enterprise setup

```text

### **GitHub Templates** (`/.GitHub/`)

**Purpose**: Specialized AI interaction templates and instructions

**Available Templates**:

- `chatmodes/` - 11 specialized AI conversation modes
- `prompts/` - 7 professional prompt templates
- `instructions/` - 6+ advanced instruction sets

**Usage Example**:

```bash

## Instead of creating custom templates

ls .GitHub/chatmodes/                        # Available chat modes
ls .GitHub/prompts/                          # Professional prompts
ls .GitHub/instructions/                     # Instruction files

```text

### **Archive System** (`/archive/`)

**Purpose**: Historical documentation and version management

**Available Archives**:

- `deprecated/` - Deprecated documentation with migration guides
- `legacy-versions/` - Previous versions for reference
- `superseded/` - Replaced documentation with transition guides

**Usage Example**:

```bash

## Instead of recreating historical documentation

cat /archive/README.md                       # Archive policy
cat /archive/ARCHIVE_INDEX.md                # Content inventory

```text

## 🎯 **MANDATORY: Documentation Discovery Workflow**

### **Step 1: Always Check Documentation Repository First**

```bash

## Before ANY documentation creation, check

ls /docs/
cat /docs/README.md
find /docs/ -name "*.md" -exec basename {} \;

```text

### **Step 2: Search for Existing Content**

```bash

## Search for similar documentation

grep -r "keyword" /docs/
find /docs/ -name "_keyword_"
find .GitHub/ -name "_topic_"

```text

### **Step 3: Use Existing Documentation**

```bash

## Example: Framework overview

cat /docs/guides/ENHANCEMENTS.md

## Example: Project structure

cat /docs/guides/PROJECT_STRUCTURE.md

## Example: Organization setup

cat /docs/guides/organization-custom-instructions.md

```text

### **Step 4: Update, Don't Duplicate**

If existing documentation needs enhancement:

- **Update existing files** with new information
- **Extend established sections** with additional details
- **Follow established formatting** and structure
- **Maintain consistency** with existing documentation

## 🔍 **Documentation Discovery Commands**

```bash

## List all available documentation

find /docs/ -name "*.md" | sort

## Get summary of all documentation topics

grep -r "^# " /docs/ | sed 's/.*://' | sort

## Check documentation coverage

for doc in $(find /docs/ -name "*.md"); do
    echo "=== $doc ==="

    head -5 "$doc" | grep "^#" || echo "No clear title"
done

```text

## 📋 **Quality Standards for Documentation Usage**

### **Required Checks Before Documentation Creation**

1. ✅ Checked `/docs/README.md` documentation index
2. ✅ Searched existing guides with `find /docs/guides/ -name "_keyword_"`
3. ✅ Reviewed relevant templates in `.GitHub/` directories
4. ✅ Confirmed no existing documentation covers the topic
5. ✅ Planned to update existing documentation or follow patterns

### **Validation Commands**

```bash

## Verify documentation repository is available

test -d /docs && echo "✅ Documentation repository available" || echo "❌ Documentation missing"

## Count available documentation

find /docs/ -name "*.md" | wc -l

## Validate documentation organization

ls -la /docs/guides/ /docs/implementation-reports/

```text

## 🚨 **Enforcement Policy**

### **MANDATORY Requirements**

1. **Pre-Creation Check**: Always check documentation repository before writing docs
2. **Use Existing Documentation**: Utilize available guides when applicable
3. **Consistent Formatting**: All documentation follows established patterns
4. **Update Documentation Index**: Update `/docs/README.md` when adding new docs
5. **Quality Standards**: All documentation must meet enterprise standards

### **Compliance Validation**

```bash

## Check if documentation repository is being used properly

ls -la /docs/
wc -l /docs/README.md

## Verify no duplicate documentation exists

find . -name "README.md" -not -path "./docs/_" -not -path "./.GitHub/_"
find . -name "_guide_" -not -path "./docs/guides/*"

```text

## 💡 **Best Practices for Agents**

### **Documentation Selection Priority**

1. **First**: Use exact matching documentation from `/docs/guides/`
2. **Second**: Update existing documentation with new information
3. **Third**: Create new documentation following established patterns
4. **Never**: Recreate documentation that exists in the repository

### **Integration Patterns**

```bash

## Standard documentation integration approach

if [[-f "/docs/guides/topic-guide.md"]]; then

## Use existing documentation

    echo "Using existing guide: /docs/guides/topic-guide.md"
    cat /docs/guides/topic-guide.md
else

## Create following established patterns

    echo "Creating new documentation following patterns..."
    cp /docs/guides/template.md /docs/guides/new-topic.md
fi

```text

## 📊 **Success Metrics**

### **Compliance Indicators**

- ✅ 100% documentation awareness before content creation
- ✅ 90%+ reuse rate of existing documentation
- ✅ Zero duplicate documentation across projects
- ✅ Consistent documentation quality and formatting

### **Quality Assurance**

- All agents check documentation repository first
- Existing documentation is updated rather than duplicated
- New documentation follows established patterns
- Documentation index is maintained and updated

## 🆘 **Quick Reference Card**

### **Essential Commands**

```bash

## ALWAYS RUN THESE FIRST

ls /docs/                                    # See available documentation
cat /docs/README.md                          # Read full documentation index
find /docs/guides/ -name "*.md"              # List all user guides

## CORE DOCUMENTATION

cat /docs/guides/ENHANCEMENTS.md             # Framework overview
cat /docs/guides/PROJECT_STRUCTURE.md        # Repository structure
cat /docs/guides/organization-custom-instructions.md  # Enterprise setup

```text

### **When in Doubt**

1. Check `/docs/README.md` for documentation index
2. Run `find /docs/ -name "_keyword_"`
3. Review existing guides for similar content
4. Update existing documentation instead of creating new

## 🎯 **Available Documentation Catalog**

### **Framework Documentation**

- **Framework Overview**: `/docs/guides/ENHANCEMENTS.md` (comprehensive features and capabilities)
- **Project Structure**: `/docs/guides/PROJECT_STRUCTURE.md` (repository organization guide)
- **Organization Setup**: `/docs/guides/organization-custom-instructions.md` (enterprise deployment)

### **Integration Documentation**

- **MCP Integration**: `/docs/guides/MCP.md` (Model Context Protocol setup)
- **VS Code Integration**: `/docs/guides/INSTALL_LINKS.md` (extension installation)
- **AI Model Targeting**: `/docs/guides/model-targeting-guide.md` (GPT-5, Claude, Gemini)

### **Template Documentation**

- **Chat Modes**: `/.GitHub/chatmodes/` (11 specialized AI interaction modes)
- **Prompt Templates**: `/.GitHub/prompts/` (7 professional prompt templates)
- **Instructions**: `/.GitHub/instructions/` (6+ advanced instruction sets)

### **Archive Documentation**

- **Archive Policy**: `/archive/README.md` (comprehensive archive management)
- **Content Index**: `/archive/ARCHIVE_INDEX.md` (complete content inventory)
- **Migration Guides**: `/archive/*/README.md` (transition procedures)

### **Organizational Documentation**

- **Repository Organization**: `/docs/REPOSITORY_ORGANIZATION.md` (detailed structure)
- **Organization Standards**: `/docs/ORGANIZATION.md` (enterprise standards)
- **Implementation Reports**: `/docs/implementation-reports/` (technical documentation)

---

**This documentation awareness is MANDATORY for all GitHub Copilot agents to
ensure efficient, consistent, and high-quality documentation across all
projects.**
