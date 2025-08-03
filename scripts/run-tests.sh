#!/bin/bash
# Local test runner script for NetEOC
# This script mimics the GitHub Actions workflow for local testing

set -e

echo "🚀 Starting NetEOC Local Test Suite"
echo "=================================="

# Set environment variables for testing
export DJANGO_SETTINGS_MODULE=neteoc.settings
export DJANGO_DEBUG=false
export SECRET_KEY="test-secret-key-for-local-testing"
export DATABASE_URL="sqlite:///test_local.db"

echo "📦 Installing dependencies..."
uv sync --frozen

echo "🔍 Running code quality checks..."
echo "  - Linting with ruff..."
uv run ruff check .

echo "  - Format check with ruff..."
uv run ruff format --check .

echo "🔧 Running Django system checks..."
uv run python manage.py check --deploy

echo "📊 Running database migrations..."
uv run python manage.py migrate

echo "📁 Collecting static files..."
uv run python manage.py collectstatic --noinput

echo "🧪 Running unit tests..."
echo "  - All tests..."
uv run python manage.py test --verbosity=2

echo "  - Operations tests specifically..."
uv run python manage.py test operations --verbosity=2

echo "🛡️  Running security scans..."
echo "  - Installing security tools..."
uv run pip install bandit safety

echo "  - Running Bandit security scan..."
uv run bandit -r . -ll

echo "  - Running Safety security scan..."
uv run safety check

echo ""
echo "✅ All tests passed! Ready for production."
echo "🎉 Local test suite completed successfully."

# Clean up test database
rm -f test_local.db

echo "🧹 Cleaned up test artifacts."
