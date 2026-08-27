#!/bin/sh
# Entrypoint del contenedor backend.
#
# Con ENTRYPOINT fijo, cualquier `command:` del compose llega aquí como argumentos
# ("$@") en vez de reemplazar el proceso. Por eso:
#   - Si se pasa un comando (worker Celery, runserver de dev, un management command),
#     se ejecuta tal cual SIN migrar — el worker no debe correr migraciones y el
#     flujo de dev las aplica a mano (ver docs/development/getting-started.md).
#   - Sin comando (caso de prod), aplicamos migraciones y arrancamos gunicorn.
# collectstatic ya corrió en build (ver Dockerfile).
set -e

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --worker-class "${GUNICORN_WORKER_CLASS:-gthread}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
