# NetEOC Disaster Response Application

[![Django Tests](https://github.com/neteoc/neteoc-py/actions/workflows/test.yml/badge.svg)](https://github.com/neteoc/neteoc-py/actions/workflows/test.yml)
[![Docker Image CI](https://github.com/neteoc/neteoc-py/actions/workflows/docker-image.yml/badge.svg)](https://github.com/neteoc/neteoc-py/actions/workflows/docker-image.yml)

This is a web application used in disaster response for tracking people, resources, and needs. It is designed to run completely disconnected from the internet on a laptop or a device like a Raspberry Pi.

## Overview

Basic public pages are managed by Wagtail, a Django-based CMS. The system supports multi-organization incident management with role-based access control and inter-organization support request workflows.

## Key Features

- **Multi-Organization Support**: Users can be members of multiple organizations and switch contexts
- **Incident Management**: Create, manage, and track disaster incidents with status tracking
- **Support Request Workflow**: Organizations can request support from other organizations
- **Check-in/Check-out System**: Track personnel for insurance and safety purposes
- **Geographic Support**: Built-in geographic data handling with GeoDjango
- **Offline Capability**: Designed to work without internet connectivity

## Tech Stack

- **Database**: [PostgreSQL](https://www.postgresql.org/) with [PostGIS](https://postgis.net/) extension
- **Backend**: Python with [Django](https://www.djangoproject.com/) framework
- **Geographic Features**: [GeoDjango](https://docs.djangoproject.com/en/5.1/ref/contrib/gis/)
- **Package Management**: [uv](https://docs.astral.sh/uv/)
- **Frontend**: Bootstrap 5 with Bootstrap Icons
- **CMS**: Wagtail for public pages

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL with PostGIS extension
- uv package manager

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd neteoc-py
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run database migrations:

   ```bash
   uv run python manage.py migrate
   ```

5. Create a superuser:

   ```bash
   uv run python manage.py createsuperuser
   ```

6. Start the development server:

   ```bash
   uv run python manage.py runserver 127.0.0.1:8000
   ```

### Using Justfile (Alternative)

This project includes a `justfile` for task automation:

```bash
# View available commands
just

# Run the development server
just run

# Run tests
just test

# Lint and format code
just lint
```

## Development

### Running Tests

The project includes comprehensive unit tests for all core functionality:

```bash
# Run all tests
uv run python manage.py test

# Run tests with verbose output
uv run python manage.py test --verbosity=2

# Run only operations app tests
uv run python manage.py test operations

# Run specific test class
uv run python manage.py test operations.test_models.AssetModelTest

# Run local test suite (includes linting, security scans)
./scripts/run-tests.sh
```

### Continuous Integration

Tests automatically run on every push and pull request via GitHub Actions:

- **Unit Tests**: Run on Python 3.11 and 3.12 with SQLite and PostgreSQL
- **Code Quality**: Linting with ruff, format checking
- **Security Scans**: Bandit for security vulnerabilities, Safety for dependency checks
- **Coverage Reports**: Automatically generated and uploaded to Codecov

### Test Structure

Tests are organized in the `operations/` app:

- `operations/test_models.py` - Model functionality tests (376 lines)
- `operations/test_forms_views.py` - Form validation and view tests (140 lines)
- `operations/tests.py` - Test discovery module (39 lines)

### Code Quality

The project follows Django coding standards and uses Ruff for linting and formatting:

```bash
# Check code style
uv run ruff check

# Format code
uv run ruff format

# Run pre-commit hooks
pre-commit run --all-files
```

## Documentation

Comprehensive documentation is available in the `docs` directory:

- [Documentation Index](docs/README.md) - Complete table of contents
- [Django Organizations Cookbook](docs/django-orgs-cookbook.md) - Multi-organization implementation guide
- [Incident Creation System](docs/incident-creation-system.md) - Incident management documentation
- [Organization Switching](docs/organization-switching-implementation.md) - Context switching functionality
- [Support Request Workflow](docs/support-request-implementation.md) - Inter-organization support requests

## Deployment

The application is packaged as a Docker container and can be deployed on Kubernetes clusters.

### Production Environment Configuration

For production deployments, use the production environment configuration:

1. **Create production environment file:**

   ```bash
   cp .env.production .env.production.local
   # Edit .env.production.local with your actual production values
   ```

2. **Run deployment checks:**

   ```bash
   # Using the helper script (recommended)
   ./scripts/check-production-deploy.sh

   # Or manually with your production .env file
   cp .env.production.local .env
   uv run python manage.py check --deploy
   rm .env  # Clean up
   ```

3. **Important Security Notes:**
   - Never commit `.env.production.local` or any file containing real secrets
   - The `.env.production` file is a template - replace all placeholder values
   - Production environment files are automatically excluded from Git and Docker builds

See the [deployment documentation](docs/docker-deployment.md) for detailed instructions.

## Contributing

1. Follow the coding standards outlined in the [project guidelines](.github/copilot-instructions.md)
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure all pre-commit hooks pass

## License

See [LICENSE](LICENSE) file for details.
