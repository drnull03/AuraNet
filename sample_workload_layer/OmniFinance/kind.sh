#!/bin/bash

# Ensure the script stops if any command fails
set -e

echo "🚀 Loading OmniFinance Docker images into the Kind cluster..."

# Load each freshly built image directly into the Kind node's cache
kind load docker-image omnifinance-db:latest --name my-cluster
echo "✅ Loaded: omnifinance-db:latest"

kind load docker-image omnifinance-account:latest --name my-cluster
echo "✅ Loaded: omnifinance-account:latest"

kind load docker-image omnifinance-loan:latest --name my-cluster
echo "✅ Loaded: omnifinance-loan:latest"

kind load docker-image omnifinance-gateway:latest --name my-cluster
echo "✅ Loaded: omnifinance-gateway:latest"

kind load docker-image omnifinance-frontend:latest --name my-cluster
echo "✅ Loaded: omnifinance-frontend:latest"

echo "🎉 All OmniFinance images have been successfully imported to Kind!"
echo "   You are now ready to run: helm install omnifinance ./helm-chart"
