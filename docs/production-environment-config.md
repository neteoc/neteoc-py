# Production Environment Configuration

This guide explains how to configure and validate production environment settings for NetEOC deployment.

## Overview

NetEOC uses environment variables for configuration management through the `python-decouple` library. For production deployments, you need to create a separate environment configuration that can be used for deployment validation without exposing secrets in version control.

## Files and Security

### Environment Files

- `.env.production` - **Template file** with placeholder values (safe to commit)
- `.env.production.local` - **Your actual production config** (NEVER commit this)
- `.env` - **Development/runtime config** (ignored by Git)

### Security Guarantees

- All production environment files are excluded from Git via `.gitignore`
- All production environment files are excluded from Docker builds via `.dockerignore`
- The template file contains only safe placeholder values

## Setup Process

### 1. Create Your Production Configuration

Copy the template and customize it with your real values:

```bash
cp .env.production .env.production.local
```

Edit `.env.production.local` and replace all placeholder values:

```bash
# Example of what to change:
DJANGO_SECRET_KEY=your-actual-secret-key-here
DJANGO_ALLOWED_HOSTS=myapp.com,www.myapp.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/neteoc
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### 2. Validate Configuration

Use the provided script to run deployment checks:

```bash
./scripts/check-production-deploy.sh
```

This script will:

- Temporarily load your production settings
- Run Django's `--deploy` checks
- Clean up afterwards
- Restore your original `.env` if it existed

### 3. Manual Validation (Alternative)

If you prefer to run checks manually:

```bash
# Backup current .env if it exists
cp .env .env.backup

# Load production settings
cp .env.production.local .env

# Run deployment checks
uv run python manage.py check --deploy

# Clean up
rm .env
mv .env.backup .env  # Restore if needed
```

## Critical Production Settings

### Security Headers

```bash
DJANGO_DEBUG=False
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

### Cookie Security

```bash
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SESSION_COOKIE_HTTPONLY=True
DJANGO_CSRF_COOKIE_HTTPONLY=True
```

### Content Security

```bash
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF=True
DJANGO_SECURE_BROWSER_XSS_FILTER=True
DJANGO_X_FRAME_OPTIONS=DENY
```

### Network Configuration

```bash
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com,load-balancer.internal
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Common Deployment Checks

The `python manage.py check --deploy` command validates:

- SECRET_KEY is not using default/weak values
- DEBUG is disabled
- ALLOWED_HOSTS is properly configured
- SSL/HTTPS settings are secure
- Session and CSRF cookies are secure
- Security headers are enabled

## Storage Configuration

For production file storage using Cloudflare R2:

```bash
AWS_ACCESS_KEY_ID=your-r2-access-key
AWS_SECRET_ACCESS_KEY=your-r2-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=auto
AWS_LOCATION=production
AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
```

## Database Configuration

For production PostgreSQL with PostGIS:

```bash
DATABASE_URL=postgresql://username:password@host:5432/database_name
```

Ensure your database has the PostGIS extension installed:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## Troubleshooting

### Common Issues

1. **SECRET_KEY warnings**: Generate a new secret key for production
2. **ALLOWED_HOSTS errors**: Include all domains that will access your app
3. **SSL redirect issues**: Ensure your load balancer/proxy handles SSL termination correctly
4. **CSRF errors**: Verify CSRF_TRUSTED_ORIGINS includes all your domains with protocol

### Generating a Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Best Practices

1. **Never commit real secrets** - Use the template system
2. **Test locally first** - Run deployment checks before deploying
3. **Use strong secrets** - Generate new keys for production
4. **Document your setup** - Keep notes on your production configuration
5. **Regular rotation** - Periodically rotate secrets and keys

## Integration with CI/CD

You can integrate production validation into your deployment pipeline:

```bash
# In your CI/CD script
cp .env.production.template .env
# Inject secrets from your CI/CD secret store
echo "DJANGO_SECRET_KEY=$PRODUCTION_SECRET_KEY" >> .env
echo "DATABASE_URL=$PRODUCTION_DATABASE_URL" >> .env
# ... other secrets

# Validate configuration
uv run python manage.py check --deploy

# Clean up
rm .env
```
