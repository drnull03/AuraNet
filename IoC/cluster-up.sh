#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

CLUSTER_NAME="auranet"

echo "🧹 Step 1: Cleaning up old cluster..."
# We use || true so the script doesn't crash if the cluster doesn't exist yet
kind delete cluster --name $CLUSTER_NAME || true

echo "📦 Step 2: Booting up new 3-node cluster..."
kind create cluster --name $CLUSTER_NAME --config ./cluster/3Nodes.yaml


echo "🐝 Step 4: Installing Cilium eBPF Datapath..."
# We use --wait so the script pauses until the CNI is fully functional
cilium install --wait

echo "✅ Step 5: Cluster is ready!"
kubectl get nodes
