#!/bin/bash
# Script to run pre-commit hooks and stage changes
# This version is designed to work with VS Code's source control
# Usage: ./scripts/precommit-stage.sh

set -e

echo "Running pre-commit hooks..."

# Run pre-commit on staged files only
if ! pre-commit run; then
    echo "Warning: Some pre-commit hooks failed. Review the output above."
fi

# Check if there are any changes after pre-commit
if ! git diff --quiet; then
    echo "Pre-commit made changes. Adding them to staging..."
    git add -u
    echo "Changes staged. You can now commit through VS Code."
else
    echo "Pre-commit completed with no additional changes."
fi
