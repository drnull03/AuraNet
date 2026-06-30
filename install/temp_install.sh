#!/bin/bash
# Install AuraNet Components
cd ..
COMPONENTS=("auranet-ztc" "auranet-autoheal" "auranet-agent" "auranet-controller")
NAMESPACE="auranet-namespace"

echo "🚀 Starting AuraNet Deployment..."

for comp in "${COMPONENTS[@]}"; do
    echo "-----------------------------------"
    echo "📦 Deploying $comp..."
    cd "$comp" || { echo "❌ Directory $comp not found!"; continue; }
    
    # Run the install command
    helm upgrade --install "$comp" ./chart -n "$NAMESPACE" --create-namespace
    
    cd ..
done

echo "✅ AuraNet Deployment Complete!"
