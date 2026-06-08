#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

CLUSTER_NAME="my-cluster"

echo "🧹 Step 1: Cleaning up old cluster..."
# We use || true so the script doesn't crash if the cluster doesn't exist yet
kind delete cluster --name $CLUSTER_NAME || true

echo "📦 Step 2: Booting up new 3-node cluster..."
kind create cluster --name $CLUSTER_NAME --config ./cluster/3Nodes.yaml

echo "🐝 Step 3: Installing Cilium eBPF Datapath & Hubble UI..."
# Passing these flags provisions Hubble during the initial install,
# preventing unnecessary daemonset restarts.
cilium install \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --wait

echo "✅ Step 4: Cluster is ready!"
kubectl get nodes

sleep 2

echo "🔭 Step 5: Starting Hubble UI Port Forward..."
nohup cilium hubble ui >> ../logs/hubble-port-forward.log 2>&1 &
echo "✅ Hubble UI is listening on VPS localhost:12000"
