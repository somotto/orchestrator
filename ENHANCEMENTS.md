# Production Enhancements

This document describes the production-ready enhancements added to the Orchestrator project.

## 1. Health Checks and Readiness Probes 

All services now include health checks to ensure reliability:

### API Gateway & Inventory App
- **Liveness Probe**: HTTP GET to `/api/movies` every 10s
- **Readiness Probe**: HTTP GET to `/api/movies` every 5s
- Automatically restarts unhealthy pods
- Removes unready pods from service endpoints

### Databases (PostgreSQL)
- **Liveness Probe**: `pg_isready` command every 10s
- **Readiness Probe**: `pg_isready` command every 5s
- Ensures database is accepting connections before routing traffic

### RabbitMQ
- **Liveness Probe**: `rabbitmq-diagnostics ping` every 30s
- **Readiness Probe**: `rabbitmq-diagnostics check_running` every 10s
- Verifies message broker is operational

### Billing App
- **Liveness Probe**: Python import check every 30s
- **Readiness Probe**: Python import check every 10s
- Ensures consumer process is running

**Benefits**:
- Automatic recovery from failures
- Zero-downtime deployments
- Better service reliability

## 2. Network Policies 

Implemented zero-trust network security:

### Policy Rules
- **API Gateway**: Can only communicate with Inventory App and RabbitMQ
- **Inventory App**: Can only communicate with Inventory DB
- **Billing App**: Can only communicate with Billing DB and RabbitMQ
- **Databases**: Only accept connections from their respective apps
- **RabbitMQ**: Only accepts connections from API Gateway and Billing App

**Benefits**:
- Prevents lateral movement in case of compromise
- Enforces principle of least privilege
- Reduces attack surface

**File**: `manifests/10-network-policy.yaml`

## 3. Ingress Controller 

Added Ingress for better routing and external access:

### Features
- Host-based routing (orchestrator.local)
- Path-based routing support
- SSL/TLS termination ready
- Replaces NodePort for production use

**Usage**:
```bash
./scripts/setup-ingress.sh
# Add to /etc/hosts: 127.0.0.1 orchestrator.local
# Access: http://orchestrator.local:3000
```

**File**: `manifests/09-ingress.yaml`

## 4. Monitoring Stack 

Complete observability solution with Prometheus and Grafana:

### Prometheus
- Metrics collection from all pods
- 15-day retention
- AlertManager for notifications
- Node exporter for system metrics
- Kube-state-metrics for cluster state

### Grafana
- Pre-configured Prometheus datasource
- Built-in Kubernetes dashboards:
  - Cluster overview (GnetId: 7249)
  - Pod monitoring (GnetId: 6417)
- Admin credentials: admin/admin
- Persistent storage for dashboards

### Kubernetes Dashboard
- Visual cluster management
- Resource monitoring
- Log viewing
- Pod management

**Setup**:
```bash
./scripts/setup-monitoring.sh
```

**Access**:
- Prometheus: `kubectl port-forward -n monitoring svc/prometheus-server 9090:80`
- Grafana: `kubectl port-forward -n monitoring svc/grafana 3001:80`
- K8s Dashboard: `http://localhost:30002`

**Files**: 
- `scripts/setup-monitoring.sh`
- `monitoring/prometheus-values.yaml`
- `monitoring/grafana-values.yaml`
- `monitoring/kubernetes-dashboard.yaml`

## 5. CI/CD Pipeline 

GitHub Actions workflow for automated testing and deployment:

### Pipeline Stages

**1. Test Job**
- Runs on every push and PR
- Python linting with flake8
- Unit tests (pytest ready)
- Code coverage reporting

**2. Build Job**
- Builds Docker images for all services
- Pushes to GitHub Container Registry (ghcr.io)
- Matrix strategy for parallel builds
- Caches layers for faster builds
- Tags: branch name, SHA, latest

**3. Deploy to Development**
- Triggers on push to `develop` branch
- Updates deployment images
- Waits for rollout completion
- Automated deployment verification

**4. Deploy to Production**
- Triggers on push to `main` branch
- Requires manual approval (GitHub environment)
- Updates production cluster
- Rollout verification

### Setup Requirements

Add these secrets to your GitHub repository:
- `KUBECONFIG_DEV`: Base64-encoded kubeconfig for dev cluster
- `KUBECONFIG_PROD`: Base64-encoded kubeconfig for prod cluster

**File**: `.github/workflows/ci-cd.yaml`

## 6. Cloud Deployment Guides 

Comprehensive guides for major cloud providers:

### AWS EKS
- EKS cluster creation with eksctl
- ECR for container registry
- EBS CSI driver for persistent volumes
- AWS Load Balancer Controller
- IAM roles for service accounts
- Cost optimization tips

**File**: `cloud/eks-deployment.md`

## 7. Monitoring Dashboard 

Quick monitoring script for cluster health:

**Features**:
- Node status
- Pod health
- Service endpoints
- HPA metrics
- PVC status
- Recent events
- Resource usage (if metrics-server available)

**Usage**:
```bash
./scripts/monitor.sh
```

**File**: `scripts/monitor.sh`

## Summary of Enhancements

| Enhancement | Status | Files |
|-------------|--------|-------|
| Health Checks | ✅ | manifests/03-08 (updated) |
| Readiness Probes | ✅ | manifests/03-08 (updated) |
| Network Policies | ✅ | manifests/10-network-policy.yaml |
| Ingress Controller | ✅ | manifests/09-ingress.yaml |
| Prometheus | ✅ | monitoring/prometheus-values.yaml |
| Grafana | ✅ | monitoring/grafana-values.yaml |
| K8s Dashboard | ✅ | monitoring/kubernetes-dashboard.yaml |
| CI/CD Pipeline | ✅ | .github/workflows/ci-cd.yaml |
| AWS EKS Guide | ✅ | cloud/eks-deployment.md |
