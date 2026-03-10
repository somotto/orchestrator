#!/bin/bash

REGISTRY="k3d-registry.localhost:5000"

echo "Building Docker images..."

# Build inventory-db
docker build -t ${REGISTRY}/inventory-db:latest srcs/postgres-db/
docker push ${REGISTRY}/inventory-db:latest

# Build billing-db (same image as inventory-db)
docker tag ${REGISTRY}/inventory-db:latest ${REGISTRY}/billing-db:latest
docker push ${REGISTRY}/billing-db:latest

# Build RabbitMQ
docker build -t ${REGISTRY}/rabbitmq:latest srcs/rabbitmq/
docker push ${REGISTRY}/rabbitmq:latest

# Build inventory-app
docker build -t ${REGISTRY}/inventory-app:latest srcs/inventory-app/
docker push ${REGISTRY}/inventory-app:latest

# Build billing-app
docker build -t ${REGISTRY}/billing-app:latest srcs/billing-app/
docker push ${REGISTRY}/billing-app:latest

# Build api-gateway
docker build -t ${REGISTRY}/api-gateway:latest srcs/api-gateway-app/
docker push ${REGISTRY}/api-gateway:latest

echo "All images built and pushed successfully!"
