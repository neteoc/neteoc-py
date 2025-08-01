# Project Overview

This is a web application used in disaster response for tracking people, stuff, and needs.

Basic public pages are managed by Wagtail, a Django-based CMS.

A user is a person. A person might not be a user. A person may be a responder or a civilian or both in any given incident.

An incident is a specific occurrence of a disaster or community event. Like a hurricane, flood, or community festival.

The owner of an incident has full administrative control over that incident in the system.

Each incident should also have a user that is the incident commander. This user is the primary point of contact for the incident and has full control over the incident. That user's information should be displayed on the incident page and easily accessible by other users who have permission to view the incident.

It is important to keep track of who has checked in and out of an incident. This is for insurance and safety purposes. The system should allow users to check in and out of incidents, and the incident owner should be able to view all check-ins for that incident. The incident owner and incident commander should also be able to delete/update check-ins if necessary.

## Project Infrastructure

The application is packaged as a Docker container and can be run using Podman.

The project uses a `justfile` for task automation, which includes commands for running the application, building the Docker image, and managing dependencies.

The application will be deployed on a kubernetes cluster, and the Docker image will be pushed to a container registry.

## Incident Creation and Management

An incident should have a primary location, a start date, and an end date. The incident should also have a status (active, standby, closed) and an incident type (hurricane, flood, etc.).

An incident should have a name that is descriptive and unique. The incident name should be used to identify the incident in the system.

An incident should have a way to attach files and documents related to the incident. This could be done through a file upload system or by linking to external documents. Those documents should be accessible to users with the appropriate permissions.

When an incident is created, the user creating the incident should be automatically set as the owner of the incident. The owner can be changed later by the incident owner or commander.

An incident should have a primary organization associated with it. This organization is the primary entity responsible for the incident and should be displayed on the incident page. Incidents should be able to be associated with other incidents, such as a parent incident or related incidents. This way each organization maintains control over their own incidents and can link them with other organization's incidents for better tracking.

## User Permissions and Access Control

Organizations should configured using [django-organizations](../docs/django-orgs-cookbook.rst)

Users should be able to sign up and create an account, however, they will not be able to do anything other than update their profile until they are invited into an organization.

## Code Style and Standards

All basic resources should have basic CRUD functionality and be accessible via the Django admin interface. CRUD functionality should also be available through the web interface for users with the appropriate permissions.

All code should follow the PEP 8 style guide for Python code. Use `uv run ruff` for linting and formatting of Python code.

Run `pre-commit run --all-files` to check code style and standards.

## Security

All endpoints other than the wagtail managed public pages should be protected by the `@login_required` decorator.

## Python Instructions

The UV tool should be used to manage python.

When running python commands use `uv run` prefixed to the command to ensure the correct environment is used.

For example:

`python manage.py runserver 127.0.0.1:8000` becomes `uv run python manage.py runserver 127.0.0.1:8000`

To install new packages use `uv add` instead of `pip install`. For development packages use `uv add --dev`

Use Django and associated projects as the primary toolkit for this project

Django REST framework should be used for any data endpoints for things like ajax calls.
https://www.django-rest-framework.org/

Geographic functions and data should make use of GeoDjango: https://docs.djangoproject.com/en/5.2/ref/contrib/gis/

Code should be checked and formatted with the tool `ruff` after any changes. There is a shortcut command in the justfile that can be used for this: `just lint`.

## UI Components

Use Bootstrap 5 for UI components. https://getbootstrap.com/docs/5.3/getting-started/introduction/

Use Bootstrap Icons library for icons: https://icons.getbootstrap.com/

## HTML Template instructions

Do not break code into multiple lines, this breaks the rendering.

Wrong:

```
   {% bootstrap_button button_type="link" content="Add" button_class="btn-primary" extra_classes="float-start"
    href="/checkin/new/" %}
```

Correct:

```
   {% bootstrap_button button_type="link" content="Add" button_class="btn-primary" extra_classes="float-start" href="/checkin/new/" %}
```

## Data instructions

Migrations, models, endpoints, etc should be backwards compatible one version so that blue/green deployments are possible.

Data should be normailzed and broken down.

### Address

An address should be in its own table and other models refer to it so that many other records can be associated with a single address.

Street 1 - Required
Street 2 - Optional
City - Required
State - Required
Zip - Required
latitude - Optional
latitude - Optional

# Debugging

When running locally, the `netoc.log` file will contain debug information. This file is located in the root of the project directory. You can tail this file to see real-time logs without needing to start a serpate server:

```bash
tail -f netoc.log
```
