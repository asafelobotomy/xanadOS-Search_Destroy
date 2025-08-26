---
applyTo: "**/*.tf"
---

# Terraform-specific Copilot Instructions

- Use modules for reuse and clear boundaries; keep root minimal.
- Set `terraform { required_version }` and provider version constraints.
- Keep state remote and locked (e.g., S3 + DynamoDB) when appropriate.
- Run `terraform fmt`and`tflint` if configured; keep changes small and reviewable.
- Use `variables.tf` with types, descriptions, and validation; avoid hard-coded values.
- Name resources consistently; tag everything; avoid drift from existing conventions.
