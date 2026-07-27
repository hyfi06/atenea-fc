# 0004 — Docker topology: one image per process

**Status:** Accepted
**Date:** 2026-07-27

## Context

Atenea must be deployable as a Docker service. The backend has two distinct runtime roles beyond serving HTTP: Celery worker and Celery beat (scheduler). The frontend is a static build artifact once compiled.

## Decision

Build one image per process, not one image for the whole app:

- `backend` image — Django + DRF, serves the API (e.g. via gunicorn).
- `frontend` image — React build output served by a lightweight web server (e.g. nginx).
- `celery-worker` image — same backend codebase, different entrypoint (`celery worker`).
- `celery-beat` image — same backend codebase, different entrypoint (`celery beat`), only needed once scheduled tasks exist.

`backend`, `celery-worker`, and `celery-beat` share the same Dockerfile/build context (`/backend`); they differ only in the container's command.

## Consequences

- Each process can be scaled independently (e.g. multiple `celery-worker` replicas without extra API instances).
- A `docker-compose.prod.yml` (or equivalent orchestration config) wires these images together and points them at the externally-managed PostgreSQL 16 and Redis instances via environment variables — no database or broker containers in production (see [0005](0005-dev-vs-prod-services.md)).
- Slightly more images to build/publish than a single all-in-one image, but each stays focused and matches how the processes actually scale/fail independently.

## Alternatives considered

- **Single all-in-one container** (supervisord running backend + frontend + celery): simpler to deploy as "one thing," but conflates independent scaling/failure domains and complicates image builds (frontend build tooling mixed with Python runtime).
