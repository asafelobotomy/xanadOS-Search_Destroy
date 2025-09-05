---
archived_date: "2025-09-05"
archive_reason: "Deprecated PolicyKit file superseded by io.github.asafelobotomy.* policies"
replacement: "config/io.github.asafelobotomy.searchanddestroy*.policy"
retention_period: "1 year"
archive_type: "deprecated"
original_location: "config/org.xanados.searchanddestroy.hardened.policy"
dependencies: []
migration_guide: "docs/implementation-reports/archiving-policy-implementation-2025-08-26.md"
security_considerations: "PolicyKit files archived but maintained for historical reference"
compliance_notes: "Superseded by updated app-id compliant policies"
---

# Archived PolicyKit Configuration

This file was archived as part of the final repository modernization cleanup.

## Reason for Archival
- **Status**: DEPRECATED
- **Superseded by**: io.github.asafelobotomy.* policy files
- **Migration Date**: 2025-08-24
- **Archive Date**: 2025-09-05

## Current Implementation
The functionality of this file has been replaced by:
- `config/io.github.asafelobotomy.searchanddestroy.policy`
- `config/io.github.asafelobotomy.searchanddestroy.hardened.policy`  
- `config/io.github.asafelobotomy.searchanddestroy.rkhunter.policy`

## Historical Context
This file represents the legacy org.xanados.* app-id implementation that was
superseded during Flathub compliance updates requiring io.github.* app-ids.
