#!/usr/bin/env bash

set -euo pipefail

OUTPUT="project_tree.txt"

# Directories to ignore
IGNORE_DIRS=(
    ".git"
    ".github"
    ".idea"
    ".vscode"
    "__pycache__"
    ".pytest_cache"
    ".mypy_cache"
    ".ruff_cache"
    ".tox"
    ".venv"
    "venv"
    "env"
    "node_modules"
    "dist"
    "build"
    "coverage"
    ".coverage"
    ".next"
    ".nuxt"
    ".cache"
    "target"
    "bin"
    "obj"
    ".terraform"
    ".pulumi"
    "auranet_docs"
    "shadowAuraNet"
    "lib"
    "include"
    "pulumi_IoC"
)

# Build tree ignore arguments
TREE_ARGS=()
for dir in "${IGNORE_DIRS[@]}"; do
    TREE_ARGS+=("-I" "$dir")
done

echo "Generating project tree..."

{
    echo "Project Tree"
    echo "============"
    echo
    tree -a "${TREE_ARGS[@]}"
} > "$OUTPUT"

echo "Saved to $OUTPUT"