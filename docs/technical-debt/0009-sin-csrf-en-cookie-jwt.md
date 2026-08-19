# 0009 — Sin protección CSRF explícita en el transporte de JWT por cookie

**Estado:** Activa
**Origen:** [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md)

## Qué se simplificó

En prod, el JWT viaja como cookie `httpOnly`+`Secure` (`JWTCookieAuthentication`). La librería (`dj-rest-auth`) soporta forzar validación CSRF sobre requests autenticados por cookie vía `JWT_AUTH_COOKIE_USE_CSRF`, pero el proyecto deja ese flag en su default (`False`): las requests que autentican vía cookie no requieren un header CSRF adicional.

## Por qué era razonable

`JWT_AUTH_SAMESITE` se fija explícitamente en `"Lax"` (ver `config/settings/prod.py`), y `SameSite=Lax` sí bloquea el escenario clásico de CSRF: un request cross-site iniciado por JS (`fetch`/`XHR`) desde un origen ajeno no adjunta la cookie. Pero `SameSite` se evalúa sobre el **dominio registrable** (eTLD+1), no sobre el origen exacto: cualquier subdominio hermano bajo el mismo dominio padre (p. ej. otro sitio o servicio no relacionado de la misma institución, `otro-servicio.dominio.mx` junto a `atenea.dominio.mx`) sigue siendo "same-site" para efectos de la cookie. Un `<form>` HTML plano con `method="POST"` alojado en ese subdominio hermano — sin necesitar JS ni leer la cookie — sí la adjunta, porque los parsers default de DRF aceptan `application/x-www-form-urlencoded` y `APIView` es CSRF-exempt por default (no usa el middleware CSRF de Django salvo para vistas de sesión). El riesgo residual real no es "frontend y backend comparten dominio" (eso es cierto y no es el problema); es que **cualquier otro subdominio bajo ese mismo dominio padre, controlado o no por este proyecto, también cuenta como same-site**. Activar `JWT_AUTH_COOKIE_USE_CSRF` cerraría ese hueco, pero exigiría además que el frontend lea y reenvíe un token CSRF en cada request de escritura (`POST`/`PATCH`/`DELETE`), trabajo de frontend no pedido en este pase.

## Señal de revisión

Si se identifica un endpoint de escritura (`POST`/`PATCH`/`DELETE`) accesible desde un subdominio hermano no controlado por este proyecto vía POST con `application/x-www-form-urlencoded`, o si el despliegue pasa a compartir dominio/subdominio con contenido de terceros no confiable, activar `JWT_AUTH_COOKIE_USE_CSRF=True` y coordinar el trabajo correspondiente en `api/client.ts` del frontend.

## Confirmado en vivo (2026-08-18)

Pentest contra staging reprodujo el POST de escritura autenticada (agendar
una Asesoria) sin token CSRF ni header custom, solo con la cookie —
aceptado por la API. Sigue activa; `SameSite=Lax` en las cookies JWT
mitiga el vector de formulario cross-site clásico. Ver auditoría:
https://claude.ai/code/artifact/e73411a0-fdae-405e-ab8f-d38b56482f9e
