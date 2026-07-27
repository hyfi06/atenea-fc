# 0009 — Settings divididos (base/dev/prod) + django-environ

**Status:** Accepted
**Date:** 2026-07-27

## Context

[0005](0005-dev-vs-prod-services.md) ya fijó que dev y prod usan distintos servicios de datos (Postgres/Redis locales vs externos) configurados por variables de entorno (`DATABASE_URL`, `REDIS_URL`). El backend Django necesita una forma concreta de leer esas variables y de separar configuración que sí difiere entre entornos (DEBUG, ALLOWED_HOSTS, seguridad de cookies) de la que no.

## Decision

- Dividir `config/settings/` en `base.py` (todo lo común: `INSTALLED_APPS`, `AUTH_USER_MODEL`, `DATABASES`, `REST_FRAMEWORK`, `CELERY_*`, allauth), `dev.py` (`from .base import *` + overrides de desarrollo) y `prod.py` (`from .base import *` + overrides de producción).
- Usar [django-environ](https://django-environ.readthedocs.io/) para leer `.env`/variables de entorno, incluyendo `env.db("DATABASE_URL")` que castea directo a la estructura `DATABASES` de Django.
- `manage.py`, `wsgi.py` y `asgi.py` usan `config.settings.dev` como default; los despliegues de producción deben fijar `DJANGO_SETTINGS_MODULE=config.settings.prod` explícitamente vía el entorno del contenedor.

## Consequences

- Ningún valor de configuración sensible (`SECRET_KEY`, credenciales de base de datos) vive hardcodeado en el código — todo entra por variables de entorno.
- Agregar un nuevo ajuste que difiere entre entornos es tan simple como agregarlo en `dev.py`/`prod.py`; lo que no cambia vive una sola vez en `base.py`.
- Riesgo a vigilar: si un despliegue de producción olvida fijar `DJANGO_SETTINGS_MODULE`, cae silenciosamente en `dev` (con `DEBUG=True`). Se documenta como chequeo explícito antes de desplegar.

## Alternatives considered

- **Un solo `settings.py` con `if os.environ.get("ENV") == "prod"`:** funciona para proyectos muy pequeños, pero mezcla en un solo archivo lo que es igual entre entornos con lo que no, y crece mal conforme se agregan más diferencias.
- **`python-decouple` en vez de `django-environ`:** alternativa similar y válida, pero `django-environ` tiene soporte directo para `env.db()`/`env.cache()` que encaja mejor con el patrón `DATABASE_URL`/`REDIS_URL` ya decidido en [0005](0005-dev-vs-prod-services.md).
