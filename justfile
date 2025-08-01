migrate:
    uv run python manage.py maintenance_mode on
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py maintenance_mode off

check:
    pre-commit run --all-files
    pre-commit install

lint:
    uv run ruff check --fix --exit-zero
    uv run ruff format

serve:
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py runserver

env:
    source .venv/bin/activate

export:
    uv export --frozen --no-hashes --output-file=requirements.txt

run:
    podman build -t netoc:latest .
    podman-compose up
