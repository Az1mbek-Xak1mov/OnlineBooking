#!/bin/sh
set -e

# entrypoint: run migrations & collectstatic using `uv run` so commands run inside
# the environment created by `uv sync`
echo "Starting entrypoint"

UV_CMD="uv run"

if [ "$DJANGO_MIGRATE" != "false" ]; then
    echo "Running migrations in order..."

    # Run migrations for each app in proper order
    echo "Running migrations for service app..."
    $UV_CMD python manage.py migrate service || true

    echo "Running migrations for users app..."
    $UV_CMD python manage.py migrate users || true

    echo "Running migrations for stats app..."
    $UV_CMD python manage.py migrate stats || true

    echo "Running any remaining migrations..."
    $UV_CMD python manage.py migrate || true
fi

if [ "$DJANGO_COLLECTSTATIC" != "false" ]; then
    echo "Collecting static files..."
    $UV_CMD python manage.py collectstatic --noinput || true
fi

# Start Gunicorn
exec "$@"
