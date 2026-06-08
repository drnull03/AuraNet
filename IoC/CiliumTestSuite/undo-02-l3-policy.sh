#!/bin/bash
echo "🧹 Cleaning up Baseline Apps, Unauthorized Client, and L3 Policy..."

# 1. Remove the L3 Elements
echo "Removing network policies and rogue clients..."
kubectl delete -f policy.yaml --ignore-not-found
kubectl delete -f unauthorized-client.yaml --ignore-not-found

# 2. Remove the Baseline Elements
echo "Removing baseline deployment, service, and authorized client..."
kubectl delete -f netshoot-client-pod.yaml --ignore-not-found
kubectl delete -f nginx-service.yaml --ignore-not-found
kubectl delete -f nginx-deployment.yaml --ignore-not-found

echo "✅ Cluster is clean and ready for the next test!"
