## Login — Transporte de autenticación con Google (Sign In With Google / ID token)

**Status:** Approved
**Date:** 2026-08-04

### Context

El login (frontend + backend, dev/prod) ya funciona y está documentado en [ADR 0003](../../decisions/0003-google-oauth-allauth-jwt.md) y [ADR 0018](../../decisions/0018-contrato-autenticacion-frontend-backend.md) — confirmado en código, no solo en docs: `frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/google.ts`, `frontend/src/api/client.ts` y `backend/accounts/{serializers,views}.py` ya implementan exactamente el contrato de ADR 0018 (GIS Token Client vía popup, split dev/prod de storage de JWT, interceptor de refresh en 401).

Al retomar el paso 2 del plan de rediseño (`docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`), el ledger marcaba como pendiente reabrir explícitamente la decisión 1 de ADR 0018 (transporte de Google OAuth) para verificar que siga siendo la mejor opción — el motivo concreto dado por el usuario fue **alinear la decisión con el estándar actual y priorizar la seguridad informática**, no un problema puntual detectado en producción.

El análisis con el código en la mano (no solo la documentación) encontró una debilidad concreta en el transporte actual: `GoogleOAuth2Adapter.complete_login` (allauth), cuando recibe solo un `access_token` (el caso de hoy, sin `id_token`), valida la identidad llamando `GET userinfo` con ese token como Bearer — **sin verificar que el token se haya emitido para el `client_id` de Atenea** (`audience`). Es la clase de vulnerabilidad "OAuth token confusion / mix-up attack" ya documentada en la literatura de seguridad OAuth. El flujo de `id_token` (JWT firmado por Google) sí valida `audience=app.client_id` explícitamente, y esa verificación ya existe sin cambios en `django-allauth` — solo no se ejercita hoy porque el frontend nunca manda un `id_token`.

Se evaluaron tres opciones (detalle completo de trade-offs y esfuerzo en [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md)):

1. Mantener GIS Token Client / access_token (statu quo de ADR 0018).
2. Authorization Code + PKCE, redirect completo (la alternativa que ADR 0018 ya había descartado y que el ledger nombraba explícitamente).
3. Sign In With Google / ID token (OIDC) — no estaba en el radar del ledger original, surgió del análisis de código de este paso.

### Decisions captured

1. **Transporte de Google: Sign In With Google (`google.accounts.id`), no GIS Token Client.** El SPA obtiene un `id_token` (JWT OIDC) y lo envía a `POST /api/auth/google/ {id_token}`. Reemplaza la decisión 1 de ADR 0018. Ver [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md) para el detalle y las alternativas descartadas.
2. **Storage/transporte del JWT propio de Atenea no cambia.** Split dev/prod (`localStorage` + header `Authorization` en dev, cookie `httpOnly` en prod) sigue vigente tal como lo fija la decisión 2 de ADR 0018. Esta spec no reabre esa decisión.
3. **Logout sin invalidar refresh token en servidor no cambia.** Sigue como deuda técnica aceptada (decisión 3 de ADR 0018, [deuda técnica 0007](../../technical-debt/0007-logout-sin-invalidacion-refresh-token.md)).
4. **Deuda técnica 0010 (API no expone perfil/rol del usuario autenticado) queda explícitamente fuera de esta spec** — ver la nota dedicada más abajo. No se resuelve aquí, pero se deja registrada la razón y la señal de cuándo debe dejar de posponerse.
5. **El placeholder de `Landing.tsx` se corrige como parte de esta spec.** El botón "Continuar con Correo Ciencias" (`Landing.tsx:25`) hoy hace `navigate('/home')` directo, sin llamar el login — es el único defecto funcional real detectado en el flujo de login (no un problema de arquitectura). Se corrige en el plan de implementación del paso 9: el botón pasa a invocar el mismo flujo que `Login.tsx` (`useAuth().loginWithGoogle()`, con manejo de carga/error análogo), y navega a `/home` solo tras un login exitoso.
6. **CSRF en cookie JWT (deuda técnica 0009) se decide explícitamente: no se activa en este trabajo.** `JWT_AUTH_COOKIE_USE_CSRF` sigue en `False`. Razón (ya registrada en la propia deuda 0009, reafirmada aquí): `JWT_AUTH_SAMESITE="Lax"` ya bloquea el escenario clásico de CSRF cross-site; el hueco residual es acceso desde un subdominio hermano del mismo dominio padre, y su señal de revisión documentada (endpoint de escritura explotado así, o despliegue compartiendo dominio con contenido de terceros no confiable) no se ha dado. Activarlo además exigiría trabajo de frontend (leer y reenviar el token CSRF en cada `POST`/`PATCH`/`DELETE`) no motivado por el cambio de transporte de Google que sí decide esta spec.

### Cambios de backend

- `accounts/serializers.py` — `GoogleLoginSerializer.validate` deja de exigir `access_token` de forma incondicional (hoy: `if not access_token: raise ValidationError(...)`); acepta un login válido con solo `id_token` presente.
- Nuevo adapter propio (subclase de `GoogleOAuth2Adapter`) que sobreescribe `parse_token` para construir el `SocialToken` sin requerir `data["access_token"]` — la base de allauth (`OAuth2Adapter.parse_token`, `allauth/socialaccount/providers/oauth2/views.py`) hace `data["access_token"]` sin fallback, así que no se puede usar tal cual con solo `id_token`.
- Sin cambios en `GoogleOAuth2Adapter.complete_login` ni en la verificación de firma/`audience` (`_decode_id_token` → `_verify_and_decode`) — ya existen en `django-allauth` tal como está instalado, no se reimplementan.
- `accounts/views.py` (`GoogleLoginView`) — sin cambios de configuración; sigue usando `adapter_class = GoogleOAuth2Adapter` (o su subclase nueva) y `serializer_class = GoogleLoginSerializer`.

### Cambios de frontend

- `frontend/src/auth/google.ts` — reemplaza `cargarGoogleIdentityServices`/`solicitarAccessTokenDeGoogle` (basados en `google.accounts.oauth2.initTokenClient`) por el flujo de `google.accounts.id.initialize` + callback de credential (botón o One Tap). El script `https://accounts.google.com/gsi/client` sigue siendo el mismo, solo cambia qué parte de la API se usa.
- Ya no se solicita `scope: 'email profile'` — el `id_token` trae las claims de identidad por defecto, sin pedir un grant de autorización de API.
- `frontend/src/auth/AuthContext.tsx` (`loginWithGoogle`) — cambia de `apiPost('/api/auth/google/', { access_token: accessToken })` a `apiPost('/api/auth/google/', { id_token: idToken })`.
- `frontend/src/screens/Login.tsx` — el botón "Continuar con Correo Ciencias" sigue disparando el mismo flujo desde `useAuth().loginWithGoogle()`; no cambia su UX de cara al usuario (sigue siendo popup/One Tap, no navegación de página completa).
- `frontend/src/screens/Landing.tsx` — el botón "Continuar con Correo Ciencias" (línea 25) deja de hacer `navigate('/home')` directo; pasa a invocar `useAuth().loginWithGoogle()` (mismo flujo de `id_token` que `Login.tsx`) con manejo de carga/error, y navega a `/home` solo si el login resuelve. Ver decisión 5.

### Variables de entorno

Ninguna variable nueva — las tres opciones evaluadas reusan el mismo par ya existente:

| Variable | Uso en la decisión elegida |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` (backend, `.env`) | Única variable funcionalmente necesaria — se usa como `audience` al verificar el `id_token`. |
| `GOOGLE_OAUTH_CLIENT_SECRET` (backend, `.env`) | Se mantiene configurada (parte de `SocialApp`), pero deja de ejercitarse en esta ruta — la verificación de `id_token` es criptografía de clave pública, sin secreto compartido. |
| `VITE_GOOGLE_OAUTH_CLIENT_ID` (frontend, `.env`) | Misma variable, mismo Client ID de Google Cloud Console — solo cambia qué función de la librería la consume (`google.accounts.id.initialize` en vez de `initTokenClient`). |

### Error handling

| Situación | Código | Origen |
|---|---|---|
| `id_token` ausente | `400` | `GoogleLoginSerializer.validate` |
| `id_token` con firma inválida o expirado | `400` | `_verify_and_decode` (allauth), propagado como `ValidationError` |
| `id_token` con `audience` distinto al `client_id` de Atenea | `400` | `_verify_and_decode` (allauth) — este es el caso que hoy el flujo de `access_token` no cubre |
| Correo sin cuenta provisionada (`login.is_existing` falso) | `400`, mensaje "No existe una cuenta para este correo. Contacta a la SAE." | `GoogleLoginSerializer.validate` (sin cambios respecto al comportamiento actual) |

### Testing

`GoogleLoginTests` (`backend/accounts/tests/test_auth.py`) mockea `GoogleOAuth2Adapter.complete_login` directamente, así que no ejercita hoy el parseo/verificación real del token — los tres tests existentes (`test_rejects_unprovisioned_email`, `test_connects_provisioned_email`, `test_sets_cookies_when_httponly_configured`) se actualizan para postear `{"id_token": "fake-token"}` en vez de `{"access_token": "fake-token"}`, con el mismo mock de `complete_login`. Se agregan además:

- Un test que confirma que un `POST` con solo `access_token` (sin `id_token`) es rechazado (`400`) — cierra explícitamente el transporte descartado.
- Un test que confirma que un `id_token` con `audience` incorrecto es rechazado — sin mockear `complete_login`, ejercitando la verificación real de `_decode_id_token`/`_verify_and_decode`.

### Nota sobre deuda técnica 0010

[Deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md) (`GET /api/auth/user/` no expone perfil/rol) queda **fuera de alcance de esta spec**, deliberadamente. Esta spec decide un cambio de transporte de autenticación; qué campos expone el endpoint de usuario autenticado es un cambio de forma de datos con su propia superficie (qué exponer, a quién, compatibilidad con lo que ya consume el body de creación de `Asesoria` — la misma razón que originalmente lo separó del plan de frontend que lo necesitaba). No resolverlo aquí no es una omisión silenciosa: la señal de revisión ya registrada en la propia deuda técnica 0010 sigue vigente y debe evaluarse **antes del paso 9 del ledger de progreso** (plan de implementación de login frontend), porque ese plan es el que decide la forma final de la respuesta de `loginWithGoogle`/`loginWithPassword` que consume `AuthContext.tsx`.

### Out of scope

- Authorization Code + PKCE — evaluada y descartada, ver [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md).
- Invalidación de refresh token en logout (`token_blacklist`) — deuda técnica 0007, sin cambios.
- Resolver deuda técnica 0010 en esta pasada — ver nota dedicada arriba.
- Activar CSRF en cookie JWT (`JWT_AUTH_COOKIE_USE_CSRF`) — deuda técnica 0009, decisión explícita de no activar en este trabajo, ver decisión 6.

### Self-review

- Sin placeholders/TBD — cada decisión tiene un valor concreto, confirmado por el usuario en esta conversación (elegir explícitamente la opción "Sign In With Google / ID token").
- Sin contradicciones con ADR 0018: las decisiones 2 y 3 de esa ADR se reafirman explícitamente sin cambios; solo la decisión 1 se reemplaza, y queda registrado en el changelog de esa misma ADR.
- Alcance cohesivo: esta spec cubre el transporte de autenticación con Google (backend + frontend) y el único defecto funcional real del flujo de login (`Landing.tsx`); no mezcla con la forma de datos de `/api/auth/user/` (deuda técnica 0010, explícitamente diferida) ni con el ciclo de vida del refresh token (deuda técnica 0007, sin cambios).
- Deuda técnica generada: ninguna nueva — este cambio cierra una brecha de seguridad, no la abre. Las deudas técnicas 0009 y 0010 ya existían; esta spec decide explícitamente no tocarlas ahora, con razón documentada en cada caso, tal como exige el plan que originó este paso.
- Completitud contra el plan original (`~/.claude/plans/parece-que-hubo-un-groovy-unicorn.md`, paso 2): cubre las cuatro cosas que ese paso pedía — reabrir la alternativa de transporte, reconfirmar el storage de JWT, decidir explícitamente sobre 0009/0010, e incluir el fix de `Landing.tsx`.
