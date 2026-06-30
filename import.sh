#!/usr/bin/env bash

find . -type f -name "kind.sh" -print0 |
while IFS= read -r -d '' script; do
    echo "Executing: $script"
    "$script"
done
