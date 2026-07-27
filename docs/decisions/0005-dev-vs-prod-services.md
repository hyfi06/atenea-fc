# 0005 — Local Postgres/Redis in dev, external services in prod

**Status:** Accepted
**Date:** 2026-07-27

## Context

In production, PostgreSQL 16 and Redis (Celery's broker) are already provided as separate, independently managed services — they are not part of what Atenea's own deployment needs to stand up. Developers, however, need a way to run the full stack locally without depending on those shared production-adjacent services.

## Decision

Maintain two Docker Compose profiles:

- `docker-compose.dev.yml` — runs `backend`, `frontend`, `celery-worker`, plus local `postgres:16` and `redis` containers, so a developer can start the entire stack with one command and disposable local data.
- `docker-compose.prod.yml` — runs only the app's own processes (`backend`, `frontend`, `celery-worker`, `celery-beat`); PostgreSQL and Redis connection details are supplied via environment variables pointing at the externally-managed instances.

Both compose files consume the same application images (see [0004](0004-docker-topology.md)); only the set of services and environment configuration differ.

## Consequences

- Application code must get all datastore connection info from environment variables (`DATABASE_URL`, `REDIS_URL` or equivalent) — never hardcode "postgres"/"redis" as a hostname assumption beyond the dev compose network alias.
- Developers get a self-contained, disposable environment; no risk of local development touching shared production-adjacent data.
- Production deployment doesn't need to manage stateful containers (backups, volumes) for Postgres/Redis — that's already handled by the separate services team/infra.

## Alternatives considered

- **Always connect to shared external services, even in dev:** rejected — couples local development to availability/state of shared infrastructure and risks accidental cross-contamination of data.
