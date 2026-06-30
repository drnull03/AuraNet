#!/bin/bash
# Uninstall AuraNet Components
cd ..
COMPONENTS=("auranet-ztc" "auranet-autoheal" "auranet-agent" "auranet-controller")
NAMESPACE="auranet-namespace"

echo "tarting AuraNet Cleanup..."

for comp in "${COMPONENTS[@]}"; do
    echo "-----------------------------------"
    echo "Removing release: $comp..."
    
    # Uninstall the helm release
    helm uninstall "$comp" -n "$NAMESPACE"
done

echo "-----------------------------------"
echo "✅ AuraNet Uninstallation Complete!"
