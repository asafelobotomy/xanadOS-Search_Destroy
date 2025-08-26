---
archived_date: "2025-08-26"
archive_reason: "Deprecated simple elevated runner; replaced by enhanced elevated_runner with persistent GUI session management"
replacement: "app/core/elevated_runner.py"
retention_period: "1 year"

archive_type: "deprecated"
original_location: "app/core/elevated_runner_simple.py"

dependencies: []
migration_guide: "docs/developer/AUTH_ELEVATION_MIGRATION.md"
security_considerations: "Prefer sudo with askpass and session caching; avoid pkexec when possible; ensure environment sanitization"
compliance_notes: "Follows file-organization and archive policies; references removed"
---

Deprecated simple elevated runner archived after adoption of unified, persistent GUI authentication flow.
