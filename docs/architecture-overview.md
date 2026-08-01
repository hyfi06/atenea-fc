# Arquitectura de Atenea

Visión general del sistema. El detalle y el razonamiento de cada elección viven en [`docs/decisions/`](decisions/) como ADRs individuales — este documento es el mapa, no la fuente de verdad de cada decisión.

## Componentes

```
┌─────────────────┐      HTTPS/JSON       ┌──────────────────────┐
│  React SPA       │ ───────────────────▶ │  Django + DRF (API)  │
│  (Vite + TS)      │ ◀─────────────────── │                      │
└─────────────────┘      JWT (access +     └──────────┬───────────┘
                          refresh)                     │
                                                        │ ORM
                                              ┌─────────▼──────────┐
                                              │  PostgreSQL 16      │
                                              │  (servicio externo) │
                                              └──────────────────────┘

┌──────────────────────┐        tasks         ┌──────────────────────┐
│ Django + DRF (API)    │ ────────────────────▶ │  Redis               │
│                       │ ◀──────────────────── │  (broker, servicio   │
└──────────────────────┘        results         │   externo)           │
           │                                    └──────────┬────────────┘
           │ enqueue                                        │
           ▼                                                ▼
┌──────────────────────┐                        ┌──────────────────────┐
│ Celery worker(s)      │                        │ Celery beat           │
│ (mismo código backend)│                        │ (scheduler, opcional) │
└──────────────────────┘                        └──────────────────────┘
```

- **React SPA** — interfaz de usuario. Ver [0006](decisions/0006-frontend-vite-typescript.md).
- **Django + DRF** — API HTTP consumida por el SPA. Ver [0002](decisions/0002-drf-for-api.md).
- **Celery worker / beat** — ejecutan tareas asíncronas y programadas encoladas por el backend, comparten el código del backend pero corren como procesos/contenedores separados. Ver [0004](decisions/0004-docker-topology.md).
- **PostgreSQL 16 y Redis** — servicios externos ya existentes, gestionados fuera del despliegue de Atenea; en producción no se contenerizan como parte de esta app. Ver [0005](decisions/0005-dev-vs-prod-services.md).

## Autenticación

1. El usuario inicia sesión con Google desde el SPA.
2. `django-allauth` completa el flujo OAuth con Google en el backend.
3. `dj-rest-auth` + `simplejwt` emiten un access token y un refresh token JWT.
4. El SPA adjunta el access token en cada llamada al API; lo renueva con el refresh token cuando expira.

Detalle y alternativas consideradas en [0003](decisions/0003-google-oauth-allauth-jwt.md) y [0018](decisions/0018-contrato-autenticacion-frontend-backend.md). Referencia completa de endpoints para integrar el SPA (incluyendo autenticación) en [`docs/development/api-frontend.md`](development/api-frontend.md).

## Despliegue

La app se empaqueta como contenedores Docker independientes por proceso (`backend`, `frontend`, `celery-worker`, `celery-beat`), orquestados por Compose:

- **Desarrollo** (`docker-compose.dev.yml`): incluye contenedores locales de Postgres 16 y Redis, entorno autocontenido.
- **Producción** (`docker-compose.prod.yml`): solo los procesos propios de Atenea; Postgres y Redis se configuran vía variables de entorno apuntando a los servicios externos ya existentes.

Ver [0004](decisions/0004-docker-topology.md) y [0005](decisions/0005-dev-vs-prod-services.md).

## Estructura del repositorio

Monorepo (ver [0001](decisions/0001-monorepo-structure.md)):

```
/frontend   # React + TypeScript + Vite
/backend    # Django + DRF + Celery
/docs       # esta documentación
```

## Integración incremental de servicios

Atenea se construye agregando servicios/módulos de la SAE de forma incremental (por ejemplo, en el histórico previo del proyecto hubo un módulo de estudiantes y uno de usuarios — no reutilizados directamente, ver nota en [`CLAUDE.md`](../CLAUDE.md)). Cada nuevo servicio que se integre:

1. Se documenta en un ADR nuevo en `docs/decisions/` si introduce una decisión de arquitectura.
2. Sigue los patrones ya establecidos aquí (DRF para exponer su API, JWT para auth, Celery para trabajo asíncrono si aplica).
