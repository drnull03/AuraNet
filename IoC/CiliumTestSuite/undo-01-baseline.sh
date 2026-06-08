#!/bin/bash
echo "🧹 Cleaning up Baseline Applications..."
kubectl delete -f netshoot-client-pod.yaml --ignore-not-found
kubectl delete -f nginx-service.yaml --ignore-not-found
kubectl delete -f nginx-deployment.yaml --ignore-not-found
