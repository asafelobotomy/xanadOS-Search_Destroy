# Deployment Strategy Prompt

Design and implement deployment strategies for modern applications.
Create automated pipelines with testing, monitoring, and rollbacks.
Support multiple environments and infrastructure types.

## Deployment Strategy Framework

### 1. Deployment Environment Architecture

### Multi-Environment Setup

```yaml
# environments.yml - Environment configuration structure

environments:
  development:
    purpose: "Developer sandbox for feature development"
    infrastructure:
      type: "local_docker"
      auto_deploy: true
  branch_triggers: ["feature/*"]
    resources:
      cpu_limit: "2 cores"
      memory_limit: "4GB"
      storage: "20GB"
    configuration:
      database_url: "postgresql://localhost:5432/myapp_dev"
      redis_url: "redis://localhost:6379/0"
      log_level: "DEBUG"
      debug_mode: true

  staging:
    purpose: "Pre-production testing and QA validation"
    infrastructure:
      type: "kubernetes"
      cluster: "staging-cluster"
      namespace: "myapp-staging"
      auto_deploy: true
  branch_triggers: ["release/*"]
    resources:
      replicas: 2
      cpu_request: "500m"
      cpu_limit: "1000m"
      memory_request: "1Gi"
      memory_limit: "2Gi"
    configuration:
      database_url: "${STAGING_DB_URL}"
      redis_url: "${STAGING_REDIS_URL}"
      log_level: "INFO"
      debug_mode: false
    testing:
      automated_tests: true
      performance_tests: true
      security_scans: true
      approval_required: false

  production:
    purpose: "Live production environment serving real users"
    infrastructure:
      type: "kubernetes"
      cluster: "production-cluster"
      namespace: "myapp-production"
      auto_deploy: false  # Manual approval required
      branch_triggers: ["main"]
    resources:
      replicas: 5
      cpu_request: "1000m"
      cpu_limit: "2000m"
      memory_request: "2Gi"
      memory_limit: "4Gi"
    configuration:
      database_url: "${PROD_DB_URL}"
      redis_url: "${PROD_REDIS_URL}"
      log_level: "WARN"
      debug_mode: false
    testing:
      smoke_tests: true
      approval_required: true
      rollback_plan: true
    monitoring:
      health_checks: true
      performance_monitoring: true
      error_tracking: true
      alerting: true
```

## Infrastructure as Code (Terraform)

```hcl
# infrastructure/main.tf - Complete infrastructure setup

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket = "myapp-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

# VPC and Networking

module "vpc" {
  source = "./modules/vpc"

  environment = var.environment
  vpc_cidr    = var.vpc_cidr

  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

  tags = local.common_tags
}

# EKS Cluster

module "eks" {
  source = "./modules/eks"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = "1.28"

  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids

  node_groups = {
    main = {
      instance_types = ["t3.medium", "t3.large"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3

      labels = {
        role = "worker"
        environment = var.environment
      }

      taints = []
    }

    gpu = {
      instance_types = ["g4dn.xlarge"]
      min_size       = 0
      max_size       = 3
      desired_size   = 0

      labels = {
        role = "gpu-worker"
        "nvidia.com/gpu" = "true"
      }

      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }

  tags = local.common_tags
}

# RDS Database

module "database" {
  source = "./modules/rds"

  identifier = "${var.project_name}-${var.environment}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.environment == "production" ? "db.r6g.xlarge" : "db.t4g.medium"

  allocated_storage     = var.environment == "production" ? 100 : 20
  max_allocated_storage = var.environment == "production" ? 1000 : 100

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  vpc_security_group_ids = [module.security_groups.database_sg_id]
  db_subnet_group_name   = module.vpc.db_subnet_group_name

  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  deletion_protection = var.environment == "production"

  tags = local.common_tags
}

# ElastiCache Redis

module "redis" {
  source = "./modules/elasticache"

  cluster_id = "${var.project_name}-${var.environment}-redis"

  node_type           = var.environment == "production" ? "cache.r6g.large" : "cache.t4g.micro"
  num_cache_nodes     = var.environment == "production" ? 3 : 1
  parameter_group     = "default.redis7"
  engine_version      = "7.0"

  subnet_group_name   = module.vpc.cache_subnet_group_name
  security_group_ids  = [module.security_groups.cache_sg_id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = local.common_tags
}

# Application Load Balancer

module "alb" {
  source = "./modules/alb"

  name = "${var.project_name}-${var.environment}-alb"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids

  security_group_ids = [module.security_groups.alb_sg_id]

  certificate_arn = var.ssl_certificate_arn

  tags = local.common_tags
}

# Security Groups

module "security_groups" {
  source = "./modules/security_groups"

  vpc_id = module.vpc.vpc_id

  tags = local.common_tags
}

# Monitoring and Logging

module "monitoring" {
  source = "./modules/monitoring"

  environment = var.environment
  cluster_name = module.eks.cluster_name

  slack_webhook_url = var.slack_webhook_url
  pagerduty_integration_key = var.pagerduty_integration_key

  tags = local.common_tags
}

# Local values

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.team_name
  }
}
```

## 2. CI/CD Pipeline Implementation

### GitHub Actions Deployment Pipeline

```yaml
# .github/workflows/deploy.yml - Comprehensive deployment pipeline

name: Deploy Application

on:
  push:
    branches:
      - main
      - 'release/*'
      - 'feature/*'
  pull_request:
    branches:
      - main

env:
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Test Phase
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: >-
            ${{ runner.os }}-pip-

      - name: Install dependencies
  run: >-
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
  run: >-
          flake8 src/
          black --check src/
          isort --check-only src/

      - name: Run type checking
        run: mypy src/

      - name: Run unit tests
  run: >-
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=85
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0

      - name: Run integration tests
  run: >-
          pytest tests/integration/ \
            --cov=src \
            --cov-append \
            --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  # Security Scanning
  security:
    name: Security Scanning
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Semgrep security scan
        uses: returntocorp/semgrep-action@v1
        with:
          publishToken: ${{ secrets.SEMGREP_APP_TOKEN }}
          generateSarif: true

      - name: Run dependency check
  run: >-
          pip install safety
          safety check --json --output safety-report.json || true

      - name: Upload security artifacts
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: >-
            trivy-results.sarif
            safety-report.json

  # Build and Push Docker Image
  build:
    name: Build and Push Image
    runs-on: ubuntu-latest
    needs: [test, security]

    outputs:
      image-tag: ${{ steps.image.outputs.tag }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.DOCKER_REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate image metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: >-
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix=sha-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

      - name: Set image tag output
        id: image
        run: echo "tag=${{ fromJSON(steps.meta.outputs.json).tags[0] }}" >> $GITHUB_OUTPUT

  # Deploy to Development
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: build
  if: startsWith(github.ref, 'refs/heads/feature/')
    environment: development

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.DEV_KUBECONFIG }}

      - name: Deploy to development
  run: >-
          # Update image tag in deployment
          kubectl set image deployment/myapp-deployment \
            myapp=${{ needs.build.outputs.image-tag }} \
            -n myapp-development

          # Wait for rollout to complete
          kubectl rollout status deployment/myapp-deployment \
            -n myapp-development \
            --timeout=300s

      - name: Run smoke tests
  run: >-
          # Wait for service to be ready
          kubectl wait --for=condition=ready pod \
            -l app=myapp \
            -n myapp-development \
            --timeout=60s

          # Get service URL
          SERVICE_URL=$(kubectl get service myapp-service \
            -n myapp-development \
            -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

          # Run smoke tests
          pytest tests/smoke/ --url=http://$SERVICE_URL

  # Deploy to Staging
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
  if: startsWith(github.ref, 'refs/heads/release/')
    environment: staging

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.STAGING_KUBECONFIG }}

      - name: Deploy to staging
  run: >-
          helm upgrade --install myapp ./helm/myapp \
            --namespace myapp-staging \
            --create-namespace \
            --set image.tag=${{ needs.build.outputs.image-tag }} \
            --set environment=staging \
            --set database.url=${{ secrets.STAGING_DATABASE_URL }} \
            --set redis.url=${{ secrets.STAGING_REDIS_URL }} \
            --wait \
            --timeout=10m

      - name: Run comprehensive tests
  run: >-
          # Wait for deployment
          kubectl wait --for=condition=available deployment/myapp \
            -n myapp-staging \
            --timeout=300s

          # Get service URL
          SERVICE_URL=$(kubectl get ingress myapp-ingress \
            -n myapp-staging \
            -o jsonpath='{.spec.rules[0].host}')

          # Run test suites
          pytest tests/integration/ --url=https://$SERVICE_URL
          pytest tests/e2e/ --url=https://$SERVICE_URL

          # Run performance tests
          locust -f tests/performance/locustfile.py \
            --host=https://$SERVICE_URL \
            --users=50 \
            --spawn-rate=5 \
            --run-time=5m \
            --headless

  # Deploy to Production
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.PROD_KUBECONFIG }}

      - name: Pre-deployment checks
  run: >-
          # Check cluster health
          kubectl get nodes
          kubectl top nodes

          # Check current deployment status
          kubectl get deployment myapp -n myapp-production

          # Verify database connectivity
          kubectl run db-check --rm -i --restart=Never \
            --image=postgres:15 \
            -- pg_isready -h ${{ secrets.PROD_DATABASE_HOST }}

      - name: Blue-Green Deployment
  run: >-
          # Deploy to green environment
          helm upgrade --install myapp-green ./helm/myapp \
            --namespace myapp-production \
            --set image.tag=${{ needs.build.outputs.image-tag }} \
            --set environment=production \
            --set deployment.name=myapp-green \
            --set service.name=myapp-green \
            --set database.url=${{ secrets.PROD_DATABASE_URL }} \
            --set redis.url=${{ secrets.PROD_REDIS_URL }} \
            --wait \
            --timeout=10m

          # Wait for green deployment to be ready
          kubectl wait --for=condition=available deployment/myapp-green \
            -n myapp-production \
            --timeout=600s

          # Run smoke tests on green environment
          GREEN_SERVICE_IP=$(kubectl get service myapp-green \
            -n myapp-production \
            -o jsonpath='{.spec.clusterIP}')

          pytest tests/smoke/ --url=http://$GREEN_SERVICE_IP:8000

      - name: Switch Traffic to Green
  run: >-
          # Update ingress to point to green service
          kubectl patch ingress myapp-ingress \
            -n myapp-production \
            --type=json \
            -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "myapp-green"}]'

          # Wait for traffic switch
          sleep 30

          # Verify production health
          kubectl get pods -n myapp-production -l app=myapp-green

          # Run production smoke tests
          PROD_URL=$(kubectl get ingress myapp-ingress \
            -n myapp-production \
            -o jsonpath='{.spec.rules[0].host}')

          pytest tests/smoke/ --url=https://$PROD_URL

      - name: Cleanup Old Blue Deployment
  run: >-
          # Wait before cleanup (allow for quick rollback if needed)
          sleep 300  # 5 minutes

          # Remove old blue deployment
          helm uninstall myapp-blue -n myapp-production || true

          # Rename green to blue for next deployment
          kubectl patch deployment myapp-green \
            -n myapp-production \
            --type=json \
            -p='[{"op": "replace", "path": "/metadata/name", "value": "myapp"}]'

          kubectl patch service myapp-green \
            -n myapp-production \
            --type=json \
            -p='[{"op": "replace", "path": "/metadata/name", "value": "myapp"}]'

      - name: Post-deployment monitoring
  run: >-
          # Send deployment notification
          curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
            -H 'Content-type: application/json' \
            --data '{"text":"🚀 Production deployment completed successfully!\nVersion: ${{ needs.build.outputs.image-tag }}\nCommit: ${{ github.sha }}"}'

          # Update deployment tracking
          echo "Deployment completed at $(date)" >> deployment-log.txt
```

## 3. Container Orchestration with Kubernetes

### Comprehensive Kubernetes Deployment

```yaml
# k8s/namespace.yaml

apiVersion: v1
kind: Namespace
metadata:
  name: myapp-production
  labels:
    environment: production
    app: myapp

---

# k8s/configmap.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
  namespace: myapp-production
data:
  environment: "production"
  log_level: "INFO"
  redis_timeout: "30"
  api_timeout: "60"
  max_connections: "100"

---

# k8s/secret.yaml

apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
  namespace: myapp-production
type: Opaque
data:
  database_url: <base64-encoded-database-url>
  redis_url: <base64-encoded-redis-url>
  jwt_secret: <base64-encoded-jwt-secret>
  encryption_key: <base64-encoded-encryption-key>

---

# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: myapp-production
  labels:
    app: myapp
    environment: production
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
        environment: production
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: myapp
        image: ghcr.io/myorg/myapp:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: myapp-config
              key: environment
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: myapp-config
              key: log_level
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database_url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: redis_url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: jwt_secret
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /startup
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
        volumeMounts:
        - name: app-storage
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: app-storage
        persistentVolumeClaim:
          claimName: myapp-storage
      - name: logs
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - myapp
              topologyKey: kubernetes.io/hostname
      tolerations:
      - key: "node.kubernetes.io/memory-pressure"
        operator: "Exists"
        effect: "NoSchedule"
        tolerationSeconds: 300

---

# k8s/service.yaml

apiVersion: v1
kind: Service
metadata:
  name: myapp-service
  namespace: myapp-production
  labels:
    app: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  type: ClusterIP

---

# k8s/ingress.yaml

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: myapp-production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.myapp.com
    secretName: myapp-tls
  rules:
  - host: api.myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80

---

# k8s/hpa.yaml

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
  namespace: myapp-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max

---

# k8s/pdb.yaml

apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
  namespace: myapp-production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp

---

# k8s/networkpolicy.yaml

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: myapp-network-policy
  namespace: myapp-production
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
    - protocol: UDP
      port: 53
```

## 4. Advanced Deployment Strategies

### Blue-Green Deployment Implementation

```python
#!/usr/bin/env python3
"""
Blue-Green Deployment Automation Script
Manages blue-green deployments with health checks and automatic rollback
"""

import subprocess
import time
import requests
import json
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class DeploymentConfig:
    """Configuration for blue-green deployment"""
    namespace: str
    app_name: str
    image_tag: str
    health_check_url: str
    timeout_seconds: int = 600
    health_check_retries: int = 10
    health_check_interval: int = 30

class BlueGreenDeployer:
    """Manage blue-green deployments"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.current_color = self._get_current_color()
        self.target_color = 'green' if self.current_color == 'blue' else 'blue'

    def deploy(self) -> bool:
        """Execute blue-green deployment"""
        try:
            print(f"🚀 Starting blue-green deployment...")
            print(f"Current: {self.current_color}, Target: {self.target_color}")

            # Step 1: Deploy to target environment
            if not self._deploy_target_environment():
                print("❌ Failed to deploy to target environment")
                return False

            # Step 2: Health check target environment
            if not self._health_check_target():
                print("❌ Health check failed for target environment")
                self._cleanup_target()
                return False

            # Step 3: Switch traffic
            if not self._switch_traffic():
                print("❌ Failed to switch traffic")
                self._cleanup_target()
                return False

            # Step 4: Final health check
            if not self._final_health_check():
                print("❌ Final health check failed, rolling back")
                self._rollback()
                return False

            # Step 5: Cleanup old environment
            self._cleanup_old_environment()

            print(f"✅ Blue-green deployment completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Deployment failed with error: {e}")
            self._rollback()
            return False

    def _get_current_color(self) -> str:
        """Determine current active color"""
        try:
            # Check which service is currently active
            result = subprocess.run([
                'kubectl', 'get', 'service', f"{self.config.app_name}-service",
                '-n', self.config.namespace,
                '-o', 'jsonpath={.spec.selector.color}'
            ], capture_output=True, text=True, check=True)

            current = result.stdout.strip()
            return current if current in ['blue', 'green'] else 'blue'

        except subprocess.CalledProcessError:
            return 'blue'  # Default to blue if service doesn't exist

    def _deploy_target_environment(self) -> bool:
        """Deploy to target color environment"""
        print(f"📦 Deploying to {self.target_color} environment...")

        try:
            # Deploy using Helm
            cmd = [
                'helm', 'upgrade', '--install',
                f"{self.config.app_name}-{self.target_color}",
                './helm/myapp',
                '--namespace', self.config.namespace,
                '--set', f"image.tag={self.config.image_tag}",
                '--set', f"deployment.color={self.target_color}",
                '--set', f"service.color={self.target_color}",
                '--wait',
                '--timeout', f"{self.config.timeout_seconds}s"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Successfully deployed to {self.target_color}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e.stderr}")
            return False

    def _health_check_target(self) -> bool:
        """Perform health check on target environment"""
        print(f"🏥 Health checking {self.target_color} environment...")

        # Get target service endpoint
        try:
            result = subprocess.run([
                'kubectl', 'get', 'service', f"{self.config.app_name}-{self.target_color}",
                '-n', self.config.namespace,
                '-o', 'jsonpath={.spec.clusterIP}'
            ], capture_output=True, text=True, check=True)

            target_ip = result.stdout.strip()
            health_url = f"http://{target_ip}:8000/health"

        except subprocess.CalledProcessError:
            print("❌ Could not get target service IP")
            return False

        # Perform health checks
        for attempt in range(self.config.health_check_retries):
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') == 'healthy':
                        print(f"✅ {self.target_color} environment is healthy")
                        return True
                    else:
                        print(f"⚠️  Health check returned: {health_data}")

            except requests.RequestException as e:
                print(f"⚠️  Health check attempt {attempt + 1} failed: {e}")

            if attempt < self.config.health_check_retries - 1:
                time.sleep(self.config.health_check_interval)

        print(f"❌ Health check failed after {self.config.health_check_retries} attempts")
        return False

    def _switch_traffic(self) -> bool:
        """Switch traffic to target environment"""
        print(f"🔄 Switching traffic to {self.target_color}...")

        try:
            # Update main service to point to target color
            patch_data = {
                "spec": {
                    "selector": {
                        "app": self.config.app_name,
                        "color": self.target_color
                    }
                }
            }

            cmd = [
                'kubectl', 'patch', 'service', f"{self.config.app_name}-service",
                '-n', self.config.namespace,
                '--type', 'merge',
                '-p', json.dumps(patch_data)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Wait for traffic switch to propagate
            time.sleep(30)

            print(f"✅ Traffic switched to {self.target_color}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to switch traffic: {e.stderr}")
            return False

    def _final_health_check(self) -> bool:
        """Perform final health check through public endpoint"""
        print("🏥 Performing final health check...")

        for attempt in range(5):
            try:
                response = requests.get(self.config.health_check_url, timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') == 'healthy':
                        print("✅ Final health check passed")
                        return True

            except requests.RequestException as e:
                print(f"⚠️  Final health check attempt {attempt + 1} failed: {e}")

            time.sleep(10)

        return False

    def _cleanup_target(self):
        """Cleanup failed target deployment"""
        print(f"🧹 Cleaning up failed {self.target_color} deployment...")

        try:
            subprocess.run([
                'helm', 'uninstall', f"{self.config.app_name}-{self.target_color}",
                '-n', self.config.namespace
            ], check=True)

        except subprocess.CalledProcessError:
            pass  # Ignore cleanup errors

    def _cleanup_old_environment(self):
        """Cleanup old environment after successful deployment"""
        print(f"🧹 Cleaning up old {self.current_color} environment...")

        try:
            # Wait before cleanup to allow for monitoring
            time.sleep(60)

            subprocess.run([
                'helm', 'uninstall', f"{self.config.app_name}-{self.current_color}",
                '-n', self.config.namespace
            ], check=True)

            print(f"✅ Cleaned up old {self.current_color} environment")

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to cleanup old environment: {e}")

    def _rollback(self):
        """Rollback to previous environment"""
        print(f"🔄 Rolling back to {self.current_color}...")

        try:
            # Switch traffic back to current color
            patch_data = {
                "spec": {
                    "selector": {
                        "app": self.config.app_name,
                        "color": self.current_color
                    }
                }
            }

            cmd = [
                'kubectl', 'patch', 'service', f"{self.config.app_name}-service",
                '-n', self.config.namespace,
                '--type', 'merge',
                '-p', json.dumps(patch_data)
            ]

            subprocess.run(cmd, check=True)

            # Cleanup failed target
            self._cleanup_target()

            print(f"✅ Rollback to {self.current_color} completed")

        except subprocess.CalledProcessError as e:
            print(f"❌ Rollback failed: {e}")

def main():
    """Main deployment function"""
    if len(sys.argv) != 4:
        print("Usage: python deploy.py <namespace> <app_name> <image_tag>")
        sys.exit(1)

    namespace = sys.argv[1]
    app_name = sys.argv[2]
    image_tag = sys.argv[3]

    config = DeploymentConfig(
        namespace=namespace,
        app_name=app_name,
        image_tag=image_tag,
        health_check_url=f"https://api.{app_name}.com/health"
    )

    deployer = BlueGreenDeployer(config)
    success = deployer.deploy()

    if not success:
        print("❌ Deployment failed")
        sys.exit(1)

    print("✅ Deployment completed successfully")

if __name__ == "__main__":
    main()
```

### Canary Deployment with Istio

```yaml
# canary-deployment.yaml - Istio canary deployment

apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-rollout
  namespace: myapp-production
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 2m}
      - setWeight: 20
      - pause: {duration: 2m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 80
      - pause: {duration: 2m}

      trafficRouting:
        istio:
          virtualService:
            name: myapp-vs
            routes:
            - primary
          destinationRule:
            name: myapp-dr
            canarySubsetName: canary
            stableSubsetName: stable

      analysis:
        templates:
        - templateName: success-rate
        - templateName: latency
        args:
        - name: service-name
          value: myapp
        - name: namespace
          value: myapp-production

        startingStep: 2
        interval: 5m
        count: 5

        successCondition: result[0] >= 0.95 && result[1] <= 500
        failureCondition: result[0] < 0.90 || result[1] > 1000

  selector:
    matchLabels:
      app: myapp

  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: ghcr.io/myorg/myapp:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi

---

# Analysis templates for canary deployment

apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: myapp-production
spec:
  args:
  - name: service-name
  - name: namespace
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= 0.95
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
  query: >-
          sum(rate(http_requests_total{service="{{args.service-name}}",namespace="{{args.namespace}}",code!~"5.."}[1m])) /
          sum(rate(http_requests_total{service="{{args.service-name}}",namespace="{{args.namespace}}"}[1m]))

---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency
  namespace: myapp-production
spec:
  args:
  - name: service-name
  - name: namespace
  metrics:
  - name: latency
    interval: 1m
    count: 5
    successCondition: result[0] <= 500
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
  query: >-
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}",namespace="{{args.namespace}}"}[1m]))
            by (le)
          ) * 1000

---

# Istio VirtualService for traffic splitting

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-vs
  namespace: myapp-production
spec:
  hosts:
  - api.myapp.com
  gateways:
  - myapp-gateway
  http:
  - name: primary
    match:
    - headers:
        end-user:
          exact: canary
    route:
    - destination:
        host: myapp-service
        subset: canary
      weight: 100
  - name: primary
    route:
    - destination:
        host: myapp-service
        subset: stable
      weight: 100
    - destination:
        host: myapp-service
        subset: canary
      weight: 0

---

# Istio DestinationRule for service subsets

apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp-dr
  namespace: myapp-production
spec:
  host: myapp-service
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
```

## 5. Monitoring and Observability

### Comprehensive Monitoring Setup

```yaml
# monitoring/prometheus.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: >-
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
    - "/etc/prometheus/rules/*.yml"

    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093

    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod

      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

    - job_name: 'myapp'
      static_configs:
      - targets: ['myapp-service.myapp-production:8000']
      metrics_path: /metrics
      scrape_interval: 10s

---

# monitoring/grafana-dashboard.json

{
  "dashboard": {
    "id": null,
    "title": "MyApp Production Dashboard",
    "description": "Comprehensive monitoring dashboard for MyApp production environment",
    "tags": ["myapp", "production", "kubernetes"],
    "timezone": "UTC",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"myapp\"}[5m])) by (method, status_code)",
            "legendFormat": "{{method}} {{status_code}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec",
            "min": 0
          }
        ],
        "legend": {
          "show": true,
          "table": true,
          "values": true,
          "avg": true,
          "current": true,
          "max": true
        }
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service=\"myapp\"}[5m])) by (le))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{service=\"myapp\"}[5m])) by (le))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds",
            "min": 0
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"myapp\",status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total{service=\"myapp\"}[5m]))",
            "format": "percent"
          }
        ],
        "thresholds": "0.01,0.05",
        "colorBackground": true
      },
      {
        "id": 4,
        "title": "Pod CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(container_cpu_usage_seconds_total{pod=~\"myapp-.*\"}[5m])) by (pod)",
            "legendFormat": "{{pod}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Pod Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(container_memory_usage_bytes{pod=~\"myapp-.*\"}) by (pod)",
            "legendFormat": "{{pod}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(database_connections_active{service=\"myapp\"})",
            "legendFormat": "Active Connections"
          },
          {
            "expr": "sum(database_connections_idle{service=\"myapp\"})",
            "legendFormat": "Idle Connections"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
```

## Alerting Configuration

```yaml
# monitoring/alerting-rules.yaml

apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: myapp-alerts
  namespace: monitoring
spec:
  groups:
  - name: myapp.rules
    rules:

    # High Error Rate Alert
    - alert: HighErrorRate
  expr: >-
        (
          sum(rate(http_requests_total{service="myapp",status_code=~"5.."}[5m])) /
          sum(rate(http_requests_total{service="myapp"}[5m]))
        ) > 0.05
      for: 2m
      labels:
        severity: critical
        service: myapp
      annotations:
        summary: "High error rate detected for MyApp"
        description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"
        runbook_url: "https://wiki.company.com/runbooks/myapp/high-error-rate"

    # High Response Time Alert
    - alert: HighResponseTime
  expr: >-
        histogram_quantile(0.95,
          sum(rate(http_request_duration_seconds_bucket{service="myapp"}[5m])) by (le)
        ) > 1.0
      for: 5m
      labels:
        severity: warning
        service: myapp
      annotations:
        summary: "High response time for MyApp"
        description: "95th percentile response time is {{ $value }}s"

    # Pod Down Alert
    - alert: PodDown
  expr: >-
        up{job="myapp"} == 0
      for: 1m
      labels:
        severity: critical
        service: myapp
      annotations:
        summary: "MyApp pod is down"
        description: "Pod {{ $labels.instance }} has been down for more than 1 minute"

    # High CPU Usage Alert
    - alert: HighCPUUsage
  expr: >-
        sum(rate(container_cpu_usage_seconds_total{pod=~"myapp-.*"}[5m])) by (pod) > 0.8
      for: 10m
      labels:
        severity: warning
        service: myapp
      annotations:
        summary: "High CPU usage for MyApp pod"
        description: "Pod {{ $labels.pod }} CPU usage is {{ $value | humanizePercentage }}"

    # High Memory Usage Alert
    - alert: HighMemoryUsage
  expr: >-
        (
          container_memory_usage_bytes{pod=~"myapp-.*"} /
          container_spec_memory_limit_bytes{pod=~"myapp-.*"}
        ) > 0.9
      for: 5m
      labels:
        severity: warning
        service: myapp
      annotations:
        summary: "High memory usage for MyApp pod"
        description: "Pod {{ $labels.pod }} memory usage is {{ $value | humanizePercentage }}"

    # Database Connection Alert
    - alert: DatabaseConnectionHigh
  expr: >-
        sum(database_connections_active{service="myapp"}) > 80
      for: 5m
      labels:
        severity: warning
        service: myapp
      annotations:
        summary: "High database connection count"
        description: "Active database connections: {{ $value }}"

    # Deployment Failed Alert
    - alert: DeploymentFailed
  expr: >-
        kube_deployment_status_replicas_unavailable{deployment="myapp"} > 0
      for: 5m
      labels:
        severity: critical
        service: myapp
      annotations:
        summary: "MyApp deployment has unavailable replicas"
        description: "{{ $value }} replicas are unavailable"

---

# monitoring/alertmanager.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: >-
    global:
      smtp_smarthost: 'smtp.company.com:587'
      smtp_from: 'alerts@company.com'
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'default'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
        repeat_interval: 15m
      - match:
          severity: warning
        receiver: 'warning-alerts'
        repeat_interval: 1h

    receivers:
    - name: 'default'
      slack_configs:
      - channel: '#alerts-general'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

    - name: 'critical-alerts'
      slack_configs:
      - channel: '#alerts-critical'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

    - name: 'warning-alerts'
      slack_configs:
      - channel: '#alerts-warning'
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
      email_configs:
      - to: 'team@company.com'
        subject: 'Warning Alert: {{ .GroupLabels.alertname }}'
        body: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## 6. Deployment Checklist

### Pre-Deployment Checklist

- [ ] **Code Quality**
  - [ ] All tests pass (unit, integration, e2e)
  - [ ] Code coverage meets minimum threshold (85%)
  - [ ] Security scans completed without critical issues
  - [ ] Performance tests pass
  - [ ] Code review approved

- [ ] **Infrastructure Readiness**
  - [ ] Target environment is healthy
  - [ ] Database migrations tested
  - [ ] Configuration secrets updated
  - [ ] Resource quotas verified
  - [ ] Monitoring and alerting configured

- [ ] **Rollback Preparation**
  - [ ] Previous version tagged and available
  - [ ] Rollback procedure documented
  - [ ] Database rollback plan (if schema changes)
  - [ ] Team notified of deployment window

### During Deployment Checklist

- [ ] **Deployment Execution**
  - [ ] Deployment started with proper approvals
  - [ ] Health checks passing
  - [ ] Traffic gradually shifted (if canary/blue-green)
  - [ ] Performance metrics within normal ranges
  - [ ] Error rates remain low

- [ ] **Monitoring**
  - [ ] Real-time monitoring dashboard active
  - [ ] Alert channels being monitored
  - [ ] Key stakeholders notified
  - [ ] Rollback trigger criteria defined

### Post-Deployment Checklist

- [ ] **Verification**
  - [ ] All smoke tests pass
  - [ ] User acceptance testing completed
  - [ ] Performance benchmarks met
  - [ ] Security posture verified
  - [ ] Documentation updated

- [ ] **Cleanup and Communication**
  - [ ] Old deployment artifacts cleaned up
  - [ ] Deployment notes documented
  - [ ] Team and stakeholders notified
  - [ ] Post-mortem scheduled (if issues occurred)
  - [ ] Lessons learned documented

Remember: Deployment strategy should match your application's requirements,
risk tolerance, and operational capabilities. Start with simpler strategies
and evolve to more sophisticated approaches as your infrastructure and
processes mature.
