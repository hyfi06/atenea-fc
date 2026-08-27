# Capacidad de servidor para producción

## Contexto

Atenea (`atenea.unam.dev`) corre en producción junto con `docs.unam.dev`
(Outline) y `monitor.unam.dev` (Uptime Kuma) en un único servidor: el
escritorio personal de Héctor (Intel i7-10700, 8 cores/16 hilos, 15GB RAM),
orquestados desde el repo `services` (`docker compose`, sin Swarm).
Población objetivo de Atenea: ~11,000 alumnos + 400 académicos, 6 personas de
SAE administrando. El tráfico esperado es en ráfagas cortas (apertura de
horarios, inicio de semestre), no sostenido — el análisis de esta spec parte
de un pico simultáneo estimado en 200-600 sesiones activas, no de la
población total.

Se revisó el código real (no solo la topología) antes de proponer cambios:
`backend/docker-entrypoint.sh`, `backend/config/settings/{base,prod}.py`,
`backend/accounts/throttling.py`, y los tres `docker-compose*.yml` de
`services`. Esta spec cubre únicamente lo que vive en el repo `atenea-fc` —
imagen, entrypoint, settings — porque viaja con el build y aplica sin
importar dónde se despliegue. Los límites de memoria/CPU, healthchecks a
nivel de contenedor, número de instancias y la concurrencia de Celery son
parámetros de *orquestación* y se definen en el plan hermano del repo
`services` (`docs/planeacion/2026_08_27_17_10_capacidad-servidor-produccion.md`),
no aquí — un `command:`/`environment:` de compose no es código de esta app,
y mezclar ambos haría que esta spec quedara desactualizada cada vez que se
ajuste un número de infraestructura sin tocar una sola línea de Atenea.

Ninguno de los cambios de esta spec es específico de un endpoint o feature
de negocio — son ajustes de cómo el proceso de la app usa los recursos que
se le dan, aplicables sin importar el tamaño final del servidor.

---

## 1 — Gunicorn: `gthread` en vez de `sync` puro

**Estado actual:** `backend/docker-entrypoint.sh` arranca gunicorn con
`--workers "${GUNICORN_WORKERS:-3}"` sin `--worker-class` ni `--threads` →
worker class `sync` por default, 3 procesos = 3 requests concurrentes como
techo absoluto, sin importar cuántos hilos tenga la máquina.

**Cambio:** agregar soporte a `GUNICORN_WORKER_CLASS` (default `gthread`) y
`GUNICORN_THREADS` (default `4`), sin tocar el default de `GUNICORN_WORKERS`:

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

Con los defaults nuevos: 3 workers × 4 threads = 12 slots de request
concurrentes en vez de 3, sin multiplicar procesos completos de Django (cada
worker sigue siendo un solo proceso — los threads comparten su memoria, así
que el footprint de RAM no se multiplica por 4). Las vistas de la API son
I/O-bound (esperan a Postgres/Redis, no CPU), que es exactamente el caso de
uso donde `gthread` gana sobre `sync` sin el riesgo de compartir estado
mutable entre threads que sí tendría código CPU-bound.

**Por qué no `gevent`/async:** requeriría auditar que ninguna dependencia
(Django ORM síncrono, `dj-rest-auth`, `django-allauth`) haga I/O bloqueante
de forma incompatible con monkey-patching — no vale la pena a esta escala.
`gthread` da la mayor parte del beneficio sin ese riesgo.

**Testing:** no hay test automatizado razonable para esto (es configuración
de arranque del proceso, no código de la app). Verificación manual tras
desplegar: `docker compose exec atenea-backend ps aux` debe mostrar 3
procesos gunicorn (más el master), y `ab`/`hey` con concurrencia >3 contra
`/api/health/` debe mostrar todas las requests atendidas en paralelo (no
serializadas).

---

## 2 — Conexiones a Postgres: `CONN_MAX_AGE`

**Estado actual:** `DATABASES["default"] = env.db("DATABASE_URL")`
(`backend/config/settings/base.py:132-134`) sin `CONN_MAX_AGE` → Django abre
y cierra una conexión nueva a Postgres en cada request (default `0`).

**Cambio**, en `backend/config/settings/prod.py` (no en `base.py` — en dev,
con un solo proceso `runserver` y recarga automática, conexiones
persistentes solo complican el ciclo de desarrollo sin beneficio real):

```python
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
```

`CONN_HEALTH_CHECKS` evita que Django reuse una conexión muerta (ej. tras un
restart de Postgres) y falle la primera request con ella — la valida antes
de reusarla.

**Por qué no PgBouncer:** con `gthread`, cada thread que toca la base abre su
propia conexión — el techo de conexiones concurrentes desde `atenea-backend`
es `workers × threads` = 3×4 = 12, más las que abra `atenea-worker` (ver plan
de `services` para su concurrencia). Aun sumando ambos, queda muy por debajo
del `max_connections` default de Postgres (100). PgBouncer agrega una pieza
de infraestructura más para operar (y otro punto de falla) sin resolver un
problema que existe a esta escala — se descarta explícitamente, no por
desconocerlo. Revisar si el número de procesos/threads concurrentes crece
mucho más allá de esto.

**Testing:** `backend/config/tests/` (o donde vivan los tests de settings, si
existen) — si no hay convención previa de testear settings de DB, verificación
manual: tras desplegar, `SELECT count(*) FROM pg_stat_activity WHERE
datname='atenea';` bajo carga normal no debe crecer sin límite ni quedarse
en un número fijo alto en reposo (conexiones persistentes que no se sueltan
nunca sería señal de fuga, no de este cambio funcionando bien).

---

## 3 — Healthcheck de imagen (`HEALTHCHECK` en los Dockerfile)

**Estado actual:** el endpoint `/api/health/` ya existe y devuelve
`{"status": "ok"}` (investigado en la sesión de debugging del 26 de agosto
sobre el falso 400 de Uptime-Kuma). Ningún `Dockerfile` del repo declara
`HEALTHCHECK` — Docker no tiene forma de saber si el proceso adentro del
contenedor sigue sano sin depender de un monitor externo.

**Cambio en `backend/Dockerfile`** (imagen usada tanto por `atenea-backend`
como por `atenea-worker` en `services` — el plan hermano neutraliza este
healthcheck para `atenea-worker`, donde no aplica un chequeo HTTP):

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/', timeout=2)" || exit 1
```

Se usa `python -c` con `urllib` (siempre disponible en la imagen, ya
`python:3.12-slim`) en vez de `curl`/`wget` — ninguno de los dos viene
instalado en la imagen `slim` de Debian y agregarlo solo para esto es peso
extra innecesario en la imagen final.

**Cambio en `frontend/Dockerfile`** (`nginx:1.27-alpine`, que sí trae `wget`
vía busybox de Alpine por default):

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
```

**Testing:** `docker build` de ambas imágenes seguido de `docker inspect
--format='{{json .Config.Healthcheck}}' <imagen>` confirma que el healthcheck
quedó embebido; `docker compose ps` tras levantar debe mostrar `(healthy)`
en vez de sin estado.

---

## 4 — Throttling: sin cambios

`CloudflareScopedRateThrottle` (`backend/accounts/throttling.py`) ya
identifica al cliente por `CF-Connecting-IP` en vez de confiar en
`X-Forwarded-For` sin `NUM_PROXIES` — el hallazgo de seguridad relacionado
(review del 19 de agosto) ya está cerrado. No hay nada que tocar aquí para
esta spec; se documenta para dejar constancia de que se revisó y se
descartó, no que se pasó por alto.

---

## Fuera de alcance (explícito)

- **Número de workers/threads/concurrencia como valores de producción**: esta
  spec agrega la *capacidad* de configurarlos vía env vars con defaults
  razonables; los valores reales para el servidor de producción (y su ajuste
  para "modo alta demanda") se fijan en `services/.env` y se documentan en el
  plan hermano de `services` — no se hardcodean acá.
- **PgBouncer**, considerado y descartado (ver sección 2).
- **Escalado horizontal (réplicas de `atenea-backend` con round-robin en
  nginx)** — requeriría cambios de `services` (resolver de DNS dinámico en
  nginx), no de este repo; fuera de alcance también ahí a esta escala (ver
  plan hermano).
- **Backups** — ya implementados en `services`, no forman parte de esta spec.
- **Migración a hosting distinto del escritorio de Héctor** — fuera de
  alcance total; si el pico de tráfico resulta sostenido (no puntual) y
  excede lo que esta spec + el plan de `services` pueden absorber, esa
  decisión se toma aparte, con su propio ADR.
