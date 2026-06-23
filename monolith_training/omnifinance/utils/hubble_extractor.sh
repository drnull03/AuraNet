#!/bin/bash

echo "🐝 Connecting to Hubble and extracting eBPF telemetry..."

# Ensure the output directory exists
mkdir -p ../data/raw

# We use the hubble CLI to observe the last 5 minutes of traffic in the default namespace
# Outputting strictly as JSON so pandas can parse it later
hubble observe \
  --namespace default \
  --since 5m \
  --output json > ../data/raw/hubble_testing_data.json

# Count the lines to verify data was captured
RECORD_COUNT=$(wc -l < ../data/raw/hubble_testing_data.json)

echo "✅ Extraction complete!"
echo "📁 Saved $RECORD_COUNT network flow records to monolith_training/data/raw/hubble_training_data.json"
