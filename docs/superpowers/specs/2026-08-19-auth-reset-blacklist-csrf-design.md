# Auth: password reset, blacklist de logout y CSRF en cookie JWT

**Fecha:** 2026-08-19
**Estado:** Aprobado para plan de implementación

## Contexto

Tres piezas del bloque Auth de este sprint, agrupadas porque comparten código (`accounts/`) y contexto reciente (pentest de staging, 2026-08-18):

1. **Password reset** (feature nueva, no deuda registrada) — las cuentas que no usan Google OAuth (login con password: staff, SAE, asesores no-alumnos) no tienen forma de recuperar su contraseña. Ya se configuró SMTP de Workspace (ADR 0028) — hay que aprovecharlo.
2. **[Deuda 0007](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md)** — logout no invalida el refresh token en el servidor.
3. **[Deuda 0009](../technical-debt/0009-sin-csrf-en-cookie-jwt.md)** — sin protección CSRF explícita en cookie JWT (confirmado explotable en pentest de staging, 2026-08-18).

## Hallazgos clave de la exploración

- **No hay campo de "tipo de cuenta"** en el modelo `User` (`accounts/models.py`). La distinción password-based vs. Google es de comportamiento, no de dato: los alumnos se crean vía `cargar_alumnos.py` con `.create()` (sin `set_password`, password no usable), las cuentas con password se crean solo desde el admin de Django (`UserAdmin.add_fieldsets`). El criterio verificable es `user.has_usable_password()` (built-in de `AbstractBaseUser`).
- **dj-rest-auth ya monta** `POST /api/auth/password/reset/` y `/password/reset/confirm/` (`dj_rest_auth.urls` incluido en `accounts/urls.py`), con `PasswordResetSerializer` propio (`accounts/serializers.py`) que ya genera la URL hacia `{FRONTEND_URL}/reset-password/{uid}/{temp_key}/`. **Ya hay un test end-to-end pasando** (`accounts/tests/test_auth.py::PasswordResetLoginFlowTests`) que ejercita reset → confirm → login → refresh leyendo el link desde `mail.outbox`. Es decir: el backend de reset **ya funciona** contra cualquier cuenta con password usable. Lo que falta es acotarlo a cuentas password-based y exponerlo en el frontend.
- **El botón "¿Olvidaste tu contraseña?" ya existe** en `Login.tsx` sin handler. No existe la pantalla ni la ruta `/reset-password/:uid/:token` en el frontend.
- **Blacklist de logout es casi gratis**: `dj_rest_auth.views.LogoutView.logout()` ya contiene toda la lógica, condicionada solo a que `'rest_framework_simplejwt.token_blacklist'` esté en `INSTALLED_APPS`. El trabajo real es: agregar la app, migrar, y verificar que el frontend mande el refresh token en el body del logout en dev (en prod lo toma de la cookie httponly automáticamente; en dev el `AuthContext.tsx` actual llama `apiPost('/api/auth/logout/', {})` sin el refresh — hay que corregirlo o el blacklist fallará con 401 en dev).
- **CSRF en cookie**: activar `JWT_AUTH_COOKIE_USE_CSRF=True` en `prod.py` obliga al frontend a leer la cookie CSRF (`csrftoken`, generada por Django) y reenviarla como header (`X-CSRFToken`) en cada request de escritura (`POST`/`PATCH`/`DELETE`) autenticada por cookie. Hoy `api/client.ts` no lee ni reenvía ese header.
- **Rate limiting ya cubre reset "gratis"**: `CloudflareScopedRateThrottle` + `DEFAULT_THROTTLE_RATES["dj_rest_auth"] = "5/min"` aplica automáticamente a `PasswordResetView`/`PasswordResetConfirmView` porque ambas ya traen `throttle_scope = 'dj_rest_auth'` de fábrica — comparten cupo con login. El pedido explícito de "configuremos rate limit para este flujo" se interpreta como: darle un scope propio, más estricto, para que un atacante golpeando reset no consuma el cupo de otros usuarios intentando login, y viceversa.

## Diseño

### 1. Password reset acotado a cuentas password-based

- Sobrescribir `PasswordResetSerializer.validate_email` (`accounts/serializers.py`) para rechazar (con el mismo mensaje genérico que hoy, sin filtrar si el correo existe) cuando el usuario asociado no tenga `has_usable_password()` — evita que alguien pida "reset" de una cuenta que solo puede entrar por Google, lo cual generaría un correo confuso ("nunca pediste una contraseña").
- Respuesta debe ser indistinguible entre "correo no existe" y "correo es Google-only", para no filtrar qué cuentas existen ni su tipo (mismo patrón de no-enumeración que ya usa dj-rest-auth por default).
- Nueva pantalla en frontend: `ForgotPassword.tsx` (pide email, llama `POST /api/auth/password/reset/`) y `ResetPassword.tsx` (ruta `/reset-password/:uid/:token`, pide password nueva, llama `POST /api/auth/password/reset/confirm/`). Ambas siguen el patrón de `Login.tsx` / `AuthContext.tsx` ya existente (usar `apiPost`, mismo layout de formulario).
- Conectar el botón placeholder de `Login.tsx:108-110` a la navegación hacia `/forgot-password`.

### 2. Rate limit dedicado para password reset

- Nuevo scope `"password_reset"` en `DEFAULT_THROTTLE_RATES` (`config/settings/base.py`), rate a definir (propuesta: `3/hour` por IP real vía `CloudflareScopedRateThrottle`, ya que reset es una acción rara en operación normal — 5/min es demasiado generoso para un flujo que dispara envío de correo).
- Subclases delgadas de `PasswordResetView`/`PasswordResetConfirmView` en `accounts/views.py` que solo overridan `throttle_scope = "password_reset"`, montadas en `accounts/urls.py` en vez del include genérico para esas dos rutas específicas (mismo patrón que `AteneaLoginView` ya usa para override sobre `rest_login`).

### 3. Blacklist de refresh token en logout (deuda 0007)

- Agregar `'rest_framework_simplejwt.token_blacklist'` a `THIRD_PARTY_APPS`, generar y aplicar la migración (crea `OutstandingToken`/`BlacklistedToken`).
- Corregir `AuthContext.tsx` (logout) para incluir `{ refresh: <token> }` en el body cuando la app corre en dev (`!import.meta.env.PROD`) — en prod la librería ya lo toma de la cookie httponly, no requiere cambio de frontend ahí.
- Marcar deuda 0007 como resuelta al terminar, con referencia al commit.

### 4. CSRF en cookie JWT (deuda 0009)

- Activar `JWT_AUTH_COOKIE_USE_CSRF = True` en `config/settings/prod.py` (solo prod; en dev el JWT no viaja en cookie httponly).
- Frontend: `api/client.ts` debe leer la cookie `csrftoken` (Django la setea automáticamente al servir cualquier vista que use `CsrfViewMiddleware`; puede requerir que el backend garantice que se emite en el primer request, p. ej. vista de login) y reenviarla como header `X-CSRFToken` en todo `apiPost`/`apiPatch`/`apiDelete`.
- Marcar deuda 0009 como resuelta al terminar, con referencia al commit.

### Testing

- Reusar y extender `PasswordResetLoginFlowTests` (ya existe) para: (a) reset rechazado sobre cuenta sin password usable, (b) rate limit dedicado no comparte cupo con login (mismo patrón que `LoginThrottleTests`, incluyendo el caso de spoofing de `X-Forwarded-For`).
- Nuevo test: logout con blacklist activo — verificar que un refresh usado después de logout es rechazado por `/api/auth/token/refresh/`.
- Nuevo test: request de escritura autenticado solo por cookie, sin header CSRF, debe ser rechazado (403) una vez activado `JWT_AUTH_COOKIE_USE_CSRF` — este es el caso que el pentest de staging explotó, debe quedar como regression test.
- Frontend: tests de `ForgotPassword`/`ResetPassword` (si el proyecto tiene suite frontend — confirmar convención existente antes de escribir).

### Fuera de alcance

- Personalizar el template del correo de reset (dj-rest-auth usa el default de allauth salvo que se sobreescriba) — no se pidió, se deja para una iteración de contenido si la SAE lo solicita.
- Registro público de cuentas — sigue cerrado (`is_open_for_signup=False`), no cambia con este trabajo.
