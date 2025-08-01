#!/bin/bash
set -e

echo "Starting NetEOC container..."

# Function to wait for database
wait_for_db() {
    echo "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if python manage.py check --database default >/dev/null 2>&1; then
            echo "Database is ready!"
            break
        fi

        echo "Database not ready, attempt $attempt/$max_attempts. Waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done

    if [ $attempt -gt $max_attempts ]; then
        echo "Error: Database is not ready after $max_attempts attempts"
        exit 1
    fi
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
