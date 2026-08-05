# 0019 — Transporte de login con Google: ID token (OIDC) en vez de access_token (OAuth)

**Status:** Accepted
**Date:** 2026-08-04

## Context

[ADR 0018](0018-contrato-autenticacion-frontend-backend.md) decidió (decisión 1) usar GIS Token Client (`google.accounts.oauth2.initTokenClient`) para obtener un `access_token` OAuth de Google vía popup y enviarlo a `POST /api/auth/google/`. Al retomar el trabajo de rediseño de login ([paso 2 del plan](../superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md)), se reabrió esa decisión explícitamente para evaluarla contra el estándar de seguridad vigente — el motivo dado fue alinear la decisión con el estándar actual y priorizar la seguridad informática, no un incidente puntual.

El análisis con el código en la mano (no solo la documentación) encontró una debilidad concreta en el transporte actual: `GoogleOAuth2Adapter.complete_login` (allauth), cuando recibe solo un `access_token` (sin `id_token` — el caso de hoy), valida la identidad llamando `GET userinfo` con ese token como Bearer (`_fetch_user_info`) — **sin verificar que el token se haya emitido para el `client_id` de Atenea** (`audience`). Es la clase de vulnerabilidad "OAuth token confusion / mix-up attack" documentada en la literatura de seguridad OAuth: en teoría, cualquier access_token válido de Google que pueda llamar ese mismo endpoint de userinfo autenticaría igual, sin importar para qué aplicación se emitió.

En contraste, el flujo de `id_token` (JWT firmado por Google, verificado vía las llaves públicas de Google) sí valida `audience=app.client_id` explícitamente (`GoogleOAuth2Adapter._decode_id_token` → `_verify_and_decode`, ya presente en `django-allauth`, hoy solo se ejercita cuando el cliente manda un `id_token` opcional junto al `access_token`).

## Decision

El SPA usa **Google Identity Services — "Sign In With Google"** (`google.accounts.id`, no `google.accounts.oauth2`), que emite un **ID token** (JWT OIDC) en vez de un access_token OAuth, y lo envía a `POST /api/auth/google/ {id_token}`.

Cambios necesarios:

- **Backend** (`accounts/serializers.py`, `accounts/views.py`): `GoogleLoginSerializer.validate` deja de exigir `access_token` de forma incondicional; acepta login con solo `id_token`. Se necesita un `GoogleOAuth2Adapter` propio (subclase) que sobreescriba `parse_token` para construir el `SocialToken` sin requerir `data["access_token"]` — la base de allauth (`OAuth2Adapter.parse_token`, `allauth/socialaccount/providers/oauth2/views.py`) hace `data["access_token"]` sin fallback. El resto de la verificación (`complete_login` → `_decode_id_token` → `_verify_and_decode` con `audience=app.client_id`) ya existe en la librería sin cambios.
- **Frontend** (`frontend/src/auth/google.ts`, `AuthContext.tsx`): reemplaza `initTokenClient`/`requestAccessToken` por `google.accounts.id.initialize` + el flujo de botón/One Tap, que entrega el `id_token` directamente en el callback (`credential` en la respuesta de Google). Ya no se solicita el scope OAuth `email profile` — el ID token trae las claims de identidad (`email`, `name`, `sub`) por defecto, sin pedir autorización de API.
- **Sin cambios de infraestructura**: ninguna variable de entorno nueva. `GOOGLE_OAUTH_CLIENT_ID` (backend y frontend, ya existente) sigue siendo la única variable funcionalmente necesaria — se usa para verificar `audience`. `GOOGLE_OAUTH_CLIENT_SECRET` queda configurado pero deja de ejercitarse en esta ruta (la verificación de `id_token` es criptografía de clave pública, sin secreto compartido).
- Sigue sin navegación de página completa (popup/One Tap, no redirect) — no se reintroduce la ruta `/auth/google/callback` eliminada en el changelog de ADR 0018 (2026-08-01).

## Consequences

- Reduce la superficie de la vulnerabilidad de "token confusion" descrita en Context: el backend ahora siempre verifica `audience=app.client_id` en cada login con Google, sin depender de que el cliente decida mandar también un `id_token` opcional.
- Ya no se solicita el scope de autorización `email profile` vía OAuth — el consentimiento que ve el usuario es el de "iniciar sesión", no el de "dar acceso a tu perfil de Google a esta app", más preciso para lo que Atenea realmente hace (autenticar, no llamar APIs de Google a nombre del usuario).
- El backend deja de hacer una llamada de red a Google en cada login (`_fetch_user_info`) — la verificación del `id_token` es puramente criptográfica contra llaves públicas cacheadas por `allauth`. Menos dependencia de red por request de login.
- Requiere escribir y probar el `GoogleOAuth2Adapter`/`GoogleLoginSerializer` actualizados — no es un cambio de configuración, es código nuevo con su propia cobertura de test (ver [spec de login](../superpowers/specs/2026-08-04-login-oauth-design.md) y el paso 9 del ledger de progreso para el plan de implementación).
- `frontend/src/auth/google.ts` cambia de superficie (ya no expone `solicitarAccessTokenDeGoogle`, expone el flujo de credential/One Tap) — cualquier consumidor de esa función debe actualizarse junto con este cambio.

## Alternatives considered

- **Mantener GIS Token Client / access_token (statu quo de ADR 0018):** cero esfuerzo, ya implementado y probado. Se descarta como decisión final porque no resuelve la debilidad de "token confusion" descrita en Context, y porque usa el mecanismo de *autorización* de OAuth (pensado para acceder a APIs de Google a nombre del usuario) para un caso de uso que es puramente de *autenticación* — un uso del mecanismo distinto de para lo que fue diseñado, aunque hoy no esté siendo explotado.
- **Authorization Code + PKCE, redirect completo:** es el patrón que OAuth 2.1 exige para clientes públicos, y elimina cualquier token de Google del navegador por completo (el intercambio ocurre servidor-a-servidor). Se descarta frente a la opción elegida porque: (1) reintroduce código eliminado deliberadamente el 2026-08-01 por no tener consumidor real (`accounts/views.py:13`, rama `elif code` de `GoogleLoginSerializer.validate`); (2) exige recrear la ruta `/auth/google/callback` en el SPA y sacrificar el popup por navegación de página completa; (3) no cierra una brecha que el ID token no cierre ya — el JWT propio de Atenea (la sesión que realmente importa) ya viaja como cookie `httpOnly` en producción desde ADR 0018, así que este endurecimiento solo protegería el token transitorio de Google, que en la opción elegida directamente deja de tener el problema (el id_token siempre valida `audience`).
- **Instalar `token_blacklist` u otros endurecimientos de sesión al mismo tiempo:** fuera de alcance de esta decisión — es la deuda técnica ya registrada en [`docs/technical-debt/0007-logout-sin-invalidacion-refresh-token.md`](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md), no se resuelve aquí.

## Changelog

- **2026-08-04** — ADR creada al retomar el paso 2 del plan de rediseño de login (`docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`), reabriendo deliberadamente la decisión 1 de ADR 0018.
