#!/bin/bash

CLUSTER_NAME="orchestrator-cluster"
REGISTRY_PORT=5000

case "$1" in
    create)
        echo "Creating k3d cluster..."
        
        # Create k3d cluster with 1 server (master) and 1 agent
        k3d cluster create $CLUSTER_NAME \
            --servers 1 \
            --agents 1 \
            --port "3000:30000@loadbalancer" \
            --registry-create k3d-registry.localhost:$REGISTRY_PORT \
            --k3s-arg "--disable=traefik@server:0"
        
        if [ $? -eq 0 ]; then
            echo "Cluster created successfully"
            echo "Waiting for cluster to be ready..."
            kubectl wait --for=condition=Ready nodes --all --timeout=60s
            
            echo "Installing Traefik Ingress Controller..."
            helm repo add traefik https://traefik.github.io/charts
            helm repo update
            helm install traefik traefik/traefik \
                --namespace kube-system \
                --set ports.web.nodePort=30000
            
            echo "Applying Kubernetes manifests..."
            kubectl apply -f manifests/
            echo "Deployment complete!"
        else
            echo "Failed to create cluster"
            exit 1
        fi
        ;;
    
    start)
        echo "Starting k3d cluster..."
        k3d cluster start $CLUSTER_NAME
        if [ $? -eq 0 ]; then
            echo "Cluster started"
        else
            echo "Failed to start cluster"
            exit 1
        fi
        ;;
    
    stop)
        echo "Stopping k3d cluster..."
        k3d cluster stop $CLUSTER_NAME
        if [ $? -eq 0 ]; then
            echo "Cluster stopped"
        else
            echo "Failed to stop cluster"
            exit 1
        fi
        ;;
    
    delete)
        echo "Deleting k3d cluster..."
        k3d cluster delete $CLUSTER_NAME
        if [ $? -eq 0 ]; then
            echo "Cluster deleted"
        else
            echo "Failed to delete cluster"
            exit 1
        fi
        ;;
    
    status)
        echo "Cluster status:"
        k3d cluster list
        echo ""
        echo "Nodes:"
        kubectl get nodes
        echo ""
        echo "Pods:"
        kubectl get pods -A
        ;;
    
    *)
        echo "Usage: $0 {create|start|stop|delete|status}"
        exit 1
        ;;
esac
