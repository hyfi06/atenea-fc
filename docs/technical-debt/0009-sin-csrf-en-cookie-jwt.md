# 0009 — Sin protección CSRF explícita en el transporte de JWT por cookie

**Estado:** Activa
**Origen:** [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md)

## Qué se simplificó

En prod, el JWT viaja como cookie `httpOnly`+`Secure` (`JWTCookieAuthentication`). La librería (`dj-rest-auth`) soporta forzar validación CSRF sobre requests autenticados por cookie vía `JWT_AUTH_COOKIE_USE_CSRF`, pero el proyecto deja ese flag en su default (`False`): las requests que autentican vía cookie no requieren un header CSRF adicional.

## Por qué era razonable

`JWT_AUTH_SAMESITE` queda en su default (`Lax`), y ADR 0018 ya asume que en prod frontend y backend se despliegan bajo una topología conocida (mismo sitio/subdominios de Atenea, no orígenes arbitrarios) — con `SameSite=Lax`, el navegador no adjunta la cookie en requests cross-site iniciados por JS desde un origen ajeno, lo que ya mitiga el escenario clásico de CSRF contra este endpoint. Activar `JWT_AUTH_COOKIE_USE_CSRF` exigiría además que el frontend lea y reenvíe un token CSRF en cada request de escritura (`POST`/`PATCH`/`DELETE`), trabajo de frontend no pedido en este pase.

## Señal de revisión

Si la topología de despliegue cambia (frontend y backend dejan de compartir dominio/subdominio — p. ej. frontend servido desde un CDN con dominio propio), o si se detecta/sospecha un intento de CSRF contra un endpoint autenticado por cookie, activar `JWT_AUTH_COOKIE_USE_CSRF=True` y coordinar el trabajo correspondiente en `api/client.ts` del frontend.
