FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

# Copy project and install pinned dependencies via uv (reads uv.lock / pyproject.toml)
COPY . /app
RUN uv sync

# Ensure entrypoint exists and is executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=root.settings

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
