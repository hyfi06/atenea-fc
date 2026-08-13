# 0025 — Despliegue a producción: mismo origen, imágenes en GHCR

**Status:** Accepted
**Date:** 2026-08-13

## Context

Atenea se despliega dentro del ecosistema externo `services/` (repo `fc-sae/services`):
**Cloudflare (termina TLS) → cloudflared → nginx central (solo HTTP) → contenedores en `sae-network`**, modo Full sin TLS interno. Ese stack es *pull-based* (`make deploy` = `git pull` + `docker compose pull` + `up -d`) y ya declara `atenea-db` (postgres:16) y `atenea-redis`. No tiene CI.

El repo `atenea-fc` no era desplegable: su `docker-compose.prod.yml` propio no corría migraciones ni `collectstatic`, exponía gunicorn plano, y `config/settings/prod.py` forzaba `SECURE_SSL_REDIRECT` sin reconocer el proxy TLS (loop de redirección). Además, el admin de Django quedaba sin estáticos con `DEBUG=False`.

Este ADR fija cómo se produce y despliega la app. Amplía [ADR 0004](0004-docker-topology.md) (topología Docker) y [ADR 0005](0005-dev-vs-prod-services.md) (Postgres/Redis externos en prod), y depende del contrato de auth de [ADR 0018](0018-contrato-autenticacion-frontend-backend.md) / [ADR 0019](0019-transporte-login-google-id-token.md).

## Decision

- **Mismo origen bajo `atenea.unam.dev`.** Un único vhost en el nginx central rutea `/api/`, `/admin/`, `/static/` → `atenea-backend:8000` y todo lo demás → `atenea-frontend:80` (SPA). No hay `ateneapi.unam.dev`. Consecuencia: **sin CORS**, la cookie JWT httpOnly queda *same-site* (`SameSite=Lax` funciona), y el SPA se construye con `VITE_API_BASE_URL=""` (llamadas relativas).
- **Confianza en el proxy TLS.** `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`; el nginx central propaga `X-Forwarded-Proto https`. Es seguro porque el backend nunca se expone directo a internet — solo lo alcanza el nginx interno. Se fija además `CSRF_TRUSTED_ORIGINS` y `SECURE_HSTS_PRELOAD`.
- **Estáticos con WhiteNoise**, seleccionable por env `DJANGO_STATIC_BACKEND` (default `whitenoise`, manifest comprimido). `collectstatic` corre en build; el admin sirve sus estáticos sin depender del nginx central. No se integra MinIO/S3 para estáticos (ver [deuda 0015](../technical-debt/0015-estaticos-whitenoise-media-pendiente.md)).
- **Arranque por entrypoint.** `docker-entrypoint.sh` aplica `migrate` y arranca gunicorn cuando no recibe comando; si el compose pasa `command:` (worker Celery, `runserver` de dev) lo ejecuta tal cual sin migrar. Compatible con `make deploy` (up -d) sin pasos manuales.
- **Imágenes en GHCR, publicadas al hacer merge a `main`.** Un workflow de GitHub Actions (`.github/workflows/publish-images.yml`) construye y publica `ghcr.io/<owner>/atenea-backend` y `ghcr.io/<owner>/atenea-frontend` (tags `:latest` + `:sha`). `services/` las referencia con `image:`; `make deploy` (pull) queda intacto.
- **Config del SPA en runtime, no en build.** El único valor específico de entorno del SPA (el client id de Google) se inyecta al arrancar el contenedor del frontend vía `/config.js`, regenerado desde `ATENEA_GOOGLE_CLIENT_ID` (env del deploy en `services/.env`); el código lee `window.__ATENEA_CONFIG__` con fallback a Vite para dev (`src/config.ts`). La única constante horneada en build es `VITE_API_BASE_URL=""` (mismo origen). Así la imagen prehorneada sirve para cualquier entorno sin rebuild y el CI no necesita ningún valor de Atenea.
- **Pasos manuales documentados** en [`docs/development/despliegue-produccion.md`](../development/despliegue-produccion.md): servicios/vhost/env en `services/`, alta del hostname en Cloudflare Tunnel, Authorized JavaScript origin de Google, y rotación de secretos.

## Consequences

- El backend deja de ser desplegable "a mano": build reproducible, migraciones automáticas y estáticos servidos. `manage.py check --deploy` sale sin warnings.
- El repo `atenea-fc` gana su primer CI (solo build+push en merge a `main`); `services/` sigue sin CI, consistente con su patrón manual.
- Mismo origen elimina CORS y simplifica el modelo de cookies, pero **no** cierra el riesgo CSRF residual *same-site*: `atenea.unam.dev` convive con subdominios hermanos bajo `unam.dev` (`docs.unam.dev`, `files.unam.dev`). Ese hueco ya está registrado y acotado en [deuda 0009](../technical-debt/0009-sin-csrf-en-cookie-jwt.md); los hermanos hoy son del mismo equipo.
- El despliegue queda partido en dos repos: el código y las imágenes en `atenea-fc`, la orquestación en `services/`. El runbook es el puente; si `services/` cambia su topología, el runbook debe actualizarse.
- Deuda referenciada, no duplicada: estáticos/media → [0015](../technical-debt/0015-estaticos-whitenoise-media-pendiente.md); CSRF same-site → [0009](../technical-debt/0009-sin-csrf-en-cookie-jwt.md).

## Alternatives considered

- **Dominios separados (`atenea.unam.dev` + `ateneapi.unam.dev`):** rechazado. Obliga a CORS y a razonar cookies cross-origin sin beneficio, ya que el único consumidor de la API es el propio SPA. Se retomaría solo si un consumidor externo necesitara la API por su cuenta.
- **Registry Docker self-hosted (`register.unam.dev`):** rechazado. Sería parte del mismo stack que intenta hacer `pull` durante el arranque → dependencia circular / riesgo de bootstrap; además no elimina el build manual. GHCR es externo y siempre disponible en deploy.
- **Estáticos/media servidos desde MinIO:** rechazado por ahora. Para estáticos (pequeños, inmutables, cacheados por Cloudflare) WhiteNoise es más simple y no añade valor de escalamiento; MinIO aporta cuando existan uploads de media (trabajo futuro, [deuda 0015](../technical-debt/0015-estaticos-whitenoise-media-pendiente.md)).
- **Servicio one-shot de `migrate` + estáticos por nginx:** rechazado. Añade un servicio y más piezas al compose; el entrypoint cubre el caso con cero pasos manuales.
