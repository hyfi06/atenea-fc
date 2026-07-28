# Entorno de desarrollo — guía inicial

El `frontend` todavía no existe (se agrega en su propia pasada); esta guía cubre el backend, que ya arranca de verdad.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Docker y Docker Compose.

## Configuración inicial

1. Copiar `backend/.env.example` a `backend/.env` y ajustar `DJANGO_SECRET_KEY` (cualquier string largo aleatorio sirve en dev).
2. Instalar dependencias: `cd backend && uv sync`.

## Flujo con Docker Compose (recomendado)

```
docker compose -f docker-compose.dev.yml up --build
```

Levanta `postgres` (16, datos descartables en un volumen), `redis`, `backend` (Django con autoreload en `http://localhost:8000`) y `celery-worker`. `DATABASE_URL`/`REDIS_URL` se fijan automáticamente a los hostnames de los servicios de Compose (`postgres`/`redis`), independientemente de lo que tenga `backend/.env`.

En otra terminal:

```
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

Verificar que responde:

```
curl http://localhost:8000/api/health/
# {"status": "ok"}
```

Admin de Django en `http://localhost:8000/admin/` con el superusuario creado (pide email, no username).

## Flujo nativo con `uv` (sin bind-mount, más rápido para iterar)

Requiere Postgres/Redis alcanzables — lo más simple es levantar solo esos dos servicios con Compose y correr Django directo con `uv`:

```
docker compose -f docker-compose.dev.yml up -d postgres redis

cd backend
uv sync
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

En este flujo, `backend/.env` sí se usa tal cual (`DATABASE_URL`/`REDIS_URL` apuntando a `localhost`, ya que los puertos de Postgres/Redis están publicados al host).

## Comandos útiles

```
uv run manage.py check                              # valida settings/apps sin tocar la base de datos
uv run manage.py makemigrations --check --dry-run    # confirma que no faltan migraciones
docker compose -f docker-compose.dev.yml logs celery-worker   # debe decir "ready.", no crash-loop
docker compose -f docker-compose.dev.yml down          # apagar todo (los datos de postgres persisten en el volumen)
```

## Pendiente

- `docker-compose.prod.yml`: se pospuso — todavía no hay nada que probar de verdad en producción (sin auth real, sin tareas Celery reales, sin decisiones de registry/secrets). Ver [0004](../decisions/0004-docker-topology.md) y [0005](../decisions/0005-dev-vs-prod-services.md).
- `frontend/`: pendiente de su propia pasada de scaffolding.
- Wiring funcional de Google OAuth y de tareas Celery reales: siguiente paso incremental (ver [0003](../decisions/0003-google-oauth-allauth-jwt.md)).
