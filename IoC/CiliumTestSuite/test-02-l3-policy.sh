#!/bin/bash
echo "🚀 Deploying Baseline Apps, Unauthorized Client, and L3 Policy..."

# Deploy Baseline
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml
kubectl apply -f netshoot-client-pod.yaml

# Deploy L3 Elements
kubectl apply -f unauthorized-client.yaml
kubectl apply -f policy.yaml

echo "⏳ Waiting for all pods to be ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=nginx --timeout=90s
kubectl wait --for=condition=Ready pod/netshoot-client --timeout=90s
kubectl wait --for=condition=Ready pod/unauthorized-client --timeout=90s

echo "✅ Testing Authorized Client (Expect: HTTP 200)..."
kubectl exec netshoot-client -- curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://nginx-service

echo "🚫 Testing Unauthorized Client (Expect: Command terminated with exit code 28)..."
# We use || true so the script doesn't crash when curl drops as expected
kubectl exec unauthorized-client -- curl --max-time 3 -s http://nginx-service || echo "✅ Connection successfully dropped by Cilium!"
