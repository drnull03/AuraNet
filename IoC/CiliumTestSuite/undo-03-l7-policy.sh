#!/bin/bash
echo "🧹 Cleaning up Baseline Apps and Layer 7 Policy..."

# 1. Remove the L7 Policy
echo "Removing L7 network policy..."
kubectl delete -f l7-policy.yaml --ignore-not-found

# 2. Remove the Baseline Elements
echo "Removing baseline deployment, service, and authorized client..."
kubectl delete -f netshoot-client-pod.yaml --ignore-not-found
kubectl delete -f nginx-service.yaml --ignore-not-found
kubectl delete -f nginx-deployment.yaml --ignore-not-found

echo "✅ Cluster is clean and ready for the next test!"
