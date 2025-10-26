#!/bin/sh
set -e

# entrypoint: run migrations & collectstatic using `uv run` so commands run inside
# the environment created by `uv sync` (the image may not have system python packages)
echo "Starting entrypoint"

UV_CMD="uv run"

if [ "$DJANGO_MIGRATE" != "false" ]; then
  echo "Running migrations..."
  $UV_CMD python manage.py migrate --noinput || true
fi

if [ "$DJANGO_COLLECTSTATIC" != "false" ]; then
  echo "Collecting static files..."
  $UV_CMD python manage.py collectstatic --noinput || true
fi

exec "$@"
