# Capacidad de servidor para producción — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preparar el código de Atenea (imagen y settings de prod) para correr con más capacidad de request concurrente y con healthchecks propios, sin depender solo del monitor externo — sin tocar orquestación (eso vive en el repo `services`).

**Architecture:** Cuatro cambios independientes y acumulativos sobre archivos ya existentes: gunicorn pasa de `sync` a `gthread` con threads configurables (`backend/docker-entrypoint.sh`), Postgres usa conexiones persistentes en prod (`backend/config/settings/prod.py`), y `backend/Dockerfile`/`frontend/Dockerfile` declaran `HEALTHCHECK` sobre el endpoint/puerto que cada imagen ya expone. Ninguno requiere modelos, migraciones ni endpoints nuevos — es configuración de arranque y de conexión.

**Tech Stack:** gunicorn (`gthread` worker class), Django (`DATABASES["default"]`), Docker `HEALTHCHECK` (Python `urllib` en la imagen `python:3.12-slim` del backend, `wget` de busybox en la imagen `nginx:1.27-alpine` del frontend).

**Spec:** `docs/superpowers/specs/2026-08-27-capacidad-servidor-produccion-design.md`

## Global Constraints

- `GUNICORN_WORKERS` default se mantiene en `3` (no se toca) — solo se agregan `GUNICORN_WORKER_CLASS` (default `gthread`) y `GUNICORN_THREADS` (default `4`).
- `CONN_MAX_AGE = 60`, `CONN_HEALTH_CHECKS = True` — valores exactos de la spec, solo en `config.settings.prod` (no en `base.py` ni `dev.py`).
- Healthcheck del backend: `--interval=30s --timeout=3s --start-period=15s --retries=3`, sobre `http://localhost:8000/api/health/`, usando `python -c` con `urllib` (sin `curl`/`wget`, no están en la imagen `slim`).
- Healthcheck del frontend: `--interval=30s --timeout=3s --start-period=10s --retries=3`, sobre `http://localhost/`, usando `wget --no-verbose --tries=1 --spider` (disponible vía busybox en `nginx:*-alpine`).
- Nada de esto toca `docker-compose.prod.yml` de este repo (no es lo que corre en producción) ni ningún archivo del repo `services` — eso ya tiene su propio plan.
- Commits: `[tipo][alcance] resumen` + lista de cambios, `git commit --signoff` (agrega `Signed-off-by` automáticamente), formato de `CLAUDE.md`.

---

### Task 1: Gunicorn — `worker-class` y `threads` configurables

**Files:**
- Modify: `backend/docker-entrypoint.sh:20-25` (el bloque `exec gunicorn ...`)

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces: el contenedor de `atenea-backend` arranca con `--worker-class gthread --threads 4` por default (antes: solo `sync` implícito, sin threads) — Task 3 agrega el `HEALTHCHECK` sobre este mismo proceso, sin depender de este cambio.

No hay test unitario razonable para un script de arranque de contenedor — la verificación es funcional: construir la imagen, levantarla contra Postgres/Redis reales, e inspeccionar el log de arranque de gunicorn.

- [ ] **Step 1: Editar `backend/docker-entrypoint.sh`**

Reemplazar el bloque final (después de `python manage.py migrate --noinput`):

```sh
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
```

por:

```sh
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --worker-class "${GUNICORN_WORKER_CLASS:-gthread}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
```

- [ ] **Step 2: Levantar Postgres y Redis de dev (ya trae healthcheck propio)**

Run:
```bash
docker compose -f docker-compose.dev.yml up -d postgres redis
```
Expected: ambos contenedores en estado `running (healthy)` — confirmar con `docker compose -f docker-compose.dev.yml ps`.

- [ ] **Step 3: Construir la imagen de backend con el cambio**

Run: `docker build -t atenea-backend-test ./backend`
Expected: build termina con `exit code 0`.

- [ ] **Step 4: Levantar el contenedor por fuera de compose, en la red de dev, forzando el path de producción (sin override de `command:`)**

```bash
NETWORK="$(docker compose -f docker-compose.dev.yml ps -q postgres | xargs docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
docker run -d --name atenea-backend-test-run --network "$NETWORK" \
  -e DJANGO_SETTINGS_MODULE=config.settings.prod \
  -e DJANGO_SECRET_KEY=test-key \
  -e DJANGO_ALLOWED_HOSTS=localhost \
  -e DATABASE_URL=postgres://atenea:atenea@postgres:5432/atenea \
  -e REDIS_URL=redis://redis:6379/0 \
  -e GOOGLE_OAUTH_CLIENT_ID=test \
  -e GOOGLE_OAUTH_CLIENT_SECRET=test \
  atenea-backend-test
sleep 5
```
Expected: `docker ps` muestra `atenea-backend-test-run` como `Up`, sin reinicios en loop.

- [ ] **Step 5: Confirmar en el log que gunicorn arrancó con `gthread` y 3 workers**

Run:
```bash
docker logs atenea-backend-test-run 2>&1 | grep -E "Using worker|Booting worker"
```
Expected: una línea `Using worker: gunicorn.workers.gthread.ThreadWorker` (o equivalente con `gthread` en el nombre) y exactamente 3 líneas `Booting worker with pid: ...`.

- [ ] **Step 6: Limpiar**

```bash
docker rm -f atenea-backend-test-run
docker compose -f docker-compose.dev.yml down
```

- [ ] **Step 7: Commit**

```bash
git add backend/docker-entrypoint.sh
git commit --signoff -m "[feat][backend] usar gthread con threads configurables en gunicorn" -m "- --worker-class (default gthread) y --threads (default 4) nuevos, configurables por env
- GUNICORN_WORKERS se mantiene en 3 por default — 3x4=12 slots de request concurrentes en vez de 3
- ver docs/superpowers/specs/2026-08-27-capacidad-servidor-produccion-design.md sección 1"
```

---

### Task 2: `CONN_MAX_AGE`/`CONN_HEALTH_CHECKS` en settings de prod

**Files:**
- Modify: `backend/config/settings/prod.py`

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces: `DATABASES["default"]["CONN_MAX_AGE"] == 60` y `DATABASES["default"]["CONN_HEALTH_CHECKS"] is True` cuando `DJANGO_SETTINGS_MODULE=config.settings.prod` — ninguna tarea posterior de este plan depende de esto.

No aplica un test de Django `TestCase` (correr bajo settings de prod dentro de la suite de tests, que usa `config.settings.dev` por default, no es el patrón de este repo) — se verifica cargando el módulo de settings directamente con las mismas variables dummy que ya usa `backend/Dockerfile` para `collectstatic`.

- [ ] **Step 1: Editar `backend/config/settings/prod.py`**

Agregar al final del archivo (después de las líneas de `SOCIALACCOUNT_PROVIDERS`):

```python
# Conexiones persistentes a Postgres — sin esto, Django abre y cierra una
# conexión nueva en cada request (CONN_MAX_AGE default 0). Con gunicorn
# gthread (ver docker-entrypoint.sh) el techo de conexiones concurrentes es
# GUNICORN_WORKERS × GUNICORN_THREADS, muy por debajo del max_connections
# default de Postgres — no se justifica PgBouncer a esta escala (ver spec).
DATABASES["default"]["CONN_MAX_AGE"] = 60
# Sin esto, Django podría reusar una conexión muerta (ej. tras un restart de
# Postgres) y fallar la primera request con ella en vez de abrir una nueva.
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
```

- [ ] **Step 2: Verificar que carga sin errores con settings de prod**

Run (mismas variables dummy que usa `backend/Dockerfile` para `collectstatic` — no requieren que Postgres/Redis sean alcanzables, `check` no toca la base de datos):
```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.prod \
DJANGO_SECRET_KEY=test-key \
DJANGO_ALLOWED_HOSTS=localhost \
DATABASE_URL=postgres://u:p@localhost:5432/db \
REDIS_URL=redis://localhost:6379/0 \
GOOGLE_OAUTH_CLIENT_ID=test \
GOOGLE_OAUTH_CLIENT_SECRET=test \
uv run manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Confirmar los valores exactos**

Run (mismas variables de entorno del Step 2):
```bash
DJANGO_SETTINGS_MODULE=config.settings.prod \
DJANGO_SECRET_KEY=test-key \
DJANGO_ALLOWED_HOSTS=localhost \
DATABASE_URL=postgres://u:p@localhost:5432/db \
REDIS_URL=redis://localhost:6379/0 \
GOOGLE_OAUTH_CLIENT_ID=test \
GOOGLE_OAUTH_CLIENT_SECRET=test \
uv run manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['CONN_MAX_AGE'], settings.DATABASES['default']['CONN_HEALTH_CHECKS'])"
```
Expected: `60 True`.

- [ ] **Step 4: Confirmar que settings de dev NO cambiaron (conexión por request se mantiene en desarrollo)**

Run:
```bash
uv run manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default'].get('CONN_MAX_AGE', 0))"
```
(sin `DJANGO_SETTINGS_MODULE` explícito — usa el default `config.settings.dev` de `manage.py`, y `backend/.env` ya configurado según `docs/development/getting-started.md`)

Expected: `0` (el default de Django, sin cambios en dev).

- [ ] **Step 5: Commit**

```bash
git add backend/config/settings/prod.py
git commit --signoff -m "[feat][backend] usar conexiones persistentes a Postgres en producción" -m "- CONN_MAX_AGE=60 y CONN_HEALTH_CHECKS=True, solo en config.settings.prod
- reduce el overhead de abrir/cerrar conexión en cada request
- PgBouncer descartado a esta escala — ver docs/superpowers/specs/2026-08-27-capacidad-servidor-produccion-design.md sección 2"
```

---

### Task 3: `HEALTHCHECK` en `backend/Dockerfile`

**Files:**
- Modify: `backend/Dockerfile`

**Interfaces:**
- Consumes: nada de tareas previas (el endpoint `/api/health/` ya existe en el código de `asesorias`/donde esté registrado — no se toca en este plan).
- Produces: la imagen de `atenea-backend` reporta `healthy`/`unhealthy` vía `docker inspect`/`docker ps` — el plan de `services` (fuera de alcance de este repo) lo neutraliza para `atenea-worker`, que usa la misma imagen pero no sirve HTTP.

- [ ] **Step 1: Editar `backend/Dockerfile`**

Agregar después de `EXPOSE 8000` y antes de `ENTRYPOINT`:

```dockerfile
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/', timeout=2)" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

**Nota de corrección (revisión final del branch):** el `CMD` que se implementó
también envuelve el request con un header `X-Forwarded-Proto: https`, para
evitar el loop de redirección 301 que `SECURE_SSL_REDIRECT` provoca sin él
(hallado durante la revisión de este Task 3). Además, `ALLOWED_HOSTS` en
`prod.py` necesitó `+ ["localhost"]`, porque el `Host: localhost:8000` que
manda este healthcheck no está en el `DJANGO_ALLOWED_HOSTS` real de
producción (hallado en la revisión final de todo el branch).

- [ ] **Step 2: Levantar Postgres y Redis de dev**

Run: `docker compose -f docker-compose.dev.yml up -d postgres redis`
Expected: ambos `running (healthy)`.

- [ ] **Step 3: Construir la imagen y confirmar que el `HEALTHCHECK` quedó embebido**

```bash
docker build -t atenea-backend-test ./backend
docker inspect --format='{{json .Config.Healthcheck}}' atenea-backend-test
```
Expected: JSON con `"Test":["CMD-SHELL","python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/', timeout=2)\" || exit 1"]` (o el equivalente en `["CMD", ...]` según cómo Docker lo serialice), `"Interval":30000000000`, `"Retries":3`.

- [ ] **Step 4: Levantar el contenedor y esperar a que el healthcheck corra**

```bash
NETWORK="$(docker compose -f docker-compose.dev.yml ps -q postgres | xargs docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
docker run -d --name atenea-backend-test-run --network "$NETWORK" \
  -e DJANGO_SETTINGS_MODULE=config.settings.prod \
  -e DJANGO_SECRET_KEY=test-key \
  -e DJANGO_ALLOWED_HOSTS=localhost \
  -e DATABASE_URL=postgres://atenea:atenea@postgres:5432/atenea \
  -e REDIS_URL=redis://redis:6379/0 \
  -e GOOGLE_OAUTH_CLIENT_ID=test \
  -e GOOGLE_OAUTH_CLIENT_SECRET=test \
  atenea-backend-test
sleep 50   # start_period (15s) + al menos un ciclo de interval (30s) + margen
docker inspect --format='{{.State.Health.Status}}' atenea-backend-test-run
```
Expected: `healthy`.

- [ ] **Step 5: Confirmar que un backend roto se reporta `unhealthy` (falso negativo del healthcheck sería peor que no tenerlo)**

```bash
docker exec atenea-backend-test-run pkill -f gunicorn
sleep 40
docker inspect --format='{{.State.Health.Status}}' atenea-backend-test-run
```
Expected: `unhealthy` (o `starting`→`unhealthy` tras los reintentos configurados).

- [ ] **Step 6: Limpiar**

```bash
docker rm -f atenea-backend-test-run
docker compose -f docker-compose.dev.yml down
```

- [ ] **Step 7: Commit**

```bash
git add backend/Dockerfile
git commit --signoff -m "[feat][backend] agregar HEALTHCHECK a la imagen sobre /api/health/" -m "- python -c con urllib (sin curl/wget, no están en la imagen slim)
- interval=30s timeout=3s start-period=15s retries=3
- ver docs/superpowers/specs/2026-08-27-capacidad-servidor-produccion-design.md sección 3"
```

---

### Task 4: `HEALTHCHECK` en `frontend/Dockerfile`

**Files:**
- Modify: `frontend/Dockerfile`

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces: la imagen de `atenea-frontend` reporta `healthy`/`unhealthy` vía `docker inspect`/`docker ps`.

- [ ] **Step 1: Editar `frontend/Dockerfile`**

Agregar después de `EXPOSE 80` y antes de `CMD`:

```dockerfile
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 2: Construir la imagen y confirmar que el `HEALTHCHECK` quedó embebido**

```bash
docker build -t atenea-frontend-test --build-arg VITE_API_BASE_URL=http://localhost:8000 ./frontend
docker inspect --format='{{json .Config.Healthcheck}}' atenea-frontend-test
```
Expected: JSON con `"Test":["CMD-SHELL","wget --no-verbose --tries=1 --spider http://localhost/ || exit 1"]`, `"Interval":30000000000`, `"Retries":3`.

- [ ] **Step 3: Levantar el contenedor y esperar a que el healthcheck corra**

```bash
docker run -d --name atenea-frontend-test-run -p 8080:80 \
  -e ATENEA_GOOGLE_CLIENT_ID=test \
  atenea-frontend-test
sleep 35   # start_period (10s) + al menos un ciclo de interval (30s) + margen
docker inspect --format='{{.State.Health.Status}}' atenea-frontend-test-run
curl -sf http://localhost:8080/ >/dev/null && echo "curl OK"
```
Expected: `healthy` y `curl OK`.

- [ ] **Step 4: Limpiar**

```bash
docker rm -f atenea-frontend-test-run
```

- [ ] **Step 5: Commit**

```bash
git add frontend/Dockerfile
git commit --signoff -m "[feat][frontend] agregar HEALTHCHECK a la imagen sobre /" -m "- wget --spider (busybox de nginx:alpine, sin dependencias nuevas)
- interval=30s timeout=3s start-period=10s retries=3
- ver docs/superpowers/specs/2026-08-27-capacidad-servidor-produccion-design.md sección 3"
```

---

## Verificación final

- [ ] `git log --oneline -4` muestra los 4 commits de este plan, uno por tarea, en orden.
- [ ] `docker compose -f docker-compose.dev.yml up --build` (flujo normal de dev, `docs/development/getting-started.md`) sigue arrancando sin errores — el backend en dev sigue usando `runserver` (el `command:` de `docker-compose.dev.yml` no cambió), así que ninguno de estos 4 cambios debe alterar el flujo de desarrollo día a día.
- [ ] Repasar la spec (`docs/superpowers/specs/2026-08-27-capacidad-servidor-produccion-design.md`) sección por sección contra las 4 tareas: sección 1 → Task 1, sección 2 → Task 2, sección 3 → Task 3 + Task 4, sección 4 (throttling) → sin tarea, confirmado sin cambios en la spec.
