#!/usr/bin/env bash

set -euo pipefail

find . -type f -name "Dockerfile" | while read -r dockerfile; do
    dir=$(dirname "$dockerfile")
    image_name=$(basename "$dir" | tr '[:upper:]' '[:lower:]')

    echo "Building $image_name from $dockerfile..."

    docker build \
        -t "$image_name:latest" \
        -f "$dockerfile" \
        "$dir"
done
