# 0001 — Monorepo structure

**Status:** Accepted
**Date:** 2026-07-27

## Context

Atenea has a React frontend and a Django backend (with Celery workers). Services will be integrated incrementally over time, and the team is small, so frontend and backend evolve together in practice.

## Decision

Single repository with a top-level split by concern:

```
/frontend   # React + TypeScript + Vite SPA
/backend    # Django + DRF project, Celery tasks
```

Frontend and backend are versioned, reviewed, and (for now) deployed together from the same repo.

## Consequences

- One PR can span an API change and its frontend consumer, reviewed as a single unit.
- Docker builds target subdirectories (`frontend/`, `backend/`) as build contexts rather than separate repos.
- If frontend and backend ever need independent release cadences or separate teams, this decision should be revisited.

## Alternatives considered

- **Polyrepo** (separate frontend/backend repos): rejected for now — adds coordination overhead (cross-repo PRs, versioning, CI wiring) that isn't justified at this project's current size.
