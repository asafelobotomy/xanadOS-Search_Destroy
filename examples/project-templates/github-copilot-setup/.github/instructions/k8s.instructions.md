---
applyTo: "**/k8s/**/*.{YAML,yml}"

---

# Kubernetes-specific Copilot Instructions

- Use Deployment/StatefulSet appropriately; define `readinessProbe`and`livenessProbe`.
- Always set resource `requests`and`limits`; avoid unbounded pods.
- Avoid mutable image tags; pin by version/digest.
- Use `securityContext`(drop capabilities, runAsNonRoot) and`podSecurityContext`.
- Keep ConfigMaps for non-sensitive config; use Secrets for sensitive data; never inline secrets.
- Version and manage manifests via GitOps/Kustomize/Helm; avoid ad-hoc cluster edits.
- Prefer `envFrom` for bulk config; document required variables and defaults.
