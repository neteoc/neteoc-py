ARG DEBIAN_VERSION=bookworm
ARG PYTHON_VERSION=3.10
ARG UV_VERSION=latest

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

# Use the official Python image as the base image
FROM python:${PYTHON_VERSION}

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Copy and make the entrypoint script executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Specify the command to run your Django app
CMD ["gunicorn", "neteoc.wsgi:application", "--bind", "0.0.0.0:8000"]
