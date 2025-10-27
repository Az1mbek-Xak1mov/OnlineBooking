#!/bin/sh
set -e

# Run Django migrations (use uv so we don't depend on make inside the image)
uv run python manage.py migrate --noinput

# Collect static files so admin assets are available
uv run python manage.py collectstatic --noinput

# Execute the container CMD (starts gunicorn)
exec "$@"
