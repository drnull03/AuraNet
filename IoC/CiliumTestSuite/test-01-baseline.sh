#!/bin/bash
echo "🚀 Deploying Baseline Applications..."
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml
kubectl apply -f netshoot-client-pod.yaml

echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=nginx --timeout=90s
kubectl wait --for=condition=Ready pod/netshoot-client --timeout=90s

echo "🌐 Testing baseline connectivity (Expect: Welcome to nginx!)..."
kubectl exec netshoot-client -- curl -s http://nginx-service
echo ""
