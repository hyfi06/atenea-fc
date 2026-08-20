# 0007 — Logout no invalida el refresh token en el servidor

**Estado:** Resuelta — 2026-08-19 ([ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md))
**Origen:** [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md)

## Qué se simplificó

El proyecto no tiene instalada `rest_framework_simplejwt.token_blacklist`. `POST /api/auth/logout/` limpia el token/cookie del lado del cliente, pero el refresh token sigue siendo válido en el servidor hasta su expiración natural (`REFRESH_TOKEN_LIFETIME = 7 días`) aunque el usuario "cierre sesión".

## Por qué era razonable

Instalar `token_blacklist` implica una app y una migración nuevas, no pedidas por ningún flujo actual; automatizar la invalidación antes de que el riesgo real lo justifique (más usuarios activos, JWT como cookie `httpOnly` en prod desde ADR 0018) es prematuro.

## Señal de revisión

Un incidente de seguridad real o sospechado donde un refresh token robado o filtrado siga siendo válido después de que el usuario cerró sesión; o, más simple, en cuanto el equipo decida invertir en revocación de sesión como feature (ej. "cerrar sesión en todos los dispositivos").

## Cómo se resolvió (2026-08-19)

Se instaló `rest_framework_simplejwt.token_blacklist`: la lógica de invalidación ya vivía en `dj_rest_auth.views.LogoutView.logout()`, condicionada solo a que la app estuviera en `INSTALLED_APPS`. Consecuencia de contrato: el logout ahora **exige** el refresh token —en el body en dev, en la cookie `atenea-refresh-token` en prod— o responde 401; `frontend/src/auth/AuthContext.tsx` lo manda en dev. Cubierto por `accounts/tests/test_auth.py::LogoutBlacklistTests`. Queda abierta la [deuda 0024](0024-blacklist-sin-purga-de-tokens-vencidos.md): las tablas del blacklist no se purgan.
