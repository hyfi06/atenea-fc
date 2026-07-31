# 0003 — Google OAuth via django-allauth, JWT for the SPA

**Status:** Accepted
**Date:** 2026-07-27

## Context

Atenea authenticates users (SAE staff and, eventually, students) through Google OAuth — there is no separate username/password signup flow. The React SPA needs to call the DRF API as an authenticated user after completing the Google login.

## Decision

- Use `django-allauth` to handle the Google OAuth flow on the backend.
- Use `dj-rest-auth` to expose REST endpoints (login, logout, token refresh, user) on top of allauth.
- Use `djangorestframework-simplejwt` for token issuance: the SPA receives a short-lived access token and a refresh token after completing Google login, and authenticates subsequent API calls with the access token.

## Consequences

- The SPA stores and refreshes JWTs client-side; the API does not need to be session/cookie-aware, which keeps frontend and backend deployable on different origins if that becomes necessary later.
- Django admin (for staff who need it) can continue to use Django's own session auth independently — this decision only governs the API consumed by the React app.
- Token refresh logic must be implemented in the frontend (silent refresh or refresh-on-401).
- Google OAuth client credentials are configuration/secrets, not part of this decision — tracked separately in environment configuration.

## Alternatives considered

- **Session cookies (`dj-rest-auth` + `SessionAuthentication`):** simpler (no client-side token handling), but requires frontend and backend to share a domain/cookie context. Rejected to keep deployment topology flexible as services are added incrementally.
- **Manual Google token verification with `google-auth`:** full control, but reimplements OAuth flow handling and account linking that `allauth` already solves.
- **`social-auth-app-django`:** viable multi-provider alternative, but `allauth` + `dj-rest-auth` has more direct DRF integration for a Google-only requirement.

## Changelog

- **2026-07-31** — [ADR 0018](0018-contrato-autenticacion-frontend-backend.md) amplía esta decisión: en producción, `REST_AUTH["JWT_AUTH_HTTPONLY"]` pasa a `True` (JWT como cookie `httpOnly`, no en el body) para mitigar robo de tokens vía XSS, siguiendo la recomendación vigente de OWASP para SPAs. En desarrollo se mantiene el comportamiento original de esta ADR (`JWT_AUTH_HTTPONLY = False`, tokens en el body, guardados en `localStorage`) por simplicidad de depuración. Ver ADR 0018 para el detalle completo del contrato frontend/backend, incluyendo el transporte elegido para el login de Google.
