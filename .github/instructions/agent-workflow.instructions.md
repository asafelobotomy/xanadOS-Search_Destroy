---
applyTo: "**/*"
priority: "critical"
enforcement: "mandatory"
---

# Agent Workflow and Quality Instructions - MANDATORY

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: ALL actions and tasks without exception
- **Compliance**: Required BEFORE any file creation, modification, or task execution
- **Philosophy**: **Quality over Speed - Thorough over Rushed**

## Executive Summary

All GitHub Copilot agents MUST follow a systematic **"Check First, Act Second"** workflow that prioritizes thoroughness, quality, and instruction compliance over speed. This prevents the common issues of rushing through tasks, creating redundant content, violating organizational policies, and making avoidable mistakes.

## 🚨 **CRITICAL DIRECTIVE: Systematic Workflow Enforcement**

**NO ACTIONS** may be taken until ALL relevant instructions have been read, understood, and validated. Agents must follow this mandatory workflow:

1. **📚 DISCOVERY PHASE** - Read ALL relevant instructions
2. **🔍 ANALYSIS PHASE** - Understand requirements and constraints
3. **✅ VALIDATION PHASE** - Verify planned actions against instructions
4. **🎯 EXECUTION PHASE** - Execute with full compliance
5. **🔄 VERIFICATION PHASE** - Confirm successful completion

## 🎯 **MANDATORY: Pre-Action Validation Workflow**

### **Phase 1: Comprehensive Instruction Discovery**

**BEFORE ANY ACTION**, agents MUST read and understand:

```bash
# Step 1: Check ALL instruction files that apply
find .github/instructions/ -name "*.instructions.md" | sort

# Step 2: Read file organization policy FIRST
cat .github/instructions/file-organization.instructions.md

# Step 3: Check toolshed for existing solutions
cat scripts/tools/README.md
find scripts/tools/ -name "*.sh"

# Step 4: Check documentation repository
cat docs/README.md
find docs/ -name "*.md"

# Step 5: Check archive for existing/deprecated content
cat archive/README.md
cat archive/ARCHIVE_INDEX.md
```

### **Phase 2: Requirements Analysis and Planning**

**MANDATORY QUESTIONS** to answer before proceeding:

1. **File Placement**: Where should this file/content be located according to file organization policy?
2. **Existing Solutions**: Does a tool, script, or documentation already exist in the repository?
3. **Instruction Compliance**: Which specific instructions apply to this task?
4. **Dependencies**: What other components or files does this affect?
5. **Quality Standards**: What validation and quality checks are required?

### **Phase 3: Action Validation Checklist**

**MANDATORY VALIDATION** before creating/modifying anything:

```bash
# File Placement Validation
echo "Planned file location: [PATH]"
echo "Checking against file organization policy..."
grep -A 20 "$(dirname [PATH])" .github/instructions/file-organization.instructions.md

# Existing Content Check
echo "Checking for existing solutions..."
find . -name "*similar-name*" -o -name "*related-keyword*"

# Instruction Compliance Check
echo "Verifying instruction compliance..."
ls .github/instructions/ | grep -E "($(echo [TASK_TYPE] | tr ' ' '|'))"

# Quality Standards Check
echo "Confirming quality requirements..."
cat .github/instructions/quality-standards.instructions.md
```

### **Phase 4: Execution with Documentation**

**MANDATORY EXECUTION STANDARDS**:

1. **Document Reasoning**: Explain WHY each action is being taken
2. **Reference Instructions**: Cite specific instruction files being followed
3. **Validate Continuously**: Check compliance at each step
4. **Update Indexes**: Maintain documentation and tool catalogs
5. **Test Thoroughly**: Verify functionality and compliance

### **Phase 5: Post-Action Verification**

**MANDATORY VERIFICATION** after completing any task:

```bash
# File Organization Compliance
echo "Verifying no root directory clutter..."
ls -la | grep -v "^[d-].*\(README\|CONTRIBUTING\|\.git\|\.editor\|\.prettier\|\.markdown\|package\)"

# Instruction Adherence
echo "Confirming all instructions were followed..."
# Review each instruction file that applied to the task

# Quality Standards Met
echo "Validating quality standards..."
./scripts/tools/validation/validate-structure.sh

# Documentation Updated
echo "Confirming documentation is current..."
# Verify indexes and catalogs are updated if needed
```

## 📋 **Common Workflow Violations and Solutions**

### **❌ VIOLATION: Root Directory Clutter**

**Problem**: Creating files like `DOCUMENTATION-REFERENCE.md` in root directory

**Solution**:
```bash
# ALWAYS check file organization policy FIRST
cat .github/instructions/file-organization.instructions.md
# THEN place files in appropriate directories:
# Documentation → docs/
# References → docs/guides/ or docs/references/
# Scripts → scripts/tools/
```

### **❌ VIOLATION: Recreating Existing Content**

**Problem**: Writing new scripts/docs when they already exist

**Solution**:
```bash
# ALWAYS check existing solutions FIRST
find scripts/tools/ -name "*.sh"
find docs/ -name "*.md"
grep -r "keyword" docs/ scripts/
# THEN extend existing content instead of recreating
```

### **❌ VIOLATION: Ignoring Instruction Files**

**Problem**: Acting without reading relevant instruction files

**Solution**:
```bash
# ALWAYS discover and read ALL relevant instructions FIRST
find .github/instructions/ -name "*$(task_type)*"
# READ each instruction file completely
# UNDERSTAND requirements and constraints
# THEN plan and execute with full compliance
```

### **❌ VIOLATION: Rushed Execution**

**Problem**: Skipping validation steps to complete tasks quickly

**Solution**:
- **Mindset Shift**: Quality and thoroughness are MORE valuable than speed
- **Systematic Approach**: Follow the 5-phase workflow without shortcuts
- **Validation First**: Always validate before acting, not after fixing mistakes

## 🛡️ **Quality-First Mindset Enforcement**

### **Core Principles**:

1. **Thoroughness Over Speed**: Taking time upfront prevents rework later
2. **Prevention Over Correction**: Follow instructions to avoid mistakes
3. **Systematic Over Reactive**: Use established workflows consistently
4. **Quality Over Quantity**: Better to do fewer things correctly than many things poorly

### **Success Metrics**:

- ✅ **Zero root directory violations** - All files in appropriate locations
- ✅ **Zero redundant content** - Use existing solutions, extend when needed
- ✅ **100% instruction compliance** - Follow ALL relevant policies
- ✅ **Comprehensive validation** - Complete workflow before execution
- ✅ **Quality documentation** - Thorough, well-organized, and maintained

## 🚨 **Enforcement Mechanisms**

### **Mandatory Pre-Action Commands**:

**EVERY agent MUST run these before ANY action:**

```bash
# 1. Instruction Discovery (MANDATORY)
echo "=== INSTRUCTION DISCOVERY ==="
find .github/instructions/ -name "*.instructions.md" | sort

# 2. File Organization Check (MANDATORY)
echo "=== FILE ORGANIZATION POLICY ==="
head -50 .github/instructions/file-organization.instructions.md

# 3. Existing Solutions Check (MANDATORY)
echo "=== EXISTING SOLUTIONS ==="
ls scripts/tools/
ls docs/guides/

# 4. Archive Check (MANDATORY)
echo "=== ARCHIVE AWARENESS ==="
head -20 archive/README.md
```

### **Validation Before Creation**:

```bash
# Before creating ANY file, validate:
echo "Planned file: $FILE_PATH"
echo "Checking organization policy compliance..."
dirname "$FILE_PATH" | grep -E "(docs|scripts|.github|archive|examples)"
echo "Result: $(test $? -eq 0 && echo "✅ COMPLIANT" || echo "❌ VIOLATION")"
```

### **Quality Gates**:

- **Gate 1**: All relevant instructions read and understood
- **Gate 2**: File placement validated against organization policy
- **Gate 3**: Existing solutions checked and considered
- **Gate 4**: Action plan validated for compliance
- **Gate 5**: Execution documented with reasoning
- **Gate 6**: Results verified for quality and compliance

## 💡 **Best Practices for Agent Excellence**

### **Discovery Phase Best Practices**:

1. **Read Completely**: Don't skim instruction files, read them entirely
2. **Understand Context**: Know WHY each instruction exists
3. **Check Dependencies**: Understand how instructions relate to each other
4. **Plan Thoroughly**: Design complete approach before starting

### **Execution Phase Best Practices**:

1. **Document Reasoning**: Explain decision-making process
2. **Reference Instructions**: Cite specific policies being followed
3. **Validate Continuously**: Check compliance at each step
4. **Maintain Quality**: Prioritize excellence over completion speed

### **Verification Phase Best Practices**:

1. **Test Thoroughly**: Verify all functionality works correctly
2. **Check Compliance**: Confirm all instructions were followed
3. **Update Documentation**: Maintain current indexes and catalogs
4. **Plan Maintenance**: Consider ongoing upkeep requirements

## 🆘 **Agent Self-Assessment Checklist**

**Before considering any task "complete", agents MUST confirm:**

- [ ] **Read ALL relevant instruction files completely**
- [ ] **Validated file placement against organization policy**
- [ ] **Checked for existing solutions in toolshed and docs**
- [ ] **Followed systematic 5-phase workflow**
- [ ] **Documented reasoning and instruction compliance**
- [ ] **Verified quality standards and functionality**
- [ ] **Updated appropriate indexes and documentation**
- [ ] **Confirmed zero policy violations**

## 🎯 **Success Indicators**

### **Agent Behavior Changes**:

- Agents read instructions BEFORE acting, not while fixing problems
- File placement follows organization policy without exceptions
- Existing solutions are discovered and used appropriately
- Quality and thoroughness are prioritized over speed
- Systematic workflows are followed consistently

### **Repository Quality Improvements**:

- Zero root directory clutter from new agent actions
- No redundant documentation or scripts created
- All content properly organized and discoverable
- Complete compliance with all instruction files
- High-quality, maintainable, and consistent results

---

**This workflow framework is MANDATORY for all GitHub Copilot agents to ensure systematic, quality-focused, and instruction-compliant development practices.**

```bash
# 1. Instruction Discovery (MANDATORY)
echo "=== INSTRUCTION DISCOVERY ==="
find .github/instructions/ -name "*.instructions.md" | sort

# 2. File Organization Check (MANDATORY)
echo "=== FILE ORGANIZATION POLICY ==="
head -50 .github/instructions/file-organization.instructions.md

# 3. Existing Solutions Check (MANDATORY)
echo "=== EXISTING SOLUTIONS ==="
ls scripts/tools/
ls docs/guides/

# 4. Archive Check (MANDATORY)
echo "=== ARCHIVE AWARENESS ==="
head -20 archive/README.md
```

### **Validation Before Creation**:

```bash
# Before creating ANY file, validate:
echo "Planned file: $FILE_PATH"
echo "Checking organization policy compliance..."
dirname "$FILE_PATH" | grep -E "(docs|scripts|.github|archive|examples)"
echo "Result: $(test $? -eq 0 && echo "✅ COMPLIANT" || echo "❌ VIOLATION")"
```

### **Quality Gates**:

- **Gate 1**: All relevant instructions read and understood
- **Gate 2**: File placement validated against organization policy
- **Gate 3**: Existing solutions checked and considered
- **Gate 4**: Action plan validated for compliance
- **Gate 5**: Execution documented with reasoning
- **Gate 6**: Results verified for quality and compliance

## 💡 **Best Practices for Agent Excellence**

### **Discovery Phase Best Practices**:

1. **Read Completely**: Don't skim instruction files, read them entirely
2. **Understand Context**: Know WHY each instruction exists
3. **Check Dependencies**: Understand how instructions relate to each other
4. **Plan Thoroughly**: Design complete approach before starting

### **Execution Phase Best Practices**:

1. **Document Reasoning**: Explain decision-making process
2. **Reference Instructions**: Cite specific policies being followed
3. **Validate Continuously**: Check compliance at each step
4. **Maintain Quality**: Prioritize excellence over completion speed

### **Verification Phase Best Practices**:

1. **Test Thoroughly**: Verify all functionality works correctly
2. **Check Compliance**: Confirm all instructions were followed
3. **Update Documentation**: Maintain current indexes and catalogs
4. **Plan Maintenance**: Consider ongoing upkeep requirements

## 🆘 **Agent Self-Assessment Checklist**

**Before considering any task "complete", agents MUST confirm:**

- [ ] **Read ALL relevant instruction files completely**
- [ ] **Validated file placement against organization policy**
- [ ] **Checked for existing solutions in toolshed and docs**
- [ ] **Followed systematic 5-phase workflow**
- [ ] **Documented reasoning and instruction compliance**
- [ ] **Verified quality standards and functionality**
- [ ] **Updated appropriate indexes and documentation**
- [ ] **Confirmed zero policy violations**

## 🎯 **Success Indicators**

### **Agent Behavior Changes**:

- Agents read instructions BEFORE acting, not while fixing problems
- File placement follows organization policy without exceptions
- Existing solutions are discovered and used appropriately
- Quality and thoroughness are prioritized over speed
- Systematic workflows are followed consistently

### **Repository Quality Improvements**:

- Zero root directory clutter from new agent actions
- No redundant documentation or scripts created
- All content properly organized and discoverable
- Complete compliance with all instruction files
- High-quality, maintainable, and consistent results

---

**This workflow framework is MANDATORY for all GitHub Copilot agents to ensure systematic, quality-focused, and instruction-compliant development practices.**
