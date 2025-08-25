---
applyTo: "**/*.SQL"

---

# SQL/Database Migration-specific Copilot Instructions

- Prefer migrations over ad-hoc scripts; keep them idempotent where feasible and ordered
- Use transactions for multi-statement changes; avoid partial application
- Add indexes with care; consider read/write tradeoffs and existing query patterns
- Avoid `SELECT *` in application-facing queries; specify columns
- Use parameterized queries; never interpolate untrusted input
- Document schema changes and rollback plan in migration comments
- Test migrations on production-like data volumes before deployment
- Include rollback instructions for breaking changes with explicit approval process
- Avoid DROP operations without explicit data backup and approval
- Use database transactions for multi-table operations to ensure consistency
- Implement migration safety checks: validate constraints before adding them
- Add foreign key constraints with proper ON DELETE/UPDATE behavior
- Use appropriate data types and avoid TEXT for structured data
- Monitor query performance impact of schema changes in staging environment
- Include migration timing estimates and lock duration warnings
