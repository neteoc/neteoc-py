# Project Overview

This is a web application used in disaster response for tracking people, stuff, and needs.

Basic public pages are managed by Wagtail, a Django-based CMS.

A user is a person. A person might not be a user. A person may be a responder or a civilian or both in any given incident.

An incident is a specific occurrence of a disaster or community event. Like a hurricane, flood, or community festival.

The owner of an incident has full administrative control over that incident in the system.

Each incident should also have a user that is the incident commander. This user is the primary point of contact for the incident and has full control over the incident. That user's information should be displayed on the incident page and easily accessible by other users who have permission to view the incident.

It is important to keep track of who has checked in and out of an incident. This is for insurance and safety purposes. The system should allow users to check in and out of incidents, and the incident owner should be able to view all check-ins for that incident. The incident owner and incident commander should also be able to delete/update check-ins if necessary.

The National Incident Management System (NIMS) and the Incident Command System (ICS) are used to manage incidents. The system should allow for the creation of incidents, the assignment of incident commanders, and the management of incidents by those commanders.

## Example use case

The local emergency management agency (EMA) is dealing with a hurricane. The first step would be for the EMA to create an incident for that hurricane. They would fill out a form with the incident name, type, status, start date, and any other relevant information. The EMA would then assign an incident commander who would be responsible for managing the incident on behalf of the EMA. The incident commander would then be able to manage the incident, including assigning check-ins to responders and civilians.

The EMA needs to request support from another organization, such as the state defense force (SDF). They would visit the SDF's public profile page and request support. The SDF would then create an incident based on that request for support for that hurricane and assign an incident commander. The incident commander would then be able to manage the incident, including assigning check-ins to soldiers. Those two incidents would be linked together so that the EMA can see the SDF's incident and the SDF can see the EMA's incident. This way each organization maintains control over their own incidents and can link them with other organization's incidents for better tracking.

Since a user can be a member of multiple organizations, the system should allow users to switch between organizations. This is important for users who may be involved in multiple incidents across different organizations.


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

A user should have only one incident context active at any given time. A user should be able to quickly switch to another incident context if needed, but any actions should only apply to the current incident context. Other incidents should not be affected by actions taken in the current incident context.

Users should be able to see other incidents they or their organizations are involved in on a dashboard or overview page. This should include incidents they own, incidents they are a member of, and incidents they have been invited to.

The user should be able to request support from an org they are also a member of. In a disaster a Liaison Officer (LNO) could be assigned before any formal requests are made. That LNO may be the user that fills out the request on behalf of the agency they are assigned temporarily to.

The only limit on what org can be a target is that it can't be the same one that is requesting.

## Asset Management

The asset management system should allow organizations to track their assets such as radios, laptops, vehicles, etc. Each asset should have a unique identifier, a name, a description, and a status (available, in use, under maintenance, etc.). There should be categories for assets that have special data requirements, such as vehicles or radios.

Assets should be able to be checked in and out by users. When an asset is checked out, the user should be able to specify the incident it is being checked out for. The asset should then be associated with that incident until it is checked back in.

An asset checkout/checkin should be a two step process where the current holder of the asset checks it out to the new holder which puts the asset in a pending state. The new holder then checks the asset in which completes the checkout process. This allows for better tracking of assets and ensures that assets are not lost or mismanaged.

## Time Tracking

The time tracking system should allow users to log their time spent on work for an organization. 

This should be a daily log of time spend on work for an organization.

The data collected should include:

- Date: The date the work was done
- ACTIVITY DESCRIPTION
- Work Hours
- Volunteer hours
- Travel Hours
- Travel Miles
- Travel Meal Costs
- Billeting Costs
- Purchases
- Explain Purchase and Reason
- User: The user who logged the time
- Organization: The organization the time is logged for

The spreadsheet based system that this is replacing has an example file in the 'docs' directory named `time_example_2025.ods`. This file should be used as a reference for the data that needs to be collected.

tT he data shown should be for the indivuial user and should be filtered by the user's current organization context. The user should only be able to see their own time entries, but the organization owner or incident commander should be able to see all time entries for the organization or incident.

## Support Request Workflow

The support request workflow allows organizations to request support from other organizations for incidents. This is useful for coordinating disaster response efforts between different organizations. A user should be able to create a draft request and save it for later, or submit it immediately.

A user with the appropriate permissions should be able to create a support request for an incident. Other users from the same organization should be able to view the support request and its status as well as cancel it.

A support request should collect the following information:

- Form data
  - Name: Default to the requesting organization's incident name
  - Description: Details about the support needed
  - Location name: The name of the location where support is needed. For example: County EOC, City Hall, etc.
  - Location address 1: The street address of the location where support is needed
  - Location address 2: Optional second line for the street address
  - Location city: The city where the location is
  - Location state: The state where the location is
  - Location zip: The zip code of the location
  - Start date: When the support is needed to start
  - End date: When the support is needed to end, estimate is fine, this can be updated later.
  - Urgency level: How urgent the support request is (low, medium, high, life safety)
- User: the user making the request
- Requesting organization: the organization making the request
- Target organization: the organization being requested for support
- Related incident: the incident this support request is related to

Support requests should have the following statuses:

- Draft: The request is being prepared and not yet submitted
- Pending: The request has been submitted and is awaiting review
- Approved: The request has been approved by the target organization
- Declined: The request has been declined by the target organization
- Fulfilled: The request has been fulfilled and support has been provided
- Cancelled: The request has been cancelled by the requesting organization

## User Permissions and Access Control

Organizations should be configured using [django-organizations](../docs/django-orgs-cookbook.rst)

Users should be able to sign up and create an account, however, they will not be able to do anything other than update their profile until they are invited into an organization.

## Code Style and Standards

Security should be a primary concern in all code written for this project. The code shall follow best practices for security, including but not limited to: 
Application Security Verification Standard (ASVS) Level 1, OWASP Top Ten, and secure coding practices.

Any documentation should be written in markdown (.md) format and should be placed in the `docs` directory. This excludes the projects main [README.md]('../README.md') file which should be in the root directory. A table of contents should be included in the `docs` directory [README.md](../docs/README.md) file that links to the rest of the documentation in the `docs` directory.

The main readme file should be used to provide an overview of the project, how to run it locally, and any other relevant information. Deeper or more specific documentation should be placed in the `docs` directory with links to it in the main readme file.

The project should follow the [Django coding style guide](https://docs.djangoproject.com/en/5.2/internals/contributing/writing-code/coding-style/) and the [Django REST framework style guide](https://www.django-rest-framework.org/topics/documenting-your-api/#style-guide).

Functions, classes, and methods should be documented using docstrings. The docstrings should follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

All basic resources should have basic CRUD functionality and be accessible via the Django admin interface. CRUD functionality should also be available through the web interface for users with the appropriate permissions.

All code should follow the PEP 8 style guide for Python code. Use `uv run ruff` for linting and formatting of Python code.

Run `pre-commit run --all-files` to check code style and standards.

unit tests should be created for all new functionality and should be placed in the `tests` directory. All tests should be run using `uv run python manage.py test`. Tests should be written using the django test framework and should follow the [Django testing documentation](https://docs.djangoproject.com/en/5.2/topics/testing/overview/).

## Security

All endpoints other than the wagtail managed public pages should be protected by the `@login_required` decorator.

## Python Instructions

The UV tool should be used to manage python.

ALWAYS USE `uv run` to run python commands. This ensures that the correct environment is used and that the command is run in the context of the project.

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
