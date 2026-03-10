# Deployment Guide

## Quick Start

### 1. Prerequisites Check

```bash
# Verify Docker Desktop is running
docker ps

# Verify k3d is installed
k3d version

# Verify kubectl is installed
kubectl version --client
```

### 2. Deploy the Cluster

```bash
# Create cluster and deploy all services
./orchestrator.sh create

# Wait for all pods to be ready (may take 2-3 minutes)
kubectl wait --for=condition=Ready pods --all -n orchestrator --timeout=300s
```

### 3. Build and Push Images

```bash
# Build all Docker images and push to local registry
./scripts/build-and-push.sh
```

### 4. Restart Deployments (to pull new images)

```bash
# Restart all deployments to use new images
kubectl rollout restart deployment -n orchestrator
kubectl rollout restart statefulset -n orchestrator

# Wait for rollout to complete
kubectl rollout status deployment/api-gateway -n orchestrator
kubectl rollout status deployment/inventory-app -n orchestrator
kubectl rollout status statefulset/billing-app -n orchestrator
```

### 5. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n orchestrator

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# api-gateway-xxx                 1/1     Running   0          2m
# billing-app-0                   1/1     Running   0          2m
# billing-db-0                    1/1     Running   0          2m
# billing-queue-0                 1/1     Running   0          2m
# inventory-app-xxx               1/1     Running   0          2m
# inventory-db-0                  1/1     Running   0          2m
```

### 6. Test the API

```bash
# Run automated tests
./scripts/test-api.sh

# Or test manually
curl http://localhost:3000/api/movies
```

## Detailed Deployment Steps

### Step 1: Create k3d Cluster

The `orchestrator.sh create` command performs:

1. Creates a k3d cluster with:
   - 1 server node (master)
   - 1 agent node (worker)
   - Local Docker registry at k3d-registry.localhost:5000
   - Port mapping: 3000:30000 for API Gateway

2. Applies Kubernetes manifests in order:
   - Namespace
   - Secrets (credentials)
   - ConfigMap (configuration)
   - StatefulSets (databases, RabbitMQ)
   - Deployments (applications)
   - Services
   - HorizontalPodAutoscalers

### Step 2: Build Docker Images

The `build-and-push.sh` script:

1. Builds images from Dockerfiles:
   - postgres-db → inventory-db & billing-db
   - rabbitmq → billing-queue
   - inventory-app
   - billing-app
   - api-gateway-app

2. Tags images with registry prefix
3. Pushes to local k3d registry

### Step 3: Verify Services

```bash
# Check nodes
kubectl get nodes
# Should show: k3d-orchestrator-cluster-server-0 and k3d-orchestrator-cluster-agent-0

# Check all resources
kubectl get all -n orchestrator

# Check persistent volumes
kubectl get pvc -n orchestrator

# Check secrets
kubectl get secrets -n orchestrator

# Check configmaps
kubectl get configmap -n orchestrator
```

## Deployment Architecture

### Network Flow

```
Client → API Gateway (NodePort 30000) → Inventory App → Inventory DB
                ↓
         RabbitMQ Queue → Billing App → Billing DB
```

### Service Dependencies

1. **Databases start first** (StatefulSets with PVCs)
   - inventory-db-0
   - billing-db-0

2. **RabbitMQ starts** (StatefulSet with PVC)
   - billing-queue-0

3. **Applications start** (wait for dependencies)
   - inventory-app (waits for inventory-db)
   - billing-app (waits for billing-db and billing-queue)
   - api-gateway (waits for all services)

### Resource Allocation

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| API Gateway | 100m | 500m | 128Mi | 512Mi |
| Inventory App | 100m | 500m | 128Mi | 512Mi |
| Billing App | - | - | - | - |
| Databases | - | - | - | - |
| RabbitMQ | - | - | - | - |

### Storage

| Component | Storage Size | Access Mode |
|-----------|--------------|-------------|
| inventory-db | 1Gi | ReadWriteOnce |
| billing-db | 1Gi | ReadWriteOnce |
| billing-queue | 1Gi | ReadWriteOnce |

## Troubleshooting Deployment

### Issue: Pods stuck in Pending

```bash
# Check events
kubectl describe pod <pod-name> -n orchestrator

# Common causes:
# - Insufficient resources
# - PVC not bound
# - Image pull errors
```

### Issue: Image pull errors

```bash
# Verify registry is accessible
docker ps | grep registry

# Rebuild and push images
./scripts/build-and-push.sh

# Check image names in manifests match registry
kubectl get deployment api-gateway -n orchestrator -o yaml | grep image:
```

### Issue: Database not ready

```bash
# Check database logs
kubectl logs inventory-db-0 -n orchestrator
kubectl logs billing-db-0 -n orchestrator

# Check if PVC is bound
kubectl get pvc -n orchestrator

# Restart database pod
kubectl delete pod inventory-db-0 -n orchestrator
```

### Issue: RabbitMQ connection failed

```bash
# Check RabbitMQ logs
kubectl logs billing-queue-0 -n orchestrator

# Verify RabbitMQ is ready
kubectl exec -it billing-queue-0 -n orchestrator -- rabbitmqctl status

# Check if queue is created
kubectl port-forward svc/billing-queue 15672:15672 -n orchestrator
# Visit http://localhost:15672 (rabbit/password)
```

### Issue: Application crashes

```bash
# Check application logs
kubectl logs -l app=inventory-app -n orchestrator
kubectl logs -l app=billing-app -n orchestrator
kubectl logs -l app=api-gateway -n orchestrator

# Check environment variables
kubectl exec -it <pod-name> -n orchestrator -- env | grep DB
```

## Updating the Deployment

### Update Application Code

```bash
# 1. Make code changes in srcs/

# 2. Rebuild and push images
./scripts/build-and-push.sh

# 3. Restart deployments
kubectl rollout restart deployment/api-gateway -n orchestrator
kubectl rollout restart deployment/inventory-app -n orchestrator
kubectl rollout restart statefulset/billing-app -n orchestrator

# 4. Watch rollout status
kubectl rollout status deployment/api-gateway -n orchestrator
```

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap app-config -n orchestrator

# Restart pods to pick up changes
kubectl rollout restart deployment -n orchestrator
```

### Update Secrets

```bash
# Edit secrets
kubectl edit secret db-secrets -n orchestrator

# Restart pods
kubectl rollout restart deployment -n orchestrator
kubectl rollout restart statefulset -n orchestrator
```

### Scale Applications

```bash
# Manual scaling
kubectl scale deployment api-gateway --replicas=3 -n orchestrator

# Update HPA
kubectl edit hpa api-gateway-hpa -n orchestrator
```

## Monitoring Deployment

### Watch Pod Status

```bash
# Watch all pods
kubectl get pods -n orchestrator -w

# Watch specific deployment
kubectl get pods -l app=api-gateway -n orchestrator -w
```

### Check Logs

```bash
# Tail logs
kubectl logs -f -l app=api-gateway -n orchestrator

# Get logs from all replicas
kubectl logs -l app=inventory-app -n orchestrator --all-containers=true

# Get previous logs (if pod crashed)
kubectl logs <pod-name> -n orchestrator --previous
```

### Check Resource Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n orchestrator

# Check HPA status
kubectl get hpa -n orchestrator
```

## Backup and Restore

### Backup Database

```bash
# Port-forward to database
kubectl port-forward svc/inventory-db 5432:5432 -n orchestrator

# Backup using pg_dump
pg_dump -h localhost -U user01 -d inventory_db > inventory_backup.sql
```

### Restore Database

```bash
# Port-forward to database
kubectl port-forward svc/inventory-db 5432:5432 -n orchestrator

# Restore using psql
psql -h localhost -U user01 -d inventory_db < inventory_backup.sql
```

## Complete Teardown

```bash
# Delete cluster and optionally remove images
./scripts/cleanup.sh

# Or manually
./orchestrator.sh delete
```
