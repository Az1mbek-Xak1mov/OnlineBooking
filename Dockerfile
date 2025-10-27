FROM ghcr.io/astral-sh/uv:python3.13-alpine

RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv run python -m ensurepip && \
    uv run python -m pip install --upgrade pip setuptools wheel && \
    uv run python -m pip install psycopg2-binary gunicorn && \
    uv sync --frozen --no-install-project

COPY . .

# copy and enable entrypoint script
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0:8000"]
