# 0010 — Modelo de usuario personalizado con email como identificador

**Status:** Accepted
**Date:** 2026-07-27

## Context

El login de Atenea es vía Google OAuth (ver [0003](0003-google-oauth-allauth-jwt.md)) — no existe un flujo de registro con username/password. Django recomienda explícitamente definir un modelo de usuario personalizado (`AUTH_USER_MODEL`) antes de la primera migración: cambiarlo después, con datos reales ya en la base, requiere migraciones muy riesgosas.

## Decision

- Definir `accounts.User` como `AUTH_USER_MODEL` desde el primer commit de settings, antes de generar cualquier migración.
- `User` hereda de `AbstractBaseUser` + `PermissionsMixin` (no de `AbstractUser`, que trae un campo `username` que no se va a usar).
- `email` es el `USERNAME_FIELD` (único, obligatorio); no existe campo `username`.
- Como `AbstractBaseUser` no trae manager, se implementa un `UserManager` propio (`create_user`/`create_superuser` basados en email) en `accounts/managers.py`.
- El `UserAdmin` de Django por defecto referencia `username` en `fieldsets`/`ordering`; se sobreescribe en `accounts/admin.py` con equivalentes basados en email.

## Consequences

- `createsuperuser` y el login de Django admin funcionan con email+password desde el día uno, coherente con que el identificador real del sistema (incluso antes de que el login de Google esté conectado) es el correo.
- Cualquier app futura que agregue campos al usuario (rol dentro de la SAE, relación con el perfil de estudiante, etc.) extiende este modelo ya existente, sin necesidad de una migración de reemplazo de modelo de usuario.
- Requiere mantener el `UserManager` y el `UserAdmin` personalizados al día conforme el modelo crezca — es código adicional comparado con usar el `User` default de Django.

## Alternatives considered

- **Usar el `User` default de Django (con `username`):** más rápido de arrancar, pero incompatible con un login basado enteramente en email/Google, y migrar a un modelo personalizado después de tener usuarios reales es una operación de alto riesgo que Django mismo desaconseja.
- **`AbstractUser` con `username` = email:** evita escribir un manager propio, pero deja un campo `username` "fantasma" sin uso real que puede confundir a alguien aprendiendo el modelo de datos.
