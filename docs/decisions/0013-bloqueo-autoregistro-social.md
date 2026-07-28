# 0013 — Por qué `is_open_for_signup` no basta para bloquear auto-registro por Google

**Status:** Accepted
**Date:** 2026-07-28

## Context

Requisito del negocio: las cuentas de Atenea siempre las crea el personal de la SAE (por acceso a un correo @ciencias existente, o por invitación con password) — nunca hay autorregistro, ni por email+password ni por Google OAuth (ver ADR 0003, ADR 0010).

El punto de extensión documentado de `django-allauth` para bloquear autorregistro es sobreescribir `is_open_for_signup()` en un adapter (`ACCOUNT_ADAPTER`/`SOCIALACCOUNT_ADAPTER`). Al implementar el login de Google con `dj-rest-auth` (`SocialLoginView` + `SocialLoginSerializer`), se encontró que **ese hook por sí solo no impide que se cree una cuenta nueva** en el flujo real usado por la API JSON.

## Decision

Se investigó el código fuente real de las versiones instaladas (`django-allauth==65.18.0`, `dj-rest-auth==7.2.0`), no solo la documentación:

- `dj_rest_auth.registration.serializers.SocialLoginSerializer.validate()` llama a `complete_social_login(request, login)`. Internamente, `allauth.socialaccount.internal.flows.login.complete_login()` sí respeta `is_open_for_signup()` para un login social genuinamente nuevo — pero cuando lo bloquea, lanza `SignupClosedException`, que ese mismo código **atrapa y convierte en un `HttpResponse` renderizado** (una plantilla HTML, no una excepción que se propague).
- `SocialLoginSerializer.validate()` solo revisa `isinstance(ret, HttpResponseBadRequest)` — un `HttpResponse` normal nunca cae en ese caso, así que el rechazo de allauth queda silenciosamente ignorado.
- Inmediatamente después, `dj-rest-auth` tiene su propia rama: `if not login.is_existing: ... login.save(request, connect=True)` — **crea la cuenta sin condición**, sin volver a consultar `is_open_for_signup()`.

Es decir: `is_open_for_signup() = False` bloquea correctamente cualquier flujo que pase por las vistas propias de allauth (server-rendered), pero **no** el endpoint JSON de `dj-rest-auth`, que es el único que este proyecto usa.

**Mecanismo real usado**: `SOCIALACCOUNT_EMAIL_AUTHENTICATION = True` + `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True`. Cuando el email verificado del login de Google coincide con un `User` ya existente, allauth marca `sociallogin.is_existing = True` y conecta la cuenta **sin pasar por `is_open_for_signup`/`process_signup` en absoluto** — es el camino diseñado específicamente para "cuenta pre-aprovisionada, la conecta el primer login social". Para el caso sin coincidencia, se sobreescribió `GoogleLoginSerializer.validate()` (copia completa del método de `dj-rest-auth`, no hay un hook más chico disponible) reemplazando el bloque final de auto-creación por un `raise ValidationError(...)` explícito.

`is_open_for_signup() = False` en los adapters (`accounts/adapters.py`) se mantiene como defensa en profundidad para cualquier otro flujo de allauth (ej. vistas server-rendered que este proyecto no expone hoy, pero podrían agregarse).

## Consequences

- El rechazo de emails de Google sin cuenta previa depende de un override completo de `SocialLoginSerializer.validate()`, no de un setting declarativo — si `dj-rest-auth` cambia esa función en una versión futura, este override necesita revisarse manualmente (no hay tests de la librería que nos avisen).
- Cubierto por tests automatizados (`accounts/tests/test_auth.py`) que mockean `GoogleOAuth2Adapter.complete_login` para simular ambos casos (email sin cuenta → rechazo sin crear usuario; email con cuenta → conexión exitosa) sin depender de credenciales reales de Google.
- Un login de Google con un token realmente inválido (no simplemente "email no aprovisionado") produce un 500 sin manejar, porque el `except HTTPError` heredado de `dj-rest-auth` no cubre todas las excepciones que puede lanzar el intercambio real con la API de Google (ej. `OAuth2Error` al pedir el userinfo) — comportamiento preexistente de la librería, no introducido aquí; no se corrigió por estar fuera de alcance de esta pasada.

## Alternatives considered

- **Confiar solo en `is_open_for_signup`**: descartado — confirmado por lectura de código que no aplica al endpoint JSON de `dj-rest-auth`.
- **Revertir manualmente la cuenta creada** (detectar la auto-creación después del hecho y borrarla): descartado por frágil y con condiciones de carrera; mejor prevenir la creación desde el inicio.
- **No usar `dj-rest-auth` para el login social, implementar el intercambio de token con Google a mano**: más control, pero reimplementa manejo de tokens/CSRF/PKCE que la librería ya resuelve — se prefirió corregir el punto específico que fallaba en vez de descartar la librería completa.
