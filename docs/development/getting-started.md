# Entorno de desarrollo — guía inicial

> Este documento se completa a medida que se crea el scaffolding real del proyecto (`/backend`, `/frontend`, `docker-compose.dev.yml`). Por ahora describe el flujo previsto según las decisiones en [`docs/decisions/`](../decisions/).

## Flujo previsto

1. `docker compose -f docker-compose.dev.yml up` levanta:
   - `backend` (Django + DRF, con autoreload)
   - `frontend` (servidor de desarrollo de Vite)
   - `celery-worker`
   - `postgres` (PostgreSQL 16, contenedor local, datos descartables)
   - `redis` (broker local para Celery)
2. Variables de entorno de desarrollo (incluyendo credenciales OAuth de Google para un proyecto de pruebas) se definen en un `.env` no versionado, siguiendo el ejemplo de `.env.example`.
3. El backend expone la API en un puerto local; el frontend consume esa API vía la URL configurada en su propio `.env`.

## Pendiente de definir al hacer el scaffolding

- Puertos exactos y nombres de servicios en `docker-compose.dev.yml`.
- Variables de entorno requeridas (`DATABASE_URL`, `REDIS_URL`, credenciales de Google OAuth, `SECRET_KEY`, etc.) y su plantilla `.env.example`.
- Comandos de migración inicial y creación de superusuario de Django.
- Comandos de lint/test para backend y frontend.

Referencia de decisiones relevantes: [0004 — Docker topology](../decisions/0004-docker-topology.md), [0005 — Dev vs prod services](../decisions/0005-dev-vs-prod-services.md).
