migrate:
    uv run python manage.py maintenance_mode on
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py maintenance_mode off

check:
    uv run pre-commit run --all-files
    uv run pre-commit install

lint:
    uv run ruff check --fix --exit-zero
    uv run ruff format
    uv run djlint . --reformat
    uv run djlint . --lint


serve:
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py runserver 0.0.0.0:8111

env:
    source .venv/bin/activate

export:
    uv export --frozen --no-hashes --output-file=requirements.txt

run:
    podman build . -t neteoc/web
    podman-compose up

build:
    podman build . -t neteoc/web
    podman push neteoc/web:latest
