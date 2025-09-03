# Runbook: Security Hardening

Add automated security checks and guidance. Use with Copilot agent mode.

## Prerequisites

- Admin or maintainer permissions available

## Steps

1. Add CodeQL security scan workflow.
2. Enable Dependabot for deps and security updates.
3. Add SECURITY.md and responsible disclosure info.
4. Add secret scanning and push protection (org settings permitting).
5. Add pre-commit security checks (linters, basic SAST where applicable).

## Prompts

- "Add CodeQL workflow for this repository."
- "Enable Dependabot version and security updates."
- "Create a SECURITY.md with reporting process and scope."

## Success criteria

- CodeQL and Dependabot active and visible in Security tab
- SECURITY.md present and linked in repo
