# Archive Directory

This directory contains historical files, deprecated content, and legacy versions following the
repository archive policy requirements.

## 📁 Directory Structure

```text
archive/
├── README.md                   # This file - Archive policy and documentation
├── ARCHIVE_INDEX.md           # Comprehensive content index
├── deprecated/                # Deprecated content archive
│   ├── README.md             # Deprecation guidelines
│   └── [YYYY-MM-DD]/         # Date-organized deprecated content
├── legacy-versions/          # Previous version archive
│   ├── README.md            # Version management guidelines
│   └── [vX.Y.Z]/            # Version-organized legacy content
├── superseded/              # Replaced content archive
│   ├── README.md           # Supersession guidelines
│   └── [YYYY-MM-DD]/       # Date-organized superseded content
└── backups/                # Backup files from various operations
```

## 🗃️ Archive Categories

### Deprecated (`deprecated/`)

Content that is no longer maintained and scheduled for future removal.

- **Retention**: Minimum 1 year, reviewed annually
- **Naming**: `YYYY-MM-DD/` date-organized structure
- **Metadata**: Required YAML frontmatter with archival information

### Legacy Versions (`legacy-versions/`)

Previous versions of current files maintained for reference.

- **Retention**: Major versions permanent, minor versions 2 years
- **Naming**: `vX.Y.Z/` version-organized structure
- **Metadata**: Version-specific archival information

### Superseded (`superseded/`)

Content completely replaced by new implementations.

- **Retention**: 3 years from supersession date
- **Naming**: `YYYY-MM-DD/` date-organized structure
- **Metadata**: Replacement path and migration guide

### Backups (`backups/`)

Operational backup files from various repository operations.

- **Retention**: Based on operation type and importance
- **Naming**: Descriptive folder/file names with dates
- **Metadata**: Operation context and backup purpose

## 📝 Usage Guidelines

### Adding Content to Archive

1. **Classify Content**: Determine appropriate category (deprecated/legacy/superseded)
2. **Create Directory**: Use proper naming convention (`YYYY-MM-DD` or `vX.Y.Z`)
3. **Add Metadata**: Include YAML frontmatter with archival information
4. **Update Index**: Add entry to `ARCHIVE_INDEX.md`
5. **Remove References**: Update links in active documentation

### Required Metadata Format

```yaml
---
archived_date: "YYYY-MM-DD"
archive_reason: "Detailed reason for archiving"
replacement: "Path to replacement or 'none'"
retention_period: "X years or 'permanent'"
archive_type: "deprecated|legacy-version|superseded"
original_location: "Original file path"
migration_guide: "Path to migration documentation"
---
```

## � Archive Statistics

- **Total Items**: 38 (updated 2025-09-12)
- **Deprecated**: 18 items (2025-09-12 cleanup)
- **Legacy Versions**: Multiple legacy content items
- **Superseded**: Historical superseded content
- **Backups**: Development environment backups

## �🔍 Finding Archived Content

- **Browse**: Use directory structure to locate content by date or version
- **Search**: Use `ARCHIVE_INDEX.md` for comprehensive content listing
- **Reference**: Check active documentation for archive migration notes

## 🧹 Maintenance

- **Annual Review**: Deprecated content reviewed and cleaned annually
- **Retention Policy**: Automatic cleanup based on retention periods
- **Index Updates**: `ARCHIVE_INDEX.md` maintained with all archived content

---

For complete archive policy details, see: `.github/instructions/archive-policy.instructions.md`
