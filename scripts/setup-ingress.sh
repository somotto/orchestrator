#!/bin/bash

echo "=== Setting up Ingress Controller ==="
echo ""

# Install Traefik (default k3d ingress controller)
echo "Applying Ingress manifest..."
kubectl apply -f manifests/09-ingress.yaml

# Wait for ingress to be ready
echo "Waiting for ingress to be ready..."
kubectl wait --for=condition=Ready ingress/orchestrator-ingress -n orchestrator --timeout=60s

# Add entry to /etc/hosts
echo ""
echo "To access via hostname, add this to /etc/hosts:"
echo "127.0.0.1 orchestrator.local"
echo ""
echo "Then access the application at: http://orchestrator.local:3000"
echo ""
echo "Or continue using: http://localhost:3000"
