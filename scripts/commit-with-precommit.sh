#!/bin/bash
# Script to run pre-commit hooks, stage any changes, and commit
# Usage: ./scripts/commit-with-precommit.sh "commit message"

set -e

# Check if commit message is provided
if [ -z "$1" ]; then
    echo "Error: Please provide a commit message"
    echo "Usage: $0 \"commit message\""
    exit 1
fi

COMMIT_MSG="$1"

echo "Running pre-commit hooks..."

# Run pre-commit on all files
pre-commit run --all-files
PRECOMMIT_EXIT=$?
if [ $PRECOMMIT_EXIT -ne 0 ]; then
    echo "Warning: Some pre-commit hooks failed, but continuing with commit."
fi

# Check if there are any changes after pre-commit
if ! git diff --quiet; then
    echo "Pre-commit made changes. Adding them to staging..."
    git add -u
fi

# Check if there are any staged changes
if git diff --cached --quiet; then
    echo "No changes to commit."
    exit 0
fi

echo "Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

echo "Commit completed successfully!"
