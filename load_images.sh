#!/bin/bash

CLUSTER_NAME="my-cluster"

echo "Scanning local Docker registry for auranet/ images..."

# Query Docker for images and tags, then grep for the 'auranet/' prefix
IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^auranet/' || true)

# Check if any images were found
if [ -z "$IMAGES" ]; then
    echo "No auranet/ images found locally. Skipping load."
    exit 0
fi

# Loop through the found images and load them into Kind
for IMAGE in $IMAGES; do
    echo "🐝 Sideloading $IMAGE into $CLUSTER_NAME..."
    kind load docker-image "$IMAGE" --name "$CLUSTER_NAME"
done

echo "✅ All AuraNet images loaded successfully!"
