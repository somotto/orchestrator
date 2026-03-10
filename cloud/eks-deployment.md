# AWS EKS Deployment Guide

## Prerequisites

1. AWS CLI configured with credentials
2. eksctl installed
3. kubectl installed
4. Helm installed

## Setup EKS Cluster

### 1. Create EKS Cluster

```bash
eksctl create cluster \
  --name orchestrator-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed
```

### 2. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name orchestrator-cluster
kubectl get nodes
```

### 3. Install EBS CSI Driver (for persistent volumes)

```bash
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster orchestrator-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve \
  --role-only \
  --role-name AmazonEKS_EBS_CSI_DriverRole

eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster orchestrator-cluster \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole \
  --force
```

### 4. Create ECR Repositories

```bash
# Create repositories for each service
aws ecr create-repository --repository-name orchestrator/api-gateway
aws ecr create-repository --repository-name orchestrator/inventory-app
aws ecr create-repository --repository-name orchestrator/billing-app
aws ecr create-repository --repository-name orchestrator/postgres-db
aws ecr create-repository --repository-name orchestrator/rabbitmq
```

### 5. Build and Push Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Set ECR registry
export ECR_REGISTRY=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t $ECR_REGISTRY/orchestrator/api-gateway:latest srcs/api-gateway-app/
docker push $ECR_REGISTRY/orchestrator/api-gateway:latest

docker build -t $ECR_REGISTRY/orchestrator/inventory-app:latest srcs/inventory-app/
docker push $ECR_REGISTRY/orchestrator/inventory-app:latest

docker build -t $ECR_REGISTRY/orchestrator/billing-app:latest srcs/billing-app/
docker push $ECR_REGISTRY/orchestrator/billing-app:latest

docker build -t $ECR_REGISTRY/orchestrator/postgres-db:latest srcs/postgres-db/
docker push $ECR_REGISTRY/orchestrator/postgres-db:latest

docker build -t $ECR_REGISTRY/orchestrator/rabbitmq:latest srcs/rabbitmq/
docker push $ECR_REGISTRY/orchestrator/rabbitmq:latest
```

### 6. Update Manifests for EKS

Update image references in manifests to use ECR:
```yaml
image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/orchestrator/api-gateway:latest
```

### 7. Deploy Application

```bash
kubectl apply -f manifests/
```

### 8. Install AWS Load Balancer Controller

```bash
eksctl utils associate-iam-oidc-provider --region=us-east-1 --cluster=orchestrator-cluster --approve

curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

eksctl create iamserviceaccount \
  --cluster=orchestrator-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=orchestrator-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 9. Create Ingress with ALB

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orchestrator-ingress
  namespace: orchestrator
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 3000
```

### 10. Get Load Balancer URL

```bash
kubectl get ingress -n orchestrator
# Wait for ADDRESS to be populated
# Use the ALB DNS name to access your application
```

## Monitoring on EKS

```bash
# Install monitoring stack
./scripts/setup-monitoring.sh

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3001:80

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 9090:80
```

## Cleanup

```bash
# Delete application
kubectl delete namespace orchestrator

# Delete monitoring
kubectl delete namespace monitoring
kubectl delete namespace kubernetes-dashboard

# Delete cluster
eksctl delete cluster --name orchestrator-cluster --region us-east-1
```

## Cost Optimization

- Use t3.medium nodes (2 vCPU, 4GB RAM)
- Enable cluster autoscaler
- Use Spot instances for non-critical workloads
- Set resource requests and limits
- Monitor with AWS Cost Explorer

## Security Best Practices

- Enable EKS cluster encryption
- Use IAM roles for service accounts (IRSA)
- Enable VPC flow logs
- Use AWS Secrets Manager for sensitive data
- Enable pod security policies
- Use private subnets for worker nodes
