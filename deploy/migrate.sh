#!/bin/sh
set -e

echo "Starting pre-deployment migrations"

# Load environment variables
set -a
source .env.prod
set +a

# Run migrations in order for each app
echo "Running migrations for service app..."
docker compose -f docker-compose.prod.yml run --rm web uv run python manage.py migrate service

echo "Running migrations for users app..."
docker compose -f docker-compose.prod.yml run --rm web uv run python manage.py migrate users

echo "Running migrations for stats app..."
docker compose -f docker-compose.prod.yml run --rm web uv run python manage.py migrate stats

echo "Running any remaining migrations..."
docker compose -f docker-compose.prod.yml run --rm web uv run python manage.py migrate

# Create superuser if specified in env
if [ ! -z "$DJANGO_SUPERUSER_USERNAME" ] && [ ! -z "$DJANGO_SUPERUSER_EMAIL" ] && [ ! -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    docker compose -f docker-compose.prod.yml run --rm web uv run python manage.py createsuperuser --noinput || true
fi

# Collect static files
echo "Collecting static files..."
docker compose -f docker-compose.prod.yml run --rm web uv run python manage.py collectstatic --noinput

echo "Migration and static file collection completed successfully!"