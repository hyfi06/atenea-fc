# 0006 — Frontend: Vite + TypeScript

**Status:** Accepted
**Date:** 2026-07-27

## Context

The frontend is a single-page app that consumes the DRF API (see [0002](0002-drf-for-api.md)); it does not need server-side rendering since Django is already the backend/API server.

## Decision

Build the React frontend with [Vite](https://vitejs.dev/) and TypeScript.

## Consequences

- Fast local dev server and simple production build (static assets served by the `frontend` image, see [0004](0004-docker-topology.md)).
- TypeScript types for API responses can be kept in sync with backend serializers as more services are integrated incrementally, catching contract drift at compile time rather than at runtime.
- No built-in SSR/routing-as-a-framework — routing is added explicitly (e.g. `react-router`) if/when needed.

## Alternatives considered

- **Next.js:** adds SSR and its own routing/server layer, which duplicates responsibilities Django already covers here. Rejected as unnecessary complexity.
- **Create React App:** officially deprecated by the React team; not a sound choice for a new project.
- **Plain JavaScript instead of TypeScript:** lower initial friction, but higher risk of runtime type errors as more API integrations are added over time.
