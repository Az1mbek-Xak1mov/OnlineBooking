FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

COPY ./ /app

RUN uv sync

CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0:8000"]
