# MANDATORY ARCHIVE POLICY FOR ALL Copilot AGENTS

## 🚨 ENFORCEMENT NOTICE

## This archive policy is MANDATORY for all GitHub Copilot agents working on repository organization and management tasks

## 📋 Policy Overview

All Copilot agents must implement comprehensive `/archive/` directory structures following these standardized best practices when organizing or restructuring repositories.

## ✅ MANDATORY REQUIREMENTS

### 1. Archive Directory Structure

**REQUIRED**: Every repository MUST include a `/archive/` directory with the following structure:

```Markdown
archive/
├── README.md                   # Archive policy and documentation
├── ARCHIVE_INDEX.md           # Comprehensive content index
├── deprecated/                # Deprecated content archive
│   ├── README.md             # Deprecation guidelines
│   └── [YYYY-MM-DD]/         # Date-organized deprecated content
├── legacy-versions/          # Previous version archive
│   ├── README.md            # Version management guidelines
│   └── [vX.Y.Z]/            # Version-organized legacy content
└── superseded/              # Replaced content archive
    ├── README.md           # Supersession guidelines
    └── [YYYY-MM-DD]/       # Date-organized superseded content
```Markdown

### 2. Archive Documentation

**REQUIRED**: All archive directories MUST include:

- Comprehensive README.md with usage guidelines
- ARCHIVE_INDEX.md with complete content inventory
- Category-specific README files in each subdirectory
- Metadata files for all archived content

### 3. Archive Classification System

**REQUIRED**: All archived content MUST be classified as:

- **Deprecated**: No longer maintained, scheduled for removal
- **Legacy Version**: Previous versions of current files
- **Superseded**: Completely replaced by new implementations

### 4. Metadata Standards

**REQUIRED**: All archived content MUST include YAML frontmatter with:

```YAML
---
archived_date: "YYYY-MM-DD"
archive_reason: "Detailed reason for archiving"
replacement: "Path to replacement or 'none'"
retention_period: "X years or 'permanent'"

archive_type: "deprecated|legacy-version|superseded"
original_location: "Original file path"

migration_guide: "Path to migration documentation"
---
```Markdown

### 5. Retention Policies

**REQUIRED**: Implement standardized retention schedules:

- **Deprecated**: Minimum 1 year, review annually
- **Legacy Versions**: Major versions permanent, minor versions 2 years
- **Superseded**: 3 years from supersession date

## 🔧 IMPLEMENTATION REQUIREMENTS

### Archive Creation Process

1. **Create Archive Structure**: Implement complete directory hierarchy
2. **Document Policies**: Create comprehensive documentation
3. **Establish Metadata**: Define content classification system
4. **Setup Maintenance**: Plan regular archive reviews and cleanup

### Content Migration Process

1. **Assess Content**: Identify files requiring archival
2. **Classify Appropriately**: Use correct archive category
3. **Add Metadata**: Include comprehensive archival information
4. **Update References**: Remove or redirect active links
5. **Validate Archive**: Ensure no broken references remain

### Quality Assurance Checklist

- [ ] Archive directory structure complete
- [ ] All documentation files present
- [ ] Metadata format standardized
- [ ] Content properly classified
- [ ] Retention policies documented
- [ ] Migration guides provided
- [ ] Index files maintained
- [ ] References updated

## 📊 COMPLIANCE MONITORING

### Agent Responsibilities

All Copilot agents MUST:

- Implement complete archive structure before finalizing repository organization
- Follow standardized naming conventions and metadata formats
- Provide comprehensive documentation for all archived content
- Maintain archive indices and navigation aids
- Ensure compliance with retention and security policies

### Validation Requirements

Before completing any repository organization task:

- [ ] Archive structure validates against standards
- [ ] All required documentation present
- [ ] Metadata format compliance verified
- [ ] Content classification accuracy confirmed
- [ ] Retention policies properly implemented

## 🎯 STANDARDIZED TEMPLATES

### Archive README Template

Use the comprehensive README template provided in `/archive/README.md`

### Index Template

Follow the structure defined in `/archive/ARCHIVE_INDEX.md`

### Metadata Template

```YAML
---
archived_date: "YYYY-MM-DD"
archive_reason: "Specific reason for archiving"
replacement: "Path to replacement or 'none'"
retention_period: "Duration or 'permanent'"

archive_type: "deprecated|legacy-version|superseded"
original_location: "Original file path"

dependencies: ["list", "of", "dependent", "files"]
migration_guide: "Path to migration documentation"
security_considerations: "Any security implications"
compliance_notes: "Regulatory or legal considerations"
---
```Markdown

## 🚀 ENTERPRISE STANDARDS

### Professional Implementation

- Follow GitHub best practices for archive organization
- Implement enterprise-grade content lifecycle management
- Ensure compliance with industry standards and regulations
- Provide comprehensive documentation and navigation aids

### Scalability Requirements

- Design for long-term content growth
- Implement efficient search and discovery mechanisms
- Plan for automated maintenance and cleanup procedures
- Support enterprise compliance and audit requirements

## 📞 SUPPORT AND ESCALATION

### Policy Questions

For questions about archive policy implementation:

1. Review this mandatory policy document
2. Check provided templates and examples
3. Validate against enterprise requirements
4. Escalate to senior agents for complex scenarios

### Implementation Issues

If unable to implement complete archive structure:

1. Document specific constraints or limitations
2. Implement maximum possible compliance
3. Note deviations from standard in documentation
4. Plan future compliance upgrades

## ⚖️ POLICY ENFORCEMENT

### Compliance Requirements

- **100% Compliance**: All repository organization tasks must include archive implementation
- **No Exceptions**: Archive structure is non-negotiable for professional repositories
- **Quality Standards**: All archives must meet documented quality requirements
- **Documentation Standards**: Comprehensive documentation is mandatory

### Audit and Review

- Regular compliance audits will be conducted
- Archive implementations will be validated against standards
- Non-compliant implementations must be corrected
- Best practices will be continuously updated and enforced

---

## This policy ensures consistent, professional, and enterprise-ready archive implementation across all Copilot agent repository organization tasks

Compliance is mandatory and non-negotiable.

## POLICY VERSION: 1.0

## EFFECTIVE DATE: 2025-08-22

## MANDATORY COMPLIANCE: ALL Copilot AGENTS

## MANDATORY COMPLIANCE: ALL Copilot AGENTS 2
