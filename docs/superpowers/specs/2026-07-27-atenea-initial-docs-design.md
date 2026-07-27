## Atenea — Initial project documentation (CLAUDE.md + docs/)

**Status:** Approved
**Date:** 2026-07-27

### Context

Atenea is the system for the SAE (Secretaría de Asuntos Estudiantiles) at Facultad de Ciencias, UNAM. The `dev` branch is a clean restart — a `dev-legacy` branch and several remote branches (`backend`, `user-app`, `students-app`, `layout`, `atenea-logo`) hold prior work, but per user decision they are historical reference only and not reused.

Before writing any application code, the project needs foundational documentation: a `CLAUDE.md` for AI-assisted development, and a `docs/` tree that records architecture decisions so that incremental service integration (the stated development approach) doesn't erode context over time.

### Decisions captured

1. **Monorepo** — `/frontend` (React) and `/backend` (Django) in one repository.
2. **API layer** — Django REST Framework.
3. **Auth** — Google OAuth via `django-allauth`, exposed to the SPA through `dj-rest-auth` issuing JWT (access + refresh) via `simplejwt`.
4. **Docker topology** — one image per process (backend, frontend, celery-worker, celery-beat). Production compose has no Postgres/Redis containers (external services); dev compose runs local Postgres 16 + Redis containers for a self-contained environment.
5. **Frontend tooling** — Vite + TypeScript.
6. **Documentation format** — one ADR per decision under `docs/decisions/`, so future incremental service additions get their own record without rewriting prior ones.

### Deliverables

- `CLAUDE.md` — project overview, stack, monorepo layout, dev/prod run instructions, pointer to ADRs, note on `dev-legacy` being non-authoritative.
- `docs/architecture-overview.md` — component diagram (text), request flow, auth flow, Docker topology.
- `docs/decisions/0001-monorepo-structure.md`
- `docs/decisions/0002-drf-for-api.md`
- `docs/decisions/0003-google-oauth-allauth-jwt.md`
- `docs/decisions/0004-docker-topology.md`
- `docs/decisions/0005-dev-vs-prod-services.md`
- `docs/decisions/0006-frontend-vite-typescript.md`
- `docs/development/getting-started.md` — placeholder outline for the dev environment doc (filled in once `docker-compose.dev.yml` exists).

### Out of scope

No application code, no `docker-compose.yml`, no Django/React scaffolding — this pass is documentation only. Scaffolding is a follow-up piece of work once these decisions are recorded.

### Self-review

- No placeholders/TBDs left in the decisions above — each has a concrete choice.
- Scope is a single cohesive unit (initial docs) — not decomposed further.
- No contradictions between this spec and the ADR list.
