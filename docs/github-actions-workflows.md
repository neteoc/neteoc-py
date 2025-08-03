# GitHub Actions Workflow Documentation

This document describes the automated testing and CI/CD workflows for the NetEOC application.

## Workflows

### 1. Django Tests (`test.yml`)

**Trigger**: Push to `main` or `asset-tracking` branches, Pull requests to `main`

**Jobs**:

#### `test` Job
- **Matrix**: Python 3.11 and 3.12
- **Database**: SQLite (for speed)
- **Steps**:
  1. Install system dependencies (GDAL, PostGIS, XML libraries)
  2. Set up Python and UV package manager
  3. Install Python dependencies
  4. Run code quality checks (ruff lint & format)
  5. Run Django system checks
  6. Run database migrations
  7. Collect static files
  8. Execute unit tests
  9. Generate coverage reports
  10. Upload coverage to Codecov

#### `test-postgres` Job
- **Database**: PostgreSQL with PostGIS extension
- **Purpose**: Ensure compatibility with production database
- **Services**: PostgreSQL 17 with PostGIS 3.5
- **Steps**: Similar to `test` job but with PostgreSQL backend

#### `security-scan` Job
- **Security Tools**:
  - **Bandit**: Python security vulnerability scanner
  - **Safety**: Dependency vulnerability checker
- **Artifacts**: Security reports uploaded for review

### 2. Docker Image CI (`docker-image.yml`)

**Trigger**: Push to `main`, Pull requests to `main`

**Purpose**: Build and publish Docker container images to GitHub Container Registry

## Environment Variables

### Test Environment
```bash
DJANGO_SETTINGS_MODULE=neteoc.settings
DJANGO_DEBUG=false
SECRET_KEY="test-secret-key-for-github-actions"
DATABASE_URL="sqlite:///test.db"  # For test job
DATABASE_URL="postgres://postgres:postgres@localhost:5432/test_neteoc"  # For postgres job
```

## Local Testing

Run the complete test suite locally:

```bash
./scripts/run-tests.sh
```

This script:
- Sets up test environment
- Runs code quality checks
- Executes Django system checks
- Runs database migrations
- Collects static files
- Executes all unit tests
- Runs security scans
- Cleans up test artifacts

## Test Coverage

The test suite includes:

- **Model Tests**: Organization, Incident, Asset, TimeEntry, SupportRequest, CheckIn models
- **Form Tests**: Validation and data integrity
- **View Tests**: Authentication, permissions, responses
- **Permission Tests**: Access control and security

**Current Coverage**: 376 lines of model tests + 140 lines of form/view tests

## Monitoring

- **Status Badges**: README displays workflow status
- **Coverage Reports**: Automatically uploaded to Codecov
- **Security Reports**: Generated and stored as artifacts
- **Failure Notifications**: GitHub automatically notifies on failures

## Troubleshooting

### Common Issues

1. **Test Database Permissions**: 
   - Solution: Workflow uses SQLite for most tests, PostgreSQL service for integration tests

2. **Missing System Dependencies**:
   - Solution: Workflow installs GDAL, PostGIS, and XML libraries

3. **UV Cache Issues**:
   - Solution: Workflow uses `astral-sh/setup-uv` with cache enabled

4. **Coverage Upload Failures**:
   - Solution: `fail_ci_if_error: false` prevents CI failure on coverage issues

### Local Development

For local testing without the full CI environment:

```bash
# Quick test run
uv run python manage.py test operations

# With coverage
uv run coverage run --source='.' manage.py test
uv run coverage report
```

## Security Considerations

- Test database credentials are safe (ephemeral test environment)
- Security scans run on every commit
- Dependencies are checked for known vulnerabilities
- Code is scanned for common security issues

## Performance Optimization

- **UV Package Manager**: Faster dependency resolution
- **Cache Strategy**: Dependencies cached between runs
- **Matrix Testing**: Parallel execution across Python versions
- **SQLite for Speed**: Most tests use SQLite for faster execution
- **PostgreSQL Integration**: Separate job ensures database compatibility
