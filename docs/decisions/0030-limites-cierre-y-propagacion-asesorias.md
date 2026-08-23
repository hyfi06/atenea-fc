# 0030 — Ventana de anticipación y resincronización en Asesorías

**Status:** Accepted
**Date:** 2026-08-19

## Context

Dos deudas técnicas de la app `asesorias` comparten modelo (`Asesoria`,
`Disponibilidad`) y se atacan juntas:

- [0003](../technical-debt/0003-sin-limites-uso-asesorias.md) — sin límites de
  uso: un alumno podía agendar o cancelar hasta el segundo anterior a la sesión,
  dejando al asesor sin margen para enterarse.
- [0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md) — `Asesoria`
  congela un snapshot de `formato`/`ubicacion`/`liga_virtual` al agendar, y
  corregir un typo en la `Disponibilidad` (una liga de Zoom mal escrita) no
  llegaba a las sesiones ya agendadas.

La exploración inicial de este plan agrupaba una tercera deuda —
[0004](../technical-debt/0004-sin-cierre-automatico-recordatorios.md), cierre
automático de sesiones vencidas vía Celery Beat — por compartir el mismo
modelo. Se decidió dejarla fuera de este sprint antes de arrancar la
implementación (ver el spec de este plan); la deuda 0004 sigue Activa, sin
cambios.

## Decision

1. **Ventana mínima de anticipación de 2 horas.** `Asesoria.clean()` rechaza
   agendar y `Asesoria.cancelar()` rechaza cancelar cuando falta menos de
   `VENTANA_MINIMA_ANTICIPACION = timedelta(hours=2)` para el inicio. Los dos
   mensajes de error son distintos y están redactados para mostrarse tal cual en
   el SPA. `Asesoria.momento_inicio` es la única fuente que combina `fecha` y
   `hora_inicio` en un datetime aware; también la usa `marcar_asistencia()`.
2. **`cancelar(..., forzar=True)` salta la ventana**, y es lo que pasa
   `Disponibilidad.desactivar()`. Dar de baja un horario no es el alumno
   cancelando de último minuto: es el asesor invalidando el bloque completo, y
   bloquearlo lo dejaría sin forma de darlo de baja. La regla vive en un solo
   lugar (`cancelar()`) y el bypass es explícito y testeado, no accidental.
3. **`POST /api/asesorias/disponibilidades/{id}/resincronizar/`** copia
   `formato`, `ubicacion` y `liga_virtual` actuales del bloque a todas las
   sesiones de `sesiones_futuras()` y encola
   `enviar_notificacion_resincronizacion` por cada una. **No** toca
   `hora_inicio`. Vive en el `DisponibilidadViewSet` del asesor, restringido al
   dueño del registro, no en un `Admin*View` con `EsMiembroSAE`: es el asesor
   corrigiendo un dato suyo, no una intervención administrativa.

## Consequences

- El SPA debe mostrar los dos mensajes nuevos de `400` y, idealmente, dejar de
  ofrecer los botones de agendar/cancelar dentro de la ventana. El contrato está
  en [`api-frontend.md`](../development/api-frontend.md); la UI queda fuera del
  alcance de este ADR.
- La deuda 0003 queda **parcialmente** resuelta; la 0005 queda **resuelta**. La
  deuda 0004 (cierre automático, recordatorios periódicos) se evaluó y quedó
  fuera de este sprint — sigue Activa, sin ninguna pieza resuelta.

## Alternatives considered

- **Meter la ventana de 2 horas en el serializer en vez del modelo:** dejaría
  `Disponibilidad.desactivar()` (que no pasa por el serializer) sin la regla y
  duplicaría la lógica entre agendar y cancelar. Rechazada: la validación de
  negocio de esta app ya vive en el modelo.
- **Un flag global tipo `saltar_validaciones` en vez de `forzar` en
  `cancelar()`:** más ancho de lo necesario y difícil de auditar. `forzar` es
  keyword-only, con un único call site.
- **Acción de `django.contrib.admin` en `DisponibilidadAdmin` para
  resincronizar:** el resto del área administrativa del proyecto usa vistas DRF
  dedicadas, no admin actions, y además el dueño natural de la operación es el
  asesor, que no entra al admin de Django.
- **Propagar también `hora_inicio`:** cambiar la hora de una sesión ya agendada
  es otra operación, con otras consecuencias para el alumno (puede dejar de
  poder asistir). Fuera de alcance.
- **Propagar automáticamente en el `PATCH` de la disponibilidad, sin endpoint
  aparte:** rompería el snapshot deliberado que motiva la deuda 0005 — no todo
  cambio del bloque debe alcanzar a las sesiones ya agendadas. Que sea una
  acción explícita mantiene la decisión en manos del asesor.
