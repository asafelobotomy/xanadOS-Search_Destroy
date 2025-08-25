# Validation Configuration

## Overview

This directory contains configuration files for the meta-instruction validation framework.
These configurations define validation rules, quality standards, and compliance requirements for GitHub Copilot instructions.

## Configuration Files

### validation-rules.JSON

Defines the core validation rules and their parameters:

- **Structural Rules**: File organization and template compliance
- **Content Quality Rules**: Clarity, completeness, and documentation standards
- **Integration Rules**: MCP compatibility and cross-reference validation
- **Performance Rules**: File size limits and complexity metrics

### quality-standards.JSON

Establishes quality benchmarks and scoring criteria:

- **Minimum Quality Scores**: Threshold values for passing validation
- **Weighting Factors**: Importance weights for different validation categories
- **Exception Rules**: Special cases and exclusions
- **Severity Levels**: Classification of issues by impact

### compliance-requirements.JSON

Specifies compliance requirements for different file types:

- **Template Requirements**: Mandatory sections and formatting
- **Naming Conventions**: File and directory naming standards
- **Documentation Standards**: Required documentation elements
- **Code Quality Standards**: Coding best practices and patterns

## Usage

The validation framework automatically loads these configuration files during execution.
You can customize the validation behavior by modifying these files according to your project requirements.

### Customization Guidelines

1. **Maintain Backward Compatibility**: Ensure changes don't break existing validations
2. **Document Changes**: Update comments and descriptions when modifying rules
3. **Test Thoroughly**: Validate configuration changes before deployment
4. **Version Control**: Track configuration changes through Git history

## Environment-Specific Configurations

Different environments may require different validation settings:

- **Development**: More lenient rules for rapid iteration
- **Staging**: Standard quality requirements with warnings
- **Production**: Strict validation with no tolerance for errors

Use environment variables or separate configuration files to manage these differences.
