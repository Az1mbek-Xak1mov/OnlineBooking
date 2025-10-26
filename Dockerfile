FROM ghcr.io/astral-sh/uv:python3.13-alpine

RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv pip install --system psycopg2-binary gunicorn && \
    uv sync

COPY . .

CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0:8000"]
