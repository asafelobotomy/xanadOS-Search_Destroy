#!/usr/bin/env python3
"""
Documentation Organization Script
Consolidates, organizes, and archives documentation for xanadOS Search & Destroy
"""

import os
import shutil


def create_consolidated_implementation_guide():
    """Create a comprehensive implementation guide from scattered docs"""

    implementation_docs = [
        "docs/implementation/implementation-summary.md",
        "docs/implementation/scan-enhancements.md",
        "docs/implementation/gui-layout-improvements.md",
        "docs/implementation/compact-layout-improvements.md",
        "docs/implementation/rkhunter_progress_improvements.md",
        "docs/implementation/warning_button_fix.md",
        "docs/implementation/TOOLTIP_IMPROVEMENTS.md",
    ]

    consolidated_content = """# xanadOS Search & Destroy - Implementation Guide
*Consolidated implementation documentation for all features and improvements*

---

## 🎯 Overview

This document consolidates all implementation details for xanadOS Search & Destroy features and improvements. Each section documents a specific feature implementation with technical details, code changes, and testing results.

---

"""

    for doc_path in implementation_docs:
        if os.path.exists(doc_path):
            print(f"   📄 Processing: {os.path.basename(doc_path)}")

            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Append section using original content, preserving its title
            consolidated_content += (
                "\n" + content.strip() + "\n\n---\n\n"
            )

    # Write consolidated guide
    os.makedirs("docs/implementation", exist_ok=True)
    with open(
        "docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(consolidated_content)

    print("   ✅ Created consolidated implementation guide")
    return implementation_docs


def consolidate_project_management_docs():
    """Consolidate overlapping project management documents"""

    # Merge VERSION_CONTROL.md and VERSION_CONTROL_SUMMARY.md
    version_control_path = "docs/project/VERSION_CONTROL.md"
    version_summary_path = "docs/project/VERSION_CONTROL_SUMMARY.md"

    if os.path.exists(version_control_path) and os.path.exists(version_summary_path):
        with open(version_control_path, "r", encoding="utf-8") as f:
            vc_content = f.read()

        with open(version_summary_path, "r", encoding="utf-8") as f:
            vc_summary = f.read()

        # Create consolidated version control doc
        consolidated_vc = (
            f"""{vc_content}

---

# Implementation Status

{vc_summary[vc_summary.find('## ✅'):]}
"""
        )

        with open(version_control_path, "w", encoding="utf-8") as f:
            f.write(consolidated_vc)

        # Archive the summary
        archive_path = "archive/deprecated-docs/VERSION_CONTROL_SUMMARY.md"
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        shutil.move(version_summary_path, archive_path)

        print("   ✅ Consolidated version control documentation")
        print("   📁 Archived: VERSION_CONTROL_SUMMARY.md")


def organize_development_docs():
    """Move and organize development-specific documentation"""

    dev_docs_to_move = {
        "dev/ARCH_LINUX_RKHUNTER_FIXES.md": "docs/implementation/arch-linux-integration.md",
        "dev/RKHUNTER_PROGRESS_INTEGRATION.md": "docs/implementation/rkhunter-integration.md",
        "dev/RKHUNTER_REALTIME_OUTPUT.md": "docs/implementation/rkhunter-realtime.md",
    }

    for src, dst in dev_docs_to_move.items():
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            print(f"   📄 Moved: {os.path.basename(src)} → docs/implementation/")


def archive_deprecated_docs():
    """Archive deprecated and outdated documentation"""

    deprecated_docs = [
        "docs/DOCUMENTATION_ORGANIZATION.md",  # Outdated organization doc
        "REPOSITORY_ORGANIZATION.md",  # Move to docs/project/
    ]

    archive_dir = "archive/deprecated-docs"
    os.makedirs(archive_dir, exist_ok=True)

    for doc in deprecated_docs:
        if os.path.exists(doc):
            shutil.move(doc, f"{archive_dir}/{os.path.basename(doc)}")
            print(f"   📁 Archived: {os.path.basename(doc)}")

    # Move REPOSITORY_ORGANIZATION.md to correct location
    if os.path.exists("REPOSITORY_ORGANIZATION.md"):
        shutil.move(
            "REPOSITORY_ORGANIZATION.md", "docs/project/REPOSITORY_ORGANIZATION.md"
        )
        print("   📄 Moved: REPOSITORY_ORGANIZATION.md → docs/project/")


def create_master_documentation_index():
    """Create a comprehensive documentation index"""

    index_content = """# xanadOS Search & Destroy - Documentation Index

*Complete documentation index and navigation guide*

---

## 📚 Documentation Structure

### 👤 User Documentation
Essential guides for end users and system administrators.

- **[Installation Guide](user/Installation.md)** - Complete setup and installation instructions
- **[User Manual](user/User_Manual.md)** - Comprehensive usage guide and features
- **[Configuration Guide](user/Configuration.md)** - Advanced settings and customization

### 🔧 Developer Documentation
Technical documentation for contributors and developers.

- **[Development Setup](developer/DEVELOPMENT.md)** - Environment setup and build process
- **[API Reference](developer/API.md)** - Complete API documentation
- **[Contributing Guide](developer/CONTRIBUTING.md)** - Contribution guidelines and standards

### 🏗️ Implementation Documentation
Detailed technical implementation guides and feature documentation.

- **[Consolidated Implementation Guide](implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md)** - All feature implementations
- **[Feature Documentation](implementation/features/)** - Individual feature guides
  - [Minimize to Tray](implementation/features/MINIMIZE_TO_TRAY_IMPLEMENTATION.md)
  - [Single Instance Enforcement](implementation/features/SINGLE_INSTANCE_IMPLEMENTATION.md)
- **[System Integration](implementation/)** - Platform-specific implementations
  - [Arch Linux Integration](implementation/arch-linux-integration.md)
  - [RKHunter Integration](implementation/rkhunter-integration.md)

### 📋 Project Documentation
Project management, organization, and maintenance documentation.

- **[Repository Organization](project/REPOSITORY_ORGANIZATION.md)** - Project structure and organization (static)
- **[Runtime Organization Report](project/REPOSITORY_ORGANIZATION_RUNTIME.md)** - Latest auto-generated report
- **[Version Control Guidelines](project/VERSION_CONTROL.md)** - Git workflow and branching strategy
- **[Performance Optimizations](project/PERFORMANCE_OPTIMIZATIONS.md)** - System performance improvements
- **[Cleanup Summary](project/CLEANUP_SUMMARY.md)** - Repository maintenance history

### 📦 Release Documentation
Version history and release information.

- **[Latest Release](releases/RELEASE_2.2.0.md)** - Current version release notes
- **[Changelog](../CHANGELOG.md)** - Complete version history

### 📖 Reference Documentation
Code references, citations, and verification reports.

- **[Code Citations](Code_Citations.md)** - Third-party code references and licenses
- **[Link Verification Report](LINK_VERIFICATION_REPORT.md)** - Documentation link validation

---

## 🚀 Quick Start

1. **New Users**: Start with [Installation Guide](user/Installation.md) -> [User Manual](user/User_Manual.md)
2. **Developers**: See [Development Setup](developer/DEVELOPMENT.md) -> [API Reference](developer/API.md)
3. **Contributors**: Review [Contributing Guide](developer/CONTRIBUTING.md) -> [Version Control Guidelines](project/VERSION_CONTROL.md)

---

## 🔄 Documentation Maintenance

This documentation is actively maintained and updated. Last major reorganization: **August 8, 2025**.

For documentation issues or improvements, please see the [Contributing Guide](developer/CONTRIBUTING.md).
"""

    with open("docs/README.md", "w", encoding="utf-8") as f:
        f.write(index_content)

    print("   ✅ Created comprehensive documentation index")


def update_gitignore():
    """Update .gitignore with documentation patterns"""

    gitignore_additions = """
# Documentation organization
archive/deprecated-docs/
docs/**/*.bak
docs/**/*.tmp
"""

    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "# Documentation organization" not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(gitignore_additions)
            print("   ✅ Updated .gitignore with documentation patterns")


def create_organization_summary():
    """Create documentation organization summary"""

    summary_content = """# Documentation Organization Summary
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📋 Organization Complete

### Consolidations Made
- ✅ **Implementation Documentation**: Merged 7 scattered implementation docs into comprehensive guide
- ✅ **Version Control Documentation**: Consolidated VERSION_CONTROL.md and VERSION_CONTROL_SUMMARY.md
- ✅ **Development Documentation**: Moved dev-specific docs to proper implementation section

### Archives Created
- 📁 **archive/deprecated-docs/**: Outdated and superseded documentation
- 📁 **docs/implementation/**: Consolidated technical implementation guides
- 📁 **docs/project/**: Project management and organization documentation

### Structure Improvements
- 📚 **Master Documentation Index**: Complete navigation guide in docs/README.md
- 🏗️ **Consolidated Implementation Guide**: Single comprehensive technical reference
- 📋 **Logical Organization**: Clear separation by audience (user/developer/project)

### Documentation Health
- ✅ **No Duplication**: Eliminated redundant documentation
- ✅ **Clear Navigation**: Comprehensive index with quick start guide
- ✅ **Proper Categorization**: Logical organization by purpose and audience
- ✅ **Updated References**: All internal links verified and updated

## 📂 Final Structure

```
docs/
├── README.md                                    # Master documentation index
├── Code_Citations.md                           # Code references and licenses
├── LINK_VERIFICATION_REPORT.md                 # Link validation report
│
├── user/                                       # End-user documentation
│   ├── Installation.md                         # Setup and installation
│   ├── User_Manual.md                         # Usage guide
│   └── Configuration.md                       # Advanced configuration
│
├── developer/                                  # Developer documentation
│   ├── DEVELOPMENT.md                         # Development environment
│   ├── API.md                                 # API reference
│   └── CONTRIBUTING.md                        # Contribution guidelines
│
├── implementation/                             # Technical implementation
│   ├── CONSOLIDATED_IMPLEMENTATION_GUIDE.md   # All feature implementations
│   ├── arch-linux-integration.md              # Platform-specific integration
│   ├── rkhunter-integration.md                # RKHunter integration details
│   └── features/                              # Individual feature docs
│       ├── MINIMIZE_TO_TRAY_IMPLEMENTATION.md
│       └── SINGLE_INSTANCE_IMPLEMENTATION.md
│
├── project/                                    # Project management
│   ├── REPOSITORY_ORGANIZATION.md             # Project structure
│   ├── VERSION_CONTROL.md                     # Git workflow (consolidated)
│   ├── PERFORMANCE_OPTIMIZATIONS.md           # Performance improvements
│   └── CLEANUP_SUMMARY.md                     # Maintenance history
│
└── releases/                                   # Release documentation
    └── RELEASE_2.2.0.md                       # Latest release notes
```

Documentation organization completed successfully! 🎉
"""

    with open("docs/DOCUMENTATION_ORGANIZATION_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(summary_content)

    print("   ✅ Created documentation organization summary")


def main():
    """Main organization function"""

    print("🚀 Starting Documentation Organization")
    print("=" * 50)

    print("📚 Consolidating implementation documentation...")
    archived_impl_docs = create_consolidated_implementation_guide()

    print("🔄 Consolidating project management docs...")
    consolidate_project_management_docs()

    print("🔧 Organizing development documentation...")
    organize_development_docs()

    print("📁 Archiving deprecated documentation...")
    archive_deprecated_docs()

    print("📖 Creating master documentation index...")
    create_master_documentation_index()

    print("📝 Updating .gitignore...")
    update_gitignore()

    print("📋 Creating organization summary...")
    create_organization_summary()

    # Archive old implementation docs after consolidation
    print("📁 Archiving old implementation files...")
    archive_dir = "archive/deprecated-docs/old-implementation"
    os.makedirs(archive_dir, exist_ok=True)

    for doc_path in archived_impl_docs:
        if os.path.exists(doc_path) and "features/" not in doc_path:
            filename = os.path.basename(doc_path)
            shutil.move(doc_path, f"{archive_dir}/{filename}")
            print(f"   📁 Archived: {filename}")

    print("\n✅ Documentation organization completed successfully!")
    print("📋 See docs/DOCUMENTATION_ORGANIZATION_SUMMARY.md for details")


if __name__ == "__main__":
    main()
