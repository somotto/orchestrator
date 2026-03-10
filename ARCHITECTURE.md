# Architecture Documentation

## System Overview

The Orchestrator project is a microservices-based movie inventory and billing system deployed on Kubernetes. It demonstrates key concepts of container orchestration, service discovery, message queuing, and persistent storage.

## Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Client/User   │
                                    └────────┬────────┘
                                             │
                                             │ HTTP :3000
                                             ▼
                                    ┌─────────────────┐
                                    │  API Gateway    │
                                    │  (Deployment)   │
                                    │  HPA: 1-3       │
                                    └────┬───────┬────┘
                                         │       │
                    ┌────────────────────┘       └──────────────────┐
                    │                                               │
                    │ HTTP :8080                          RabbitMQ  │
                    ▼                                     Message   │
           ┌─────────────────┐                                     │
           │ Inventory App   │                                     │
           │  (Deployment)   │                                     ▼
           │  HPA: 1-3       │                            ┌─────────────────┐
           └────────┬────────┘                            │  Billing Queue  │
                    │                                     │  (StatefulSet)  │
                    │ PostgreSQL :5432                    │  RabbitMQ       │
                    ▼                                     └────────┬────────┘
           ┌─────────────────┐                                    │
           │  Inventory DB   │                                    │ Consume
           │  (StatefulSet)  │                                    │ Messages
           │  PostgreSQL     │                                    ▼
           │  PVC: 1Gi       │                            ┌─────────────────┐
           └─────────────────┘                            │  Billing App    │
                                                          │  (StatefulSet)  │
                                                          └────────┬────────┘
                                                                   │
                                                                   │ PostgreSQL :5432
                                                                   ▼
                                                          ┌─────────────────┐
                                                          │   Billing DB    │
                                                          │  (StatefulSet)  │
                                                          │  PostgreSQL     │
                                                          │  PVC: 1Gi       │
                                                          └─────────────────┘
```

## Components

### 1. API Gateway (api-gateway-app)

**Type**: Deployment with HPA  
**Language**: Python (Flask)  
**Port**: 3000  
**Replicas**: 1-3 (auto-scales at 60% CPU)

**Responsibilities**:
- Entry point for all client requests
- Routes `/api/movies/*` requests to Inventory Service
- Sends billing orders to RabbitMQ queue via `/api/billing/` endpoint
- Implements request proxying and error handling

**Key Files**:
- `app/proxy.py`: HTTP request forwarding to inventory service
- `app/queue_sender.py`: RabbitMQ message publishing
- `server.py`: Flask application entry point

**Environment Variables**:
- `APIGATEWAY_PORT`: Service port (3000)
- `INVENTORY_APP_HOST`: Inventory service hostname
- `INVENTORY_APP_PORT`: Inventory service port
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE`

### 2. Inventory Service (inventory-app)

**Type**: Deployment with HPA  
**Language**: Python (Flask + SQLAlchemy)  
**Port**: 8080  
**Replicas**: 1-3 (auto-scales at 60% CPU)

**Responsibilities**:
- Manages movie catalog (CRUD operations)
- Provides REST API for movie data
- Connects to PostgreSQL database
- Supports filtering by title

**API Endpoints**:
- `GET /api/movies` - List all movies (with optional ?title filter)
- `POST /api/movies` - Create new movie
- `GET /api/movies/:id` - Get movie by ID
- `PUT /api/movies/:id` - Update movie
- `DELETE /api/movies/:id` - Delete movie
- `DELETE /api/movies` - Delete all movies

**Key Files**:
- `app/movies.py`: Movie model and REST endpoints
- `app/extensions.py`: SQLAlchemy database setup
- `server.py`: Application entry point

**Database Schema**:
```sql
CREATE TABLE movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description VARCHAR
);
```

### 3. Billing Service (billing-app)

**Type**: StatefulSet  
**Language**: Python (SQLAlchemy + Pika)  
**Port**: 5000  
**Replicas**: 1 (single consumer)

**Responsibilities**:
- Consumes order messages from RabbitMQ queue
- Stores orders in PostgreSQL database
- Acknowledges messages after successful processing
- Runs as long-lived consumer process

**Key Files**:
- `app/consume_queue.py`: RabbitMQ consumer implementation
- `app/orders.py`: Order model and database operations
- `server.py`: Consumer startup

**Database Schema**:
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    number_of_items INTEGER NOT NULL,
    total_amount FLOAT NOT NULL
);
```

**Message Format**:
```json
{
  "user_id": 123,
  "number_of_items": 2,
  "total_amount": 29.99
}
```

### 4. Inventory Database (inventory-db)

**Type**: StatefulSet  
**Technology**: PostgreSQL 13  
**Port**: 5432  
**Storage**: 1Gi PVC

**Responsibilities**:
- Persistent storage for movie data
- Provides PostgreSQL database service
- Initialized with custom user and database

**Initialization**:
- Creates database user from secrets
- Creates `inventory_db` database
- Configures remote access
- Data persists across pod restarts

### 5. Billing Database (billing-db)

**Type**: StatefulSet  
**Technology**: PostgreSQL 13  
**Port**: 5432  
**Storage**: 1Gi PVC

**Responsibilities**:
- Persistent storage for order data
- Provides PostgreSQL database service
- Initialized with custom user and database

**Initialization**:
- Creates database user from secrets
- Creates `billing_db` database
- Configures remote access
- Data persists across pod restarts

### 6. Message Queue (billing-queue)

**Type**: StatefulSet  
**Technology**: RabbitMQ  
**Ports**: 5672 (AMQP), 15672 (Management UI)  
**Storage**: 1Gi PVC

**Responsibilities**:
- Asynchronous message delivery
- Decouples API Gateway from Billing Service
- Ensures message durability
- Provides management interface

**Queue Configuration**:
- Queue name: `billing_queue`
- Durable: Yes
- Auto-delete: No

## Design Decisions

### Why Deployments for API Gateway and Inventory App?

**Stateless Nature**: Both services don't maintain local state between requests. All data is stored in databases.

**Horizontal Scaling**: Can handle increased load by adding more replicas. Each replica is identical and interchangeable.

**Rolling Updates**: Easy to update without downtime. New pods are created before old ones are terminated.

**Load Balancing**: Kubernetes Service automatically distributes traffic across all replicas.

### Why StatefulSet for Billing App?

**Single Consumer Pattern**: RabbitMQ queue should have one consumer to process messages in order and avoid duplicate processing.

**Stable Identity**: StatefulSet provides predictable pod name (billing-app-0) useful for debugging and monitoring.

**Ordered Deployment**: Ensures proper startup sequence.

**Future Scaling**: If needed, can implement competing consumers pattern with multiple replicas.

### Why StatefulSets for Databases?

**Persistent Identity**: Each database pod has a stable network identity (inventory-db-0, billing-db-0).

**Persistent Storage**: PVCs are bound to specific pods. If a pod is rescheduled, it reattaches to the same volume.

**Ordered Operations**: Databases require careful startup and shutdown sequences.

**Data Integrity**: Prevents data loss during pod restarts or node failures.

### Why RabbitMQ for Async Processing?

**Decoupling**: API Gateway doesn't wait for billing processing to complete. Responds immediately to client.

**Reliability**: Messages are persisted. If billing service is down, messages queue up and are processed when it recovers.

**Scalability**: Can handle traffic spikes. Messages are processed at billing service's pace.

**Fault Tolerance**: Acknowledgment mechanism ensures messages aren't lost if processing fails.

## Kubernetes Resources

### Namespace

**Name**: `orchestrator`  
**Purpose**: Isolates all project resources from other workloads

### Secrets

**db-secrets**:
- `INVENTORY_DB_USER`, `INVENTORY_DB_PASSWORD`, `INVENTORY_DB_NAME`
- `BILLING_DB_USER`, `BILLING_DB_PASSWORD`, `BILLING_DB_NAME`

**rabbitmq-secrets**:
- `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE`

**Security Note**: In production, use external secret management (Vault, AWS Secrets Manager, etc.)

### ConfigMap

**app-config**:
- `RABBITMQ_PORT`: 5672
- `INVENTORY_APP_PORT`: 8080
- `BILLING_APP_PORT`: 5000
- `APIGATEWAY_PORT`: 3000

### Services

| Service | Type | Port | Target |
|---------|------|------|--------|
| api-gateway | NodePort | 3000 → 30000 | api-gateway pods |
| inventory-app | ClusterIP | 8080 | inventory-app pods |
| billing-app | ClusterIP (Headless) | 5000 | billing-app-0 |
| inventory-db | ClusterIP (Headless) | 5432 | inventory-db-0 |
| billing-db | ClusterIP (Headless) | 5432 | billing-db-0 |
| billing-queue | ClusterIP (Headless) | 5672, 15672 | billing-queue-0 |

### Horizontal Pod Autoscalers

**api-gateway-hpa**:
- Min replicas: 1
- Max replicas: 3
- Target CPU: 60%

**inventory-app-hpa**:
- Min replicas: 1
- Max replicas: 3
- Target CPU: 60%

### Persistent Volume Claims

| PVC | Size | Access Mode | Used By |
|-----|------|-------------|---------|
| inventory-data | 1Gi | ReadWriteOnce | inventory-db-0 |
| billing-data | 1Gi | ReadWriteOnce | billing-db-0 |
| rabbitmq-data | 1Gi | ReadWriteOnce | billing-queue-0 |

## Network Flow

### Movie Retrieval Flow

1. Client sends `GET http://localhost:3000/api/movies`
2. Request hits API Gateway NodePort service
3. API Gateway proxies to `http://inventory-app:8080/api/movies`
4. Inventory App queries PostgreSQL at `inventory-db:5432`
5. Response flows back through API Gateway to client

### Order Creation Flow

1. Client sends `POST http://localhost:3000/api/billing/` with order JSON
2. API Gateway receives request
3. API Gateway publishes message to RabbitMQ at `billing-queue:5672`
4. API Gateway responds immediately to client
5. Billing App consumes message from queue
6. Billing App inserts order into PostgreSQL at `billing-db:5432`
7. Billing App acknowledges message to RabbitMQ

## Scaling Behavior

### Load Increase Scenario

1. Traffic to API Gateway increases
2. CPU usage rises above 60%
3. HPA detects high CPU usage
4. HPA creates additional API Gateway pods (up to 3)
5. Service load balances across all pods
6. CPU usage normalizes

### Load Decrease Scenario

1. Traffic decreases
2. CPU usage drops below 60%
3. HPA waits for stabilization period
4. HPA removes excess pods (down to 1)
5. Resources are freed

## Failure Scenarios

### Pod Failure

**Deployment pods** (API Gateway, Inventory App):
- Kubernetes detects pod failure
- New pod is scheduled immediately
- Service routes traffic to healthy pods
- No data loss (stateless)

**StatefulSet pods** (Databases, RabbitMQ, Billing App):
- Kubernetes detects pod failure
- New pod is scheduled with same identity
- PVC is reattached to new pod
- Data is preserved

### Node Failure

- All pods on failed node are rescheduled
- StatefulSet pods reattach to their PVCs
- Services update endpoints automatically
- Brief downtime during rescheduling

### Database Failure

- Application pods retry connections
- StatefulSet controller restarts database pod
- PVC ensures data persistence
- Applications reconnect automatically

### RabbitMQ Failure

- Messages in queue are persisted to disk
- API Gateway may fail to publish (returns error to client)
- When RabbitMQ recovers, billing app resumes processing
- No message loss for acknowledged messages

## Performance Considerations

### Resource Limits

- API Gateway and Inventory App have CPU/memory limits
- Prevents resource exhaustion
- Enables fair scheduling across nodes

### Database Connections

- Applications use connection pooling (SQLAlchemy)
- Reduces connection overhead
- Improves query performance

### Message Queue

- Durable queues ensure persistence
- Prefetch count controls consumer throughput
- Acknowledgments prevent message loss

## Security Considerations

### Secrets Management

- Credentials stored as Kubernetes secrets
- Mounted as environment variables
- Not hardcoded in images or manifests

### Network Policies

- Currently not implemented
- Could restrict pod-to-pod communication
- Would follow principle of least privilege

### Image Security

- Base images: python:3.12-alpine, debian:bullseye
- Should scan for vulnerabilities
- Should use specific version tags in production

### Database Access

- Databases not exposed externally
- Only accessible within cluster
- Require authentication

## Monitoring and Observability

### Logs

```bash
# Application logs
kubectl logs -l app=api-gateway -n orchestrator
kubectl logs -l app=inventory-app -n orchestrator
kubectl logs -l app=billing-app -n orchestrator

# Database logs
kubectl logs inventory-db-0 -n orchestrator
kubectl logs billing-db-0 -n orchestrator

# RabbitMQ logs
kubectl logs billing-queue-0 -n orchestrator
```

### Metrics

```bash
# Resource usage
kubectl top pods -n orchestrator
kubectl top nodes

# HPA status
kubectl get hpa -n orchestrator
```

### Health Checks

Currently not implemented. Should add:
- Liveness probes: Restart unhealthy pods
- Readiness probes: Remove from service until ready
- Startup probes: Allow slow-starting containers

## Future Enhancements

1. **Ingress Controller**: Replace NodePort with Ingress for better routing
2. **Health Checks**: Add liveness and readiness probes
3. **Monitoring**: Deploy Prometheus and Grafana
4. **Logging**: Centralized logging with ELK or Loki
5. **Network Policies**: Restrict inter-pod communication
6. **Resource Quotas**: Limit namespace resource usage
7. **Pod Disruption Budgets**: Ensure availability during updates
8. **Init Containers**: Wait for dependencies before starting
9. **Service Mesh**: Istio or Linkerd for advanced traffic management
10. **GitOps**: ArgoCD or Flux for declarative deployments
