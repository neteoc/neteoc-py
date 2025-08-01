# Project Overview

This is a web application used in disaster response for tracking people, stuff, and needs.

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

Code should be checked and formated with the tool `ruff` after any changes. There is a shortcut command in the justfile that can be used for this: `just lint`.


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
