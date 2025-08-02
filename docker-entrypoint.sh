#!/bin/bash
set -e

echo "Starting NetEOC container..."
echo "Container environment variables:"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"
echo "DATABASE_URL: ${DATABASE_URL:0:5}..." # Show first 5 chars for debugging

# Function to wait for database
wait_for_db() {
    echo "Waiting for database to be ready..."
    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Testing database connection..."

        # Try to get more detailed error information
        if python manage.py check --database default 2>&1; then
            echo "Database is ready!"
            break
        else
            echo "Database check failed. Error details above."
        fi

        if [ $attempt -eq $max_attempts ]; then
            echo "Error: Database is not ready after $max_attempts attempts"
            echo "Final attempt with verbose output:"
            python manage.py check --database default
            exit 1
        fi

        echo "Waiting 5 seconds before next attempt..."
        sleep 5
        attempt=$((attempt + 1))
    done
}

# Wait for database to be ready
wait_for_db

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting application..."
exec "$@"
