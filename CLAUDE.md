# Atenea

Sistema de la SAE (Secretaría de Asuntos Estudiantiles), Facultad de Ciencias, UNAM. Administra los servicios de la SAE; los servicios se integran de forma incremental.

## Stack

- **Frontend:** React + TypeScript + Vite (`/frontend`)
- **Backend:** Django + Django REST Framework (`/backend`)
- **Tareas asíncronas:** Celery, con Redis como broker
- **Base de datos:** PostgreSQL 16 — servicio externo, no gestionado por esta app
- **Auth:** Google OAuth (`django-allauth`) + JWT hacia el SPA (`dj-rest-auth` + `simplejwt`)
- **Despliegue:** contenedores Docker, uno por proceso (`backend`, `frontend`, `celery-worker`, `celery-beat`)

El razonamiento detrás de cada elección está documentado como ADRs en [`docs/decisions/`](docs/decisions/). La vista general de cómo encajan los componentes está en [`docs/architecture-overview.md`](docs/architecture-overview.md).

## Estructura del repositorio

Monorepo:

```
/frontend   # React + TypeScript + Vite
/backend    # Django + DRF + Celery
/docs       # documentación de arquitectura y desarrollo
```

## Desarrollo local vs producción

- **Dev:** `docker-compose.dev.yml` levanta todo el stack incluyendo Postgres y Redis locales en contenedores.
- **Prod:** `docker-compose.prod.yml` levanta solo los procesos propios de Atenea; Postgres y Redis son servicios externos ya existentes, configurados por variables de entorno.

Ver [`docs/development/getting-started.md`](docs/development/getting-started.md) (en construcción — se completa junto con el scaffolding real del proyecto).

## Estado del proyecto

La rama `dev` es un reinicio limpio. Existe una rama `dev-legacy` y ramas remotas (`backend`, `user-app`, `students-app`, `layout`, `atenea-logo`) con trabajo previo — son **referencia histórica únicamente**, no se reutilizan ni se asumen vigentes.

## Documentando decisiones

Toda decisión de arquitectura nueva (especialmente al integrar un servicio nuevo de la SAE) se registra como un ADR en `docs/decisions/NNNN-titulo.md`, siguiendo el formato de los ADRs existentes (Contexto → Decisión → Consecuencias → Alternativas consideradas).

## Documentando deuda técnica

Toda simplificación deliberada — una decisión "suficiente por ahora", tomada conscientemente para no bloquear una entrega, que alguien debería revisar si el supuesto que la sostiene deja de cumplirse — se registra como un ítem en `docs/technical-debt/NNNN-titulo.md`, numerado consecutivamente igual que los ADRs (secuencia propia de esa carpeta, no compartida con `docs/decisions/`).

Formato estándar de cada ítem:

```markdown
# NNNN — <Título corto>

**Estado:** Activa | Resuelta — YYYY-MM-DD (commit/ADR que la cerró)
**Origen:** [ADR NNNN](../decisions/NNNN-titulo.md)

## Qué se simplificó

## Por qué era razonable

## Señal de revisión
```

Un ítem nace siempre referenciado desde el ADR o spec que lo originó — no basta con mencionarlo solo en "Alternatives considered" del ADR, eso explica la decisión puntual, el ítem de deuda la hace buscable junto con toda la demás deuda del proyecto. Ver [`docs/technical-debt/README.md`](docs/technical-debt/README.md) para el índice completo.

## Mensajes de commit

Formato `[type][scope] resumen` + lista de cambios + `Signed-off-by`, commits lo más atómicos posible. Ver [`docs/development/commit-conventions.md`](docs/development/commit-conventions.md) (tipos, ejemplos) y [ADR 0007](docs/decisions/0007-commit-message-convention.md).
