# Documentation Directory Policy (/docs/) - MANDATORY

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: All repositories with documentation content
- **Compliance**: Required for repository standardization
- **Review Cycle**: Quarterly assessment and updates

## Executive Summary

This policy establishes comprehensive standards for `/docs/` directory organization based on GitHub best practices, Microsoft documentation architecture, and modern documentation platform standards. All GitHub Copilot agents MUST implement and maintain these standards in any repository containing documentation.

## Directory Structure Standards

### Primary Structure

```text
/docs/
├── README.md                          # Documentation overview and navigation
├── guides/                           # User-facing documentation
│   ├── quick-start.md
│   ├── installation.md
│   ├── user-guide.md
│   ├── troubleshooting.md
│   └── faq.md
├── api/                              # API documentation
│   ├── reference/
│   ├── examples/
│   └── changelogs/
├── development/                      # Developer documentation
│   ├── contributing.md
│   ├── setup.md
│   ├── architecture.md
│   └── coding-standards.md
├── tutorials/                        # Step-by-step learning content
│   ├── beginner/
│   ├── intermediate/
│   └── advanced/
├── reference/                        # Technical reference materials
│   ├── configuration.md
│   ├── commands.md
│   └── glossary.md
├── assets/                          # Documentation media
│   ├── images/
│   ├── videos/
│   └── diagrams/
├── templates/                       # Documentation templates
│   ├── issue-template.md
│   ├── pr-template.md
│   └── documentation-template.md
└── _archive/                        # Historical documentation
    ├── deprecated/
    └── legacy-versions/
```markdown

### Content Type Categories

#### 1. Conceptual Documentation

- **Purpose**: Explain what and why
- **Location**: `/docs/guides/`
- **Format**: Narrative explanations, overviews
- **Examples**: Architecture overviews, concept explanations

#### 2. Procedural Documentation

- **Purpose**: Step-by-step instructions
- **Location**: `/docs/tutorials/` or `/docs/guides/`
- **Format**: Numbered steps, clear actions
- **Examples**: Installation guides, setup procedures

#### 3. Reference Documentation

- **Purpose**: Quick lookup information
- **Location**: `/docs/reference/` or `/docs/api/`
- **Format**: Tables, lists, specifications
- **Examples**: API references, configuration options

#### 4. Troubleshooting Documentation

- **Purpose**: Problem resolution
- **Location**: `/docs/guides/troubleshooting.md`
- **Format**: Problem-solution pairs
- **Examples**: Error codes, common issues

#### 5. Tutorial Documentation

- **Purpose**: Learning-oriented guidance
- **Location**: `/docs/tutorials/`
- **Format**: Progressive skill building
- **Examples**: Getting started, advanced workflows

## File Naming Standards

### Naming Conventions

- Use lowercase with hyphens: `installation-guide.md`
- Be descriptive and specific: `api-authentication.md`
- Avoid abbreviations: `frequently-asked-questions.md` not `faq.md`
- Include version when applicable: `v2-migration-guide.md`

### File Extensions

- Documentation: `.md` (Markdown primary format)
- Configuration examples: `.yml`, `.json`, `.xml`
- Code examples: Language-appropriate extensions
- Images: `.png`, `.jpg`, `.svg` (prefer SVG for diagrams)

## Implementation Requirements

### For GitHub Copilot Agents

1. **Immediate Compliance**
   - Assess current documentation structure
   - Implement required directory organization
   - Apply naming convention standards
   - Establish quality processes

2. **Ongoing Responsibilities**
   - Maintain structure standards
   - Enforce naming conventions
   - Monitor content quality
   - Execute archive procedures

3. **Reporting Requirements**
   - Document compliance status
   - Report structure violations
   - Track quality metrics
   - Maintain audit trails

### Repository Assessment Checklist

- [ ] `/docs/` directory exists and follows structure
- [ ] All documentation files use proper naming conventions
- [ ] README.md provides clear navigation
- [ ] Content types are properly categorized
- [ ] Quality standards are implemented
- [ ] Archive integration is functional
- [ ] Workflow processes are documented
- [ ] Validation tools are configured

## Related Policies

- Archive Management Policy: `.github/instructions/archive-policy.instructions.md`
- Security Guidelines: `.github/instructions/security.instructions.md`
- Testing Standards: `.github/instructions/testing.instructions.md`

## Policy Metadata

- **Created**: Current implementation date
- **Last Updated**: Current date
- **Version**: 1.0
- **Next Review**: Quarterly
- **Enforcement**: Mandatory for all GitHub Copilot agents
- **Compliance Tracking**: Required in all repository assessments

---

**ENFORCEMENT NOTICE**: This policy is MANDATORY for all GitHub Copilot agents. Non-compliance will result in repository standardization requirements and additional oversight procedures. All documentation work must follow these standards without exception.
