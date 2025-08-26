---
applyTo: "**/Dockerfile*"
---

# Docker-specific Copilot Instructions

- Use multi-stage builds; keep final images minimal (distroless/alpine when appropriate).
- Pin base images by digest or version; avoid `latest`.
- Create a non-root user; drop privileges; set `USER` in final stage.
- Leverage build cache: order instructions from least to most frequently changing; copy `package.JSON`/`requirements.txt` first.
- Use `.dockerignore` to exclude build artifacts, VCS, and test data.
- Prefer explicit `ENTRYPOINT`and`CMD` separation; set healthchecks if runtime supports it.
- Document exposed ports and required env vars.
