FROM python:3.12-slim AS builder

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# collectstatic con el manifest de prod (WhiteNoise). Requiere que los settings
# importen sin fallar, así que pasamos envs dummy solo para este comando —no tocan
# la base de datos ni persisten en la imagen. Los valores reales llegan en runtime.
RUN DJANGO_SECRET_KEY=build-only \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgres://u:p@localhost:5432/db \
    REDIS_URL=redis://localhost:6379/0 \
    GOOGLE_OAUTH_CLIENT_ID=build \
    GOOGLE_OAUTH_CLIENT_SECRET=build \
    python manage.py collectstatic --noinput

# Usuario no-root; dueño de /app para que migrate/gunicorn y los estáticos escriban.
RUN adduser --system --group --no-create-home appuser \
    && chown -R appuser:appuser /app \
    && chmod +x /app/docker-entrypoint.sh
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
