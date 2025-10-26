FROM python:3.13-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential gcc libpq-dev curl \
	&& rm -rf /var/lib/apt/lists/*

FROM base as builder
COPY pyproject.toml requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir -r requirements.txt

FROM base
RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
	&& chown -R app:app /app

USER app

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=root.settings

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "root.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
