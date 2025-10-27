#!/bin/sh
set -e

make mig

# collect static files for admin and others
uv run python manage.py collectstatic --noinput

exec "$@"
