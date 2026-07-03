#!/usr/bin/env bash

OUTPUT="combined.txt"
SCRIPT_NAME="$(basename "$0")"

IGNORE_DIRS=("node_modules" ".git" "dist" "build" "assets")
IGNORE_FILES=("combined.txt" "$SCRIPT_NAME" "package-lock.json")

> "$OUTPUT"

PRUNE_EXPR=()
for dir in "${IGNORE_DIRS[@]}"; do
  PRUNE_EXPR+=( -path "./$dir" -o )
done
unset 'PRUNE_EXPR[${#PRUNE_EXPR[@]}-1]'  # remove last -o

FILE_EXPR=()
for file in "${IGNORE_FILES[@]}"; do
  FILE_EXPR+=( ! -name "$file" )
done

find . \
  \( "${PRUNE_EXPR[@]}" \) -prune -o \
  -type f \
  ! -name "*.sh" \
  "${FILE_EXPR[@]}" \
  -print | while read -r file; do

  echo "# content of $file" >> "$OUTPUT"
  cat "$file" >> "$OUTPUT"
  echo >> "$OUTPUT"

done
