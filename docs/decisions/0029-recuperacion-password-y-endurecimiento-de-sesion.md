# 0029 — Recuperación de contraseña y endurecimiento de la sesión

**Status:** Accepted
**Date:** 2026-08-19

## Context

Tres piezas del bloque Auth del sprint, agrupadas porque comparten código (`accounts/`) y contexto: el pentest de staging del 2026-08-18 y el SMTP de Workspace ya configurado ([ADR 0028](0028-envio-correo-smtp-cuenta-dedicada.md)).

1. Las cuentas que no entran por Google (staff, SAE, asesores no-alumnos) no tenían forma de recuperar su contraseña. El backend de reset de `dj-rest-auth` ya funcionaba end-to-end —había un test pasando— pero no estaba expuesto en el SPA ni acotado a las cuentas a las que aplica.
2. [Deuda 0007](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md): el logout no invalidaba el refresh token en el servidor.
3. [Deuda 0009](../technical-debt/0009-sin-csrf-en-cookie-jwt.md): sin CSRF explícito sobre el JWT en cookie. El pentest lo reprodujo en vivo: una escritura autenticada solo con la cookie, sin ningún token CSRF, era aceptada.

## Decision

**1. El reset se acota a cuentas con contraseña usable.** No se agrega un campo de "tipo de cuenta" a `User`: la distinción es de comportamiento (los alumnos se dan de alta sin contraseña y entran por Google; las cuentas con contraseña se crean desde el admin) y `has_usable_password()` es el criterio verificable. `accounts.serializers.PasswordResetSerializer.validate_email` vacía `reset_form.users` en vez de levantar un error, para caer en el mismo camino que un correo desconocido: la respuesta queda indistinguible y no filtra ni qué cuentas existen ni de qué tipo son. Como efecto lateral se apaga `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS`: ese correo de allauth invita a un auto-registro que Atenea no tiene, y además reventaba con `NoReverseMatch` porque `allauth.urls` no está incluido en `config/urls.py`.

**2. El flujo de reset tiene scopes de throttle propios**, `password_reset` (3/hour) y `password_reset_confirm` (10/hour), sobre `CloudflareScopedRateThrottle`. Antes compartía el scope `dj_rest_auth` (5/min) con el login: quien golpeara reset consumía el cupo de quien intenta entrar, y al revés. Son dos scopes y no uno porque pedir el enlace dispara un correo y es rarísimo en operación normal, mientras que confirmarlo no manda nada y el usuario puede fallar los validadores de contraseña varias veces seguidas. Se montan como subclases delgadas en `accounts/views.py`, antes del `include` de `dj_rest_auth.urls` — el mismo patrón que ya usaba `AteneaLoginView`.

**3. El logout invalida el refresh token**, instalando `rest_framework_simplejwt.token_blacklist`. La lógica ya vivía en `dj_rest_auth.views.LogoutView.logout()`, condicionada únicamente a que la app estuviera en `INSTALLED_APPS`. Consecuencia de contrato: a partir de aquí el logout **exige** el refresh —en el body si `JWT_AUTH_HTTPONLY=False` (dev), en la cookie si es `True` (prod)— o responde 401.

**4. Las escrituras autenticadas por cookie exigen CSRF** (`JWT_AUTH_COOKIE_USE_CSRF = True`, solo en `prod.py`). `SameSite=Lax` no bastaba: se evalúa sobre el dominio registrable, así que un subdominio hermano bajo el mismo dominio padre sigue siendo "same-site" y podía postear con la cookie adjunta. Para que el SPA tenga qué reenviar, las vistas de login, de Google y de `/api/auth/user/` se decoran con `ensure_csrf_cookie`: Django solo emite la cookie `csrftoken` si alguna vista llama `get_token(request)`, y el SPA se sirve desde nginx, así que su primer contacto con Django es una de esas tres. El `GET /api/auth/user/` que el SPA hace al montar cubre además la transición: una sesión abierta desde antes del cambio recibe su cookie sin tener que volver a entrar (GET es método seguro y nunca se rechaza por CSRF).

## Consequences

- Las cuentas con contraseña tienen recuperación real, con dos pantallas nuevas en el SPA (`/forgot-password`, `/reset-password/:uid/:token`) y el botón del login por fin conectado.
- Un refresh token robado deja de servir en cuanto el usuario cierra sesión; se cierra la deuda 0007.
- El vector CSRF confirmado en el pentest queda cerrado, con test de regresión; se cierra la deuda 0009.
- Todo cliente nuevo que escriba contra la API en prod tiene que reenviar `X-CSRFToken`. Ya no basta con la cookie.
- Aparecen dos ítems de deuda nuevos: [0023](../technical-debt/0023-correo-de-reset-con-template-default.md) (el correo usa el template default de allauth) y [0024](../technical-debt/0024-blacklist-sin-purga-de-tokens-vencidos.md) (las tablas del blacklist crecen sin purga).

## Alternatives considered

- **Agregar un campo `tipo_cuenta` a `User`.** Explícito y consultable, pero duplica un estado que ya existe (`has_usable_password()`) y hay que mantenerlo sincronizado con cada alta. Se descarta hasta que exista un caso que necesite distinguir tipos que `has_usable_password()` no distinga.
- **Rechazar con 400 el reset de una cuenta Google-only**, con un mensaje que diga "esa cuenta entra con Google". Es más amable, pero convierte el endpoint en un oráculo de enumeración: distingue correo inexistente de correo existente y además revela el tipo de cuenta.
- **Un solo scope de throttle para todo el flujo de reset.** Más simple, pero fallar dos veces el validador de contraseña dejaría al usuario sin poder pedir un enlace nuevo durante una hora.
- **Rotar el refresh token (`ROTATE_REFRESH_TOKENS = True`) en vez de instalar el blacklist.** Acota la ventana de un token robado, pero no resuelve el caso pedido —"cerré sesión, el token ya no debe servir"— y obliga al SPA a reescribir su token guardado en cada refresh.
- **`JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED = True`.** Exigiría CSRF también en el login, que es justo el request donde el SPA todavía no tiene cookie. Se descarta.
