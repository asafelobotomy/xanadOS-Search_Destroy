---
applyTo: "**/deployment/**/*.{yml,YAML,tf,JSON}"

---

# Deployment/DevOps-specific Copilot Instructions

- Use blue-green or rolling deployments to minimize downtime
- Implement proper health checks with readiness and liveness probes
- Set resource requests and limits for all containers based on actual usage patterns
- Use secrets management systems; never hardcode sensitive values in deployment configs
- Implement proper backup and disaster recovery procedures with tested restore processes
- Use infrastructure as code with version control and peer review
- Set up monitoring and alerting before deploying to production
- Implement automated rollback triggers based on health metrics
- Use feature flags for gradual rollouts and quick rollbacks
- Document deployment procedures and runbooks for incident response
- Implement proper logging aggregation and centralized monitoring
- Use immutable infrastructure patterns; avoid manual server modifications
- Test deployment procedures in staging environments that mirror production
- Implement security scanning for container images and infrastructure
- Use multi-region deployments for critical services with proper failover mechanisms
