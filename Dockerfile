# Build arguments
ARG DEBIAN_VERSION=bookworm
ARG PYTHON_VERSION=3.12
ARG UV_VERSION=latest

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

# Use the official Python image as the base image
FROM python:${PYTHON_VERSION}

# Install system dependencies for GeoDjango
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialite-dev \
    spatialite-bin \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GeoDjango
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so.32
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so.1

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
