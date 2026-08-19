# 0028 — Envío de correo real vía SMTP de Google Workspace, cuenta dedicada

**Status:** Accepted
**Date:** 2026-08-19

## Context

`asesorias/tasks.py` ya llama a `send_mail` (recordatorios/avisos de sesiones) y
`EMAIL_BACKEND` está configurado por variable de entorno desde el inicio (default
`console.EmailBackend`, ver `config/settings/base.py`), pero en producción nunca se
configuró un backend real: los correos no salen (deuda técnica, ver
[0021](../technical-debt/0021-smtp-cuenta-dedicada-app-password.md)).

Atenea corre bajo el dominio institucional `unam.dev`/Google Workspace de la
Facultad de Ciencias. Se evaluaron dos rutas para enviar correo real usando esa
cuenta de Workspace, sin presupuesto para un proveedor externo (SendGrid, SES,
Postmark, etc.):

- **(A) SMTP relay service de Google Workspace:** requiere que un admin del
  Workspace lo habilite en la consola de administración (Gmail → Enrutamiento →
  SMTP relay), configure una IP/rango permitido y no exija autenticación por
  cuenta — el backend solo necesita host/puerto. Es la opción más robusta (sin
  límite de 2000 msj/día por cuenta, no depende de una cuenta individual) pero
  requiere acceso de administrador al Workspace, que no está disponible hoy.
- **(B) Cuenta dedicada + contraseña de aplicación:** una cuenta de Workspace
  dedicada a Atenea (no una cuenta personal) autentica directo contra
  `smtp.gmail.com:587` con una contraseña de aplicación de 16 caracteres. No
  requiere permisos de administrador, solo que el admin no haya deshabilitado
  las contraseñas de aplicación a nivel organización.

El uso del SMTP relay de Gmail sin la cuenta dedicada explícitamente separada
(es decir, relayar como si fuera cualquier cuenta genérica) **no fue
autorizado** — la vía aprobada es la cuenta dedicada de Workspace.

## Decision

- Enviar correo por SMTP autenticado (`django.core.mail.backends.smtp.EmailBackend`)
  usando una cuenta de Workspace **dedicada** a Atenea (no una cuenta personal ni
  compartida con otro servicio de la SAE), con una contraseña de aplicación
  generada para esa cuenta.
- Configuración 100% por variables de entorno (`EMAIL_HOST`, `EMAIL_PORT`,
  `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`), con defaults de
  `smtp.gmail.com:587`/TLS en `config/settings/base.py` — igual que el resto de
  la configuración sensible ([ADR 0009](0009-settings-split-django-environ.md)).
- `DEFAULT_FROM_EMAIL` se fija al mismo address de `EMAIL_HOST_USER`: Gmail
  rechaza o marca como spoofing un `From` que no coincida con la cuenta
  autenticada (o un alias "send as" configurado), y no se configuró ningún alias.
- El worker de Celery (`atenea-worker`), no solo el backend web, necesita estas
  credenciales — es quien ejecuta `asesorias/tasks.py`.

## Consequences

- Correo real funciona sin depender de un admin de Workspace ni de presupuesto
  para un proveedor externo.
- Límite de envío atado a la cuenta individual (~2000 mensajes/día, límites de
  Gmail para envíos "sospechosos" en ráfaga). Ver deuda técnica
  [0021](../technical-debt/0021-smtp-cuenta-dedicada-app-password.md) para la
  señal de cuándo migrar a la opción (A).
- La contraseña de aplicación es un secreto más en `services/.env` (rotación
  documentada en [`despliegue-produccion.md`](../development/despliegue-produccion.md)).
- Migrar a la opción (A) más adelante no requiere cambios de código: solo
  cambian los valores de `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` (o se retira la
  autenticación si el relay no la exige) vía variables de entorno.

## Alternatives considered

- **SMTP relay de Google Workspace (opción A):** más robusto y sin deuda, pero
  requiere acceso de administrador al Workspace no disponible actualmente.
  Queda como mejora futura si se obtiene ese acceso.
- **Proveedor transaccional externo (SendGrid/SES/Postmark, etc.):** fuera de
  alcance por presupuesto cero; además introduciría una dependencia externa
  nueva que el proyecto no tenía.
- **Cuenta personal de un miembro del equipo en vez de una cuenta dedicada:**
  rechazada explícitamente — acopla el envío de correo institucional a una
  cuenta individual (riesgo si esa persona sale del proyecto, mezcla de
  responsabilidad) y es lo que específicamente no se autorizó.
