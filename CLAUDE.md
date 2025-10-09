# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetEOC is a Django-based disaster response application for tracking people, resources, and needs during incidents. It features multi-organization support, incident management, asset tracking, and inter-organization support request workflows.

**Key Technologies:**
- Django 5.2+ with GeoDjango for geographic features
- PostgreSQL with PostGIS extension
- Wagtail CMS for public pages
- Bootstrap 5 with Bootstrap Icons
- Python 3.12+ managed with `uv`
- Docker containerization

## Development Commands

**Package Management:**
- `uv sync` - Install dependencies
- `uv add <package>` - Add new package
- `uv add --dev <package>` - Add development package
- `uv run <command>` - Run commands in project environment

**Django Commands:**
- `uv run python manage.py runserver 127.0.0.1:8000` - Start development server
- `uv run python manage.py migrate` - Run database migrations
- `uv run python manage.py test` - Run all tests
- `uv run python manage.py test operations` - Run operations app tests
- `uv run python manage.py check --deploy` - Production deployment checks

**Code Quality:**
- `uv run ruff check` - Lint code
- `uv run ruff format` - Format code
- `uv run djlint . --reformat` - Format templates
- `uv run pre-commit run --all-files` - Run all pre-commit hooks

**Justfile Commands:**
- `just serve` - Run development server with migrations
- `just lint` - Run all linting and formatting
- `just check` - Run pre-commit hooks
- `just safe` - Run security scan
- `just run` - Build and run with Podman
- `just build` - Build and push Docker image

**Testing:**
- `./scripts/run-tests.sh` - Complete local test suite matching CI
- `uv run python manage.py test --verbosity=2` - Run tests with verbose output
- Pytest configuration in `pytest.ini` with coverage reporting

## Architecture & Key Components

**Django Apps:**
- `operations/` - Core incident management, asset tracking, time tracking
- `home/` - Wagtail CMS pages and authentication
- `user_profile/` - User profiles and organization context
- `theme/` - Base templates and styling

**Multi-Organization System:**
- Uses `django-organizations` for organization management
- Users can be members of multiple organizations
- Organization context switching via session middleware
- Custom `IncidentOrganization` model extends `AbstractOrganization`

**Key Models:**
- `Incident` - Core incident management with owner/commander roles
- `CheckIn` - Personnel check-in/out for safety tracking
- `Asset` - Equipment tracking with checkout/checkin workflow
- `TimeEntry` - Work time logging by organization
- `SupportRequest` - Inter-organization support requests

**Authentication:**
- django-allauth with SAML support
- All endpoints require login except public Wagtail pages
- Role-based permissions using django-organizations

## Database & Migrations

- PostgreSQL with PostGIS for geographic data
- Database URL configured via `DATABASE_URL` environment variable
- Migrations should be backwards compatible for blue/green deployments
- Address data normalized in separate table for reuse

## Security Requirements

- Follow OWASP security practices
- All non-public endpoints protected with `@login_required`
- Environment-based configuration with python-decouple
- Security scanning with bandit and safety
- Production security headers configured in settings

## Code Standards

- Follow Django coding conventions
- Use `uv run` prefix for all Python commands
- 100-character line length (ruff configured)
- Conventional Commits specification for commit messages
- Google-style docstrings for functions/classes
- Unit tests required for all new functionality

## Template Guidelines

- Bootstrap 5 components and Bootstrap Icons
- Don't break template tags across multiple lines
- Use `{% bootstrap_button %}` and other django-bootstrap5 components
- Templates in `operations/templates/operations/`

## Development Workflow

1. Use Test Driven Development (TDD) for new features
2. Always use `uv run` for Python commands
3. Run `just lint` and `just check` before committing
4. Write tests for new functionality in `operations/test_*.py`
5. Use the existing patterns for forms, views, and templates
6. Update documentation in `docs/` directory as needed
7. Update CHANGELOG.md with new features, fixes, and breaking changes

## Debugging

- Local debug logs written to `netoc.log` in project root
- Tail logs with `tail -f netoc.log`
- Django debug mode controlled by `DJANGO_DEBUG` environment variable
