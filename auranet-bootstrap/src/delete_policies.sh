#!/bin/bash

POLICIES_DIR="./policies"

echo "🗑️  Starting AuraNet Policy Teardown..."

# Check if the directory exists
if [ ! -d "$POLICIES_DIR" ]; then
  echo "❌ Error: Directory $POLICIES_DIR does not exist."
  exit 1
fi

# Iterate through all yaml and yml files in the directory
for file in "$POLICIES_DIR"/*.yaml "$POLICIES_DIR"/*.yml; do
    # Check if the file actually exists (handles cases where no files match the extension)
    if [ -f "$file" ]; then
        echo " Deleting resources from: $file"
        kubectl delete -f "$file" --ignore-not-found=true
    fi
done

echo "✅ All policies from $POLICIES_DIR have been successfully deleted from the cluster."