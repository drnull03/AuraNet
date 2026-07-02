#!/usr/bin/env bash

set -euo pipefail

OUTPUT="combined.txt"

# Empty the output file
> "$OUTPUT"

find . -type f  ! -name "$OUTPUT" -print0 |
while IFS= read -r -d '' file; do
    echo "# Content of ${file#./}" >> "$OUTPUT"
    cat "$file" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
done

echo "Created $OUTPUT"
