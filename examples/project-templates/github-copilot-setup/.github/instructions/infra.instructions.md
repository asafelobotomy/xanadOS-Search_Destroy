---
applyTo: "**/Docker-compose.yml"

---

# Infrastructure-specific Copilot Instructions

- Pin all image versions in Docker-compose.yml; avoid `latest` tags.
- Use health checks for all services that expose endpoints.
- Set resource limits (memory, CPU) for containers to prevent resource exhaustion.
- Use secrets management, never environment variables for sensitive data.
- Implement proper restart policies (unless-stopped, on-failure).
- Use networks to isolate services; avoid exposing unnecessary ports to host.
- Include logging configuration with log rotation.
- Document required environment variables and their purposes.
