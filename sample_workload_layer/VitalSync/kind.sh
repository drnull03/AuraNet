
kind load docker-image vitalsync-db:latest --name my-cluster
echo "✅ Loaded: vitalsync-db:latest"

kind load docker-image vitalsync-records:latest --name my-cluster
echo "✅ Loaded: vitalsync-records:latest"

kind load docker-image vitalsync-imaging:latest --name my-cluster
echo "✅ Loaded: vitalsync-imaging:latest"

kind load docker-image vitalsync-gateway:latest --name my-cluster
echo "✅ Loaded: vitalsync-gateway:latest"

kind load docker-image vitalsync-portal:latest --name my-cluster
echo "✅ Loaded: vitalsync-portal:latest"

echo ""
echo "🎉 All VitalSync images have been successfully imported to my-cluster!"

echo ""
echo "⚙️ Step 3: Deploying VitalSync via Helm..."
# Note: This assumes you have created a helm-chart folder similar to OmniFinance
# helm upgrade --install vitalsync ./helm-chart

echo ""
echo "🌟 VitalSync image setup complete! You are ready to deploy to the cluster."
