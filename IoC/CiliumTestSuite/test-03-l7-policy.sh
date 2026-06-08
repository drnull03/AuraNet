#!/bin/bash
echo "🚀 Deploying Baseline Apps and Layer 7 Network Policy..."

# 1. Deploy Baseline
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml
kubectl apply -f netshoot-client-pod.yaml

# 2. Deploy L7 Policy (This routes traffic through Envoy)
kubectl apply -f l7-policy.yaml

echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=nginx --timeout=90s
kubectl wait --for=condition=Ready pod/netshoot-client --timeout=90s

echo "✅ Testing Allowed Path /index.html (Expect: Welcome to nginx!)..."
kubectl exec netshoot-client -- curl -s http://nginx-service/index.html
echo ""

echo "🚫 Testing Denied Path /50x.html (Expect: Access denied)..."
# We expect a 403 Access Denied from Envoy here.
kubectl exec netshoot-client -- curl -s http://nginx-service/50x.html || echo "✅ Request blocked by Envoy!"
echo ""
