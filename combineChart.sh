#!/usr/bin/env bash

set -euo pipefail

OUTPUT="charts_combined.txt"
SCRIPT_NAME="$(basename "$0")"

# Directories to ignore while searching
IGNORE_DIRS=(
    "node_modules"
    ".git"
    "__pycache__"
    ".venv"
    "venv"
    "dist"
    "build"
)

# Clear output file
: > "$OUTPUT"

# Build prune expression
prune_args=()
for dir in "${IGNORE_DIRS[@]}"; do
    if [[ ${#prune_args[@]} -gt 0 ]]; then
        prune_args+=(-o)
    fi
    prune_args+=(-name "$dir")
done

# Find every directory named "chart"
find . \
    \( -type d \( "${prune_args[@]}" \) -prune \) -o \
    \( -type d -name "chart" -print0 \) |
while IFS= read -r -d '' chart_dir; do

    find "$chart_dir" -type f -print0 |
    sort -z |
    while IFS= read -r -d '' file; do

        [[ "$(basename "$file")" == "$SCRIPT_NAME" ]] && continue
        [[ "$(basename "$file")" == "$OUTPUT" ]] && continue

        {
            echo "# $(basename "$file")"
            echo "# Path: $file"
            echo
            cat "$file"
            echo
            echo
        } >> "$OUTPUT"

    done
done

echo "Done. Output written to $OUTPUT"
