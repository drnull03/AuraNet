#!/bin/bash

echo "🚀 Starting persistent port-forwarding for frontend-ui on port 4000..."

while true; do
    kubectl port-forward --address 0.0.0.0 svc/frontend-ui -n default 4000:80
    echo "⚠️ Port-forwarding connection dropped! Reconnecting in 2 seconds..."
    sleep 2
done
