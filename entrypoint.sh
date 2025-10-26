#!/usr/bin/env bash
set -e

# entrypoint: run migrations, collectstatic (if asked), then exec passed command
echo "Starting entrypoint"

if [ "$DJANGO_MIGRATE" != "false" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput || true
fi

if [ "$DJANGO_COLLECTSTATIC" != "false" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput || true
fi

exec "$@"
