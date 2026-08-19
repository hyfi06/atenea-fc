# Runbook — Despliegue de Atenea a producción

Guía operativa para desplegar Atenea (SPA + API) en el ecosistema `services/`
(repo `fc-sae/services`). Decisiones de fondo en
[ADR 0025](../decisions/0025-despliegue-produccion-ghcr.md).

**Modelo:** las imágenes se publican en GHCR **al hacer merge a `main`** de este repo
(`atenea-fc`); el servidor las consume con `make deploy` (que hace `docker compose pull`).
Todo el estado (Postgres, Redis) y la orquestación (nginx, Cloudflare) viven en
`services/` — **este repo no se despliega directo**; su `docker-compose.prod.yml` propio
es solo referencia de dev aislado.

**Topología:** Cloudflare (TLS) → cloudflared → nginx central (HTTP) → contenedores en
`sae-network`. Todo bajo un único origen `atenea.unam.dev` (mismo origen SPA + API, sin
CORS).

```
                          atenea.unam.dev
Cloudflare ── cloudflared ──> nginx ──┬── /api/ /admin/ /static/ ──> atenea-backend:8000
                                      └── /  (resto)              ──> atenea-frontend:80
                                                   atenea-worker (Celery) ── atenea-redis
                                          atenea-backend/worker ── atenea-db (postgres:16)
```

---

## 0. Prerrequisitos

- Merge a `main` en `atenea-fc` **verde**: el workflow *Publicar imágenes* dejó en GHCR
  `ghcr.io/hyfi06/atenea-backend:latest` y `ghcr.io/hyfi06/atenea-frontend:latest`.
  - El CI **no** necesita secretos/variables de Atenea: el client id de Google se
    inyecta en runtime (ver paso 2), no se hornea en la imagen.
  - Las imágenes de GHCR nacen **privadas**. Para que el servidor pueda hacer `pull`:
    o bien marcarlas *Public* (GHCR → package → *Package settings → Change visibility*),
    o hacer `docker login ghcr.io` en el servidor con un PAT de solo lectura de packages.
- Acceso SSH al servidor donde corre `services/`, y a su archivo `.env`.
- Permisos para editar la config de Cloudflare Tunnel y el proyecto de Google Cloud.

---

## 1. Secretos en `services/.env`

En el servidor, generar y agregar los secretos de Atenea. El script existente ya cubre
`ATENEA_DB_PASSWORD`; falta `ATENEA_SECRET_KEY` y las credenciales de Google.

```bash
cd ~/services
# ATENEA_DB_PASSWORD sale de scripts/gen-secrets.sh (si aún no está en .env, correrlo).
# Secret key de Django:
echo "ATENEA_SECRET_KEY=$(openssl rand -hex 50)" >> .env
```

Agregar al `.env` (valores reales del proyecto de Google Cloud):

```dotenv
# ── Atenea ──
ATENEA_DB_PASSWORD=...           # ya generado por gen-secrets.sh
ATENEA_SECRET_KEY=...            # openssl rand -hex 50
ATENEA_GOOGLE_CLIENT_ID=...      # OAuth client id (mismo que el del SPA)
ATENEA_GOOGLE_CLIENT_SECRET=...  # OAuth client secret
ATENEA_EMAIL_HOST_USER=...       # cuenta dedicada de Workspace, ver ADR 0028
ATENEA_EMAIL_HOST_PASSWORD=...   # app password de 16 caracteres de esa cuenta
```

> **Rotación:** durante la preparación quedaron expuestos en texto plano un
> `DJANGO_SECRET_KEY`, un `GOOGLE_OAUTH_CLIENT_SECRET` y un
> `VITE_GOOGLE_OAUTH_CLIENT_SECRET` (este último ya removido del frontend). Los valores
> de prod deben ser **nuevos** (rotar el client secret en Google Cloud; generar la secret
> key con `openssl`), nunca los `.env` de desarrollo.

Reflejar los nombres nuevos en `services/.env.example` y, opcionalmente, agregar
`ATENEA_SECRET_KEY` al bloque de `services/scripts/gen-secrets.sh`.

---

## 2. Servicios en `services/docker-compose.yml`

Agregar tres servicios sobre `sae-network` (`atenea-db` y `atenea-redis` ya existen):

```yaml
  atenea-backend:
    image: ghcr.io/hyfi06/atenea-backend:latest
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.prod
      - DJANGO_SECRET_KEY=${ATENEA_SECRET_KEY}
      - DJANGO_ALLOWED_HOSTS=atenea.unam.dev
      - DATABASE_URL=postgres://atenea:${ATENEA_DB_PASSWORD}@atenea-db:5432/atenea
      - REDIS_URL=redis://atenea-redis:6379/0
      - FRONTEND_URL=https://atenea.unam.dev
      - GOOGLE_OAUTH_CLIENT_ID=${ATENEA_GOOGLE_CLIENT_ID}
      - GOOGLE_OAUTH_CLIENT_SECRET=${ATENEA_GOOGLE_CLIENT_SECRET}
      # Email vía SMTP de Google Workspace, cuenta dedicada (ADR 0028).
      - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      - EMAIL_HOST_USER=${ATENEA_EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${ATENEA_EMAIL_HOST_PASSWORD}
      - DEFAULT_FROM_EMAIL=${ATENEA_EMAIL_HOST_USER}
    networks: [sae-network]
    depends_on: [atenea-db, atenea-redis]

  atenea-worker:
    image: ghcr.io/hyfi06/atenea-backend:latest   # misma imagen
    command: celery -A config worker -l info      # NO pasa por migrate (ver entrypoint)
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.prod
      - DJANGO_SECRET_KEY=${ATENEA_SECRET_KEY}
      - DJANGO_ALLOWED_HOSTS=atenea.unam.dev
      - DATABASE_URL=postgres://atenea:${ATENEA_DB_PASSWORD}@atenea-db:5432/atenea
      - REDIS_URL=redis://atenea-redis:6379/0
      - FRONTEND_URL=https://atenea.unam.dev
      - GOOGLE_OAUTH_CLIENT_ID=${ATENEA_GOOGLE_CLIENT_ID}
      - GOOGLE_OAUTH_CLIENT_SECRET=${ATENEA_GOOGLE_CLIENT_SECRET}
      # asesorias/tasks.py envía correo desde el worker (recordatorios, avisos).
      - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      - EMAIL_HOST_USER=${ATENEA_EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${ATENEA_EMAIL_HOST_PASSWORD}
      - DEFAULT_FROM_EMAIL=${ATENEA_EMAIL_HOST_USER}
    networks: [sae-network]
    depends_on: [atenea-db, atenea-redis]

  atenea-frontend:
    image: ghcr.io/hyfi06/atenea-frontend:latest
    environment:
      # El SPA lee el client id de Google en runtime desde /config.js, que el
      # contenedor regenera al arrancar con este valor (ver src/config.ts). No es
      # secreto (viaja en el bundle), pero se centraliza aquí en services/.env.
      - ATENEA_GOOGLE_CLIENT_ID=${ATENEA_GOOGLE_CLIENT_ID}
    networks: [sae-network]
    depends_on: [atenea-backend]
```

Y las restart policies en `services/docker-compose.prod.yml`:

```yaml
  atenea-backend:
    restart: unless-stopped
  atenea-worker:
    restart: unless-stopped
  atenea-frontend:
    restart: unless-stopped
```

> El backend aplica migraciones solo al arrancar sin `command:` (su entrypoint). El worker
> pasa `command: celery …`, por lo que **no** migra — evita dobles migraciones en paralelo.

---

## 3. Vhost nginx (`services/nginx/conf.d/atenea.conf`)

Un solo server, mismo origen. Backend para `/api/`, `/admin/`, `/static/`; el resto al SPA.

```nginx
server {
    listen 80;
    server_name atenea.unam.dev;
    client_max_body_size 20m;

    location ~ ^/(api|admin|static)/ {
        proxy_pass         http://atenea-backend:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        proxy_pass         http://atenea-frontend:80;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

> `X-Forwarded-Proto https` es lo que permite que el backend (con
> `SECURE_PROXY_SSL_HEADER`) no entre en loop de redirección. Es el mismo patrón que
> `nginx/conf.d/outline.conf`. Si `nginx` lista `depends_on`, agregar `atenea-frontend` y
> `atenea-backend`.

> **Gotcha — 502 en `/api/` y `/admin/` tras un deploy.** El `proxy_pass` de arriba usa
> hostnames (`atenea-backend`, `atenea-frontend`) sin `resolver`, así que nginx los resuelve
> **una sola vez al arrancar** y cachea la IP. Cuando `make deploy` corre `docker compose up -d`
> y recrea esos contenedores con imagen nueva, obtienen **IPs nuevas** pero nginx no se recrea:
> sigue apuntando a la IP vieja y devuelve **502** en las rutas del backend (el login se rompe;
> `/api` y `/admin` *sin* barra final caen al SPA y muestran el 404). Por eso el target `deploy`
> del `Makefile` de `services/` reinicia nginx (`$(COMPOSE) restart nginx`) tras el `up -d`. Si
> pasa igualmente, el fix inmediato es `docker compose restart nginx` en `~/services`.

---

## 4. Cloudflare Tunnel

Registrar el hostname `atenea.unam.dev` apuntando al nginx central, igual que el resto de
servicios (ver `services/docs/planeacion` para el detalle de la API de Cloudflare):

- **Hostname:** `atenea.unam.dev`
- **Service:** `http://nginx:80`

---

## 5. Google OAuth

En el proyecto de Google Cloud del client usado por Atenea:

- **Authorized JavaScript origins:** agregar `https://atenea.unam.dev`.
- **No** hace falta *Authorized redirect URI*: el login es por *id_token* (Google Identity
  Services en el SPA); el SPA manda el `id_token` al backend, no hay callback server-side
  (ver [ADR 0019](../decisions/0019-transporte-login-google-id-token.md)).

---

## 6. Primer despliegue

```bash
cd ~/services
make deploy            # git pull + docker compose pull + up -d + restart nginx + prune
make logs svc=atenea-backend   # debe verse "migrate" OK y gunicorn arrancando
make logs svc=atenea-worker    # debe decir "ready."
```

Crear el superusuario del admin (una vez):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    exec atenea-backend python manage.py createsuperuser
```

---

## 7. Monitores (Uptime Kuma)

Agregar dos entradas a `services/monitor/monitors.json` (patrón externo + interno) y
sincronizar:

```json
{ "name": "Atenea — externo", "url": "https://atenea.unam.dev/api/health/",
  "interval": 60, "retryInterval": 60, "maxretries": 3 },
{ "name": "Atenea — interno", "url": "http://atenea-backend:8000/api/health/",
  "interval": 60, "retryInterval": 60, "maxretries": 3 }
```

```bash
make monitors
```

El endpoint `/api/health/` ya existe y responde `{"status":"ok"}` sin autenticación.

---

## 8. Verificación

- `https://atenea.unam.dev` carga el SPA.
- Login con Google (`@ciencias.unam.mx`) funciona; en el navegador se ve la cookie
  `atenea-access-token` con `HttpOnly`, `Secure`, `SameSite=Lax`.
- `https://atenea.unam.dev/admin/` carga **con estilos** (WhiteNoise sirviendo `/static/`).
- `https://atenea.unam.dev/api/health/` → `{"status":"ok"}`.
- Ambos monitores de Atenea en verde en Uptime Kuma.
- `make ps` — el resto de servicios (outline, monitor, minio) sin afectación.

---

## 9. Actualizaciones posteriores

1. Merge a `main` en `atenea-fc` → el workflow publica nuevas imágenes `:latest` + `:sha`.
2. En el servidor: `make deploy` (re-pull + up). Las migraciones corren solas en el
   arranque del backend.

Para fijar una versión concreta en vez de `:latest`, reemplazar el tag por
`sha-<commit>` en `docker-compose.yml`.
