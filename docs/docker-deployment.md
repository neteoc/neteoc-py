# Docker Deployment

This document describes how to deploy NetEOC using Docker containers with automatic database migrations.

## Container Features

The Docker container has been configured to automatically:

1. Install GeoDjango dependencies (GDAL, GEOS, PROJ, SpatiaLite)
2. Wait for the database to be ready
3. Run database migrations on startup
4. Collect static files
5. Start the Django application

## GeoDjango Requirements

NetEOC uses GeoDjango for geographic functionality, which requires several system libraries:

- **GDAL** (Geospatial Data Abstraction Library)
- **GEOS** (Geometry Engine - Open Source)
- **PROJ** (Cartographic Projections Library)
- **SpatiaLite** (Spatial extension for SQLite)

These are automatically installed in the Docker container.

## Building the Image

```bash
# Build the image
just build

# Or manually:
podman build . -t neteoc/web:latest
```

## Running with Docker Compose

The application includes a `compose.yml` file for easy deployment:

```bash
# Run the application
just run

# Or manually:
podman-compose up
```

## Environment Variables

The application requires the following environment variables (configured in `.env`):

- `DJANGO_DEBUG` - Set to False for production
- `DJANGO_SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection string
- `DJANGO_DEVELOPMENT_MODE` - Development mode flag
- `LOGLEVEL` - Logging level
- `DJANGO_ALLOWED_HOSTS` - Comma-separated list of allowed hosts

## Database Configuration

The container will automatically:

1. Wait up to 60 seconds for the database to be ready
2. Run `python manage.py migrate --noinput` to apply migrations
3. Run `python manage.py collectstatic --noinput --clear` to collect static files

If the database is not ready after 30 attempts (60 seconds), the container will exit with an error.

## Static Files

Static files are collected automatically on container startup. For production deployments, consider using a CDN or external static file storage.

## Logs

Container logs will show the startup process including:

- Database readiness checks
- Migration status
- Static file collection
- Application startup

## Production Considerations

1. Set `DJANGO_DEBUG=False` in production
2. Configure proper `DJANGO_ALLOWED_HOSTS`
3. Use a production-ready database (PostgreSQL recommended)
4. Consider using external static file storage (AWS S3, Digital Ocean Spaces, etc.)
5. Configure proper logging and monitoring
6. Use HTTPS in production

## Troubleshooting

### Database Connection Issues

If the container fails to start due to database connection issues:

1. Verify the `DATABASE_URL` is correct
2. Ensure the database server is running and accessible
3. Check firewall settings and network connectivity

### Migration Issues

If migrations fail:

1. Check the container logs for specific error messages
2. Verify database permissions
3. Ensure the database schema is compatible

### Static Files Issues

If static files are not loading:

1. Check the `STATIC_URL` and `STATIC_ROOT` settings
2. Verify static file collection completed successfully
3. Consider using external static file storage for production
