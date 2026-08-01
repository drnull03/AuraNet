#!/usr/bin/env bash

set -euo pipefail

OUTPUT="combined_tests.txt"
SCRIPT_NAME="$(basename "$0")"

IGNORE_DIRS=(
    "node_modules"
    ".git"
    "__pycache__"
    ".venv"
    "venv"
    "dist"
    "build"
    "CelebratingTheSmallWins"
)

# Clear output file
: > "$OUTPUT"

# Build ignore expression
prune_args=()
for dir in "${IGNORE_DIRS[@]}"; do
    [[ ${#prune_args[@]} -gt 0 ]] && prune_args+=(-o)
    prune_args+=(-name "$dir")
done

find . \
    \( -type d \( "${prune_args[@]}" \) -prune \) -o \
    \( -type f \
        \( \
            -iname "*test*" \
            -o -path "*/test/*" \
            -o -path "*/tests/*" \
        \) \
        -print0 \
    \) |
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

echo "Done. Output written to $OUTPUT"