# Project Overview

This is a web application used in disaster response for tracking people, stuff, and needs.

## Python Instructions

When running python commands use `uv run` prefixed to the command to ensure the corrent envroment is used.

For example:

`python manage.py runserver 127.0.0.1:8000` becomes `uv run python manage.py runserver 127.0.0.1:8000`


## HTML Template instructions

Do not break code into mutiple lines, this breaks the rendering.

Wrong:
```
   {% bootstrap_button button_type="link" content="Add" button_class="btn-primary" extra_classes="float-start"
    href="/checkin/new/" %}
```

Correct:
```
   {% bootstrap_button button_type="link" content="Add" button_class="btn-primary" extra_classes="float-start" href="/checkin/new/" %}
```
