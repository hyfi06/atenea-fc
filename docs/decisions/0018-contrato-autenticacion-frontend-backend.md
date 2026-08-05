# 0018 — Contrato de autenticación entre frontend y backend

**Status:** Accepted
**Date:** 2026-07-31

## Context

La [ADR 0003](0003-google-oauth-allauth-jwt.md) estableció el enfoque general (`django-allauth` + `dj-rest-auth` + `simplejwt`, JWT en vez de sesión). El backend expone hoy el contrato HTTP completo (`accounts/urls.py`, `accounts/views.py`), probado en `accounts/tests/test_auth.py`:

- `POST /api/auth/login/` — email + password → `{access, refresh}`
- `POST /api/auth/google/` — login social, soporta `access_token`/`id_token` o `code` (heredado de `SocialLoginSerializer` de `dj-rest-auth`)
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`
- `GET /api/auth/user/`
- `POST /api/auth/password/reset/` y `/password/reset/confirm/`

En esta rama ya se mergeó el scaffolding del frontend (`Login.tsx`, `api/client.ts`), pero es puramente visual: el formulario navega directo a `/home` sin llamar a la API, no hay manejo de tokens, no existe la ruta `/auth/google/callback`, y `api/client.ts` no adjunta `Authorization` en ninguna petición. El contrato real que el SPA debe implementar contra ese backend no estaba decidido. Esta ADR cubre las tres decisiones abiertas encontradas al analizarlo.

## Decision

### 1. Transporte de Google OAuth: GIS Token Client (popup), no redirect

El SPA usa la librería de Google Identity Services (`google.accounts.oauth2.initTokenClient`) para abrir un popup, obtener un `access_token` de OAuth, y enviarlo tal cual a `POST /api/auth/google/ {access_token}`.

Se descarta el flujo de Authorization Code + redirect: `GoogleLoginView.callback_url` (`accounts/views.py:13`) ya apunta a `{FRONTEND_URL}/auth/google/callback`, dejado configurado desde que se implementó el login social, pero nunca ejercitado por ningún test ni por el frontend. El flujo `access_token` es exactamente el que ejercitan `GoogleLoginTests` en `accounts/tests/test_auth.py`, no requiere cambios de backend, y no exige crear una ruta de callback ni una navegación de página completa en el SPA.

### 2. Storage/transporte de JWT: split por entorno — amplía ADR 0003

- **Dev** (`config/settings/dev.py`): `REST_AUTH["JWT_AUTH_HTTPONLY"] = False` (el valor que ya trae `base.py` hoy) — los tokens viajan en el body JSON de la respuesta; el frontend los guarda en `localStorage`, priorizando poder inspeccionar el estado de auth fácilmente desde devtools durante desarrollo.
- **Prod** (`config/settings/prod.py`): `REST_AUTH["JWT_AUTH_HTTPONLY"] = True` — `dj-rest-auth` entrega `access`/`refresh` como cookies `httpOnly` + `Secure`, coherente con `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` que `prod.py` ya fija. El frontend nunca lee ni guarda el JWT en JS; cada request usa `credentials: 'include'` en vez de un header `Authorization` armado a mano.

Esto **amplía la ADR 0003**: esa ADR decidió "JWT en el body, el SPA lo guarda y refresca client-side" como una decisión única para todos los entornos, razonando que evitaba acoplar frontend/backend a un mismo contexto de cookies. Esta ADR mantiene esa lectura para dev, pero en prod prioriza la recomendación vigente de OWASP (no exponer tokens a JS por el riesgo de robo vía XSS) sobre la flexibilidad de despliegue cross-origin — aceptable porque en prod, frontend y backend de Atenea se despliegan bajo una topología conocida (`docker-compose.prod.yml`), no como servicios arbitrariamente distintos. Requiere además `CORS_ALLOW_CREDENTIALS = True` en prod (hoy ausente) para que el navegador acepte cookies cross-origin.

### 3. Logout no invalida el refresh token en servidor — deuda técnica aceptada

El proyecto no tiene instalada `rest_framework_simplejwt.token_blacklist`. `POST /api/auth/logout/` limpia el token/cookie del lado del cliente, pero el refresh token sigue siendo válido en el servidor hasta su expiración natural (`REFRESH_TOKEN_LIFETIME = 7 días`) aunque el usuario "cierre sesión". Se acepta como límite del MVP y se registra en [`docs/technical-debt/0007-logout-sin-invalidacion-refresh-token.md`](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md).

## Consequences

- El frontend necesita una variable de entorno nueva expuesta al cliente (`VITE_GOOGLE_OAUTH_CLIENT_ID`), análoga a `GOOGLE_OAUTH_CLIENT_ID` del backend, para inicializar el token client de Google.
- `api/client.ts` deja de ser un simple wrapper de `fetch` — necesita: adjuntar credenciales según el modo (`Authorization` header en dev, `credentials: 'include'` en prod), interceptar `401` para llamar a `/api/auth/token/refresh/` y reintentar una vez, y una forma de saber al montar la app si ya hay sesión (en prod, un `GET /api/auth/user/` con la cookie; en dev, leer `localStorage`).
- El camino de Authorization Code (`code` + `callback_url`) queda como código sin usar en el backend (`accounts/views.py:13`, rama `elif code` en `GoogleLoginSerializer.validate`) — no se elimina en esta pasada por estar fuera de alcance, pero cualquiera que lo modifique debe saber que no tiene cobertura de test ni consumidor real.
- `ROTATE_REFRESH_TOKENS = False` (ya configurado) simplifica el interceptor de refresh: el refresh token no cambia entre llamadas, así que en prod (cookie) no hay nada que reescribir del lado del cliente, y en dev (localStorage) solo se actualiza el `access` token tras cada refresh.
- Con cookie `httpOnly` en prod, el usuario ya no puede "cerrar sesión" borrando algo él mismo desde devtools — la única vía es que el backend expire/reescriba la cookie, lo que hace más visible el hueco de la deuda técnica del punto 3.

## Alternatives considered

- **Authorization Code + redirect completo:** más "estándar OAuth" en el sentido de mantener el `client_secret` fuera del navegador durante el intercambio, pero el `access_token` del GIS Token Client tampoco lo expone (el intercambio con Google ocurre por completo en el flujo implícito del SDK); se descartó por el costo de UX (navegación completa) y de código (ruta nueva) sin beneficio de seguridad adicional real para este caso.
- **httpOnly cookie en todos los entornos, incluido dev:** se descartó por fricción de desarrollo — dev usa `http://localhost` sin TLS, lo que complica `Secure`/`SameSite` y dificulta inspeccionar tokens al debuggear; se prefirió limitar el costo de esa complejidad a prod, donde sí importa.
- **Access token en memoria + refresh en cookie httpOnly (híbrido) para prod:** variante más segura aún (el access token nunca se persiste ni siquiera como cookie), pero es una personalización sobre lo que `dj-rest-auth` da de fábrica con `JWT_AUTH_HTTPONLY`; se prefirió el modo soportado directamente por la librería para no mantener código de cookies a mano.
- **Instalar `token_blacklist` ahora:** cerraría el hueco de logout de inmediato, pero es una app y migración nuevas no pedidas por ningún flujo actual; se prefiere registrarlo como deuda técnica explícita y resolverlo cuando el riesgo real lo justifique.

## Changelog

- **2026-08-01** — Se elimina el código muerto del flujo Authorization Code señalado en "Consequences": `GoogleLoginView.callback_url`/`client_class` (`accounts/views.py`) y la rama `elif code` de `GoogleLoginSerializer.validate` (`accounts/serializers.py`), incluyendo el intercambio manual de `code` por `access_token`. La razón original para no quitarlo ("fuera de alcance en esa pasada") ya no aplica — se confirmó que ningún test ni consumidor real lo ejercita, y la decisión 1 de esta ADR ya había fijado GIS Token Client (`access_token`) como el único transporte usado.
- **2026-08-01** — Se implementa en el backend el transporte de cookie httpOnly para prod descrito en la decisión 2, que hasta ahora solo estaba documentado pero no era funcional: `config/settings/prod.py` fijaba `JWT_AUTH_HTTPONLY=True` sin definir `JWT_AUTH_COOKIE`/`JWT_AUTH_REFRESH_COOKIE` (sin nombre, dj-rest-auth nunca llama a `response.set_cookie(...)`), y `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` usaba `JWTAuthentication` (solo header) en vez de `JWTCookieAuthentication` (header con fallback a cookie), así que ninguna vista protegida podía autenticar con la cookie aunque existiera. Se corrigen ambos puntos; el comportamiento de dev no cambia. El default de la librería para CSRF en cookie (`JWT_AUTH_COOKIE_USE_CSRF=False`) se deja sin activar, tal como ya razonaba esta ADR en "Alternatives considered" — registrado explícitamente como deuda técnica en [`docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md`](../technical-debt/0009-sin-csrf-en-cookie-jwt.md). Nota adicional sobre el alcance real de la decisión 2: `LoginView.get_response` de `dj-rest-auth` sigue incluyendo `access` en el body JSON de `/api/auth/login/` y `/api/auth/google/` aunque `JWT_AUTH_HTTPONLY=True` (solo `refresh` se vacía) — en prod, el access token sí queda presente en una respuesta legible por JS, así que la propiedad "el frontend nunca lee ni guarda el JWT en JS" depende de disciplina del SPA (ignorar ese campo del body) y no de que el backend lo retenga; ver el detalle correspondiente en [`docs/development/api-frontend.md`](../development/api-frontend.md).
- **2026-08-04** — La decisión 1 (transporte de login de Google: GIS Token Client / `access_token`) queda **superada** por [ADR 0019](0019-transporte-login-google-id-token.md): el SPA pasa a usar Sign In With Google (`id_token`, OIDC) en vez de `access_token` OAuth, para cerrar una brecha de verificación de `audience` encontrada en el flujo de `access_token` (el backend no confirmaba que el token se hubiera emitido para el `client_id` de Atenea). Las decisiones 2 (transporte/storage del JWT propio de Atenea) y 3 (logout sin invalidar refresh token) de esta ADR no cambian — siguen vigentes tal como están descritas arriba.
