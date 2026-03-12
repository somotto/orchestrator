#!/bin/bash

API_URL="http://localhost:3000"

echo "=== Load Testing Orchestrator ==="
echo ""
echo "This will generate load to test HPA scaling"
echo "Watch HPA with: kubectl get hpa -n orchestrator -w"
echo ""

# Check if hey is installed
if ! command -v hey &> /dev/null; then
    echo "Installing 'hey' load testing tool..."
    go install github.com/rakyll/hey@latest
    export PATH=$PATH:$(go env GOPATH)/bin
fi

echo "Starting load test for 2 minutes with 50 concurrent requests..."
echo ""

# Run load test
hey -z 120s -c 50 -q 10 ${API_URL}/api/movies

echo ""
echo "Load test complete!"
echo ""
echo "Check scaling results:"
echo "kubectl get hpa -n orchestrator"
echo "kubectl get pods -n orchestrator"
