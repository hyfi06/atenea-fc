# 0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas

**Estado:** Resuelta — 2026-08-19 ([ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md))
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

`Asesoria` guarda un snapshot de `formato`/`ubicacion`/`liga_virtual` al momento de agendar. Si el asesor corrige un dato erróneo en la `Disponibilidad` (ej. una liga de Zoom mal escrita) después de que ya hay sesiones agendadas sobre ese bloque, la corrección no llega a esas sesiones — hay que corregirlas una por una.

## Por qué era razonable

El snapshot es deliberado (una `Asesoria` no debe cambiar de lugar/formato retroactivamente sin que el alumno se entere), y el caso de "corregir un typo después de agendar" se juzgó infrecuente frente a la complejidad de decidir cuándo propagar y cuándo no.

## Señal de revisión

Si se vuelve un problema operativo recurrente, la opción más simple es un endpoint/acción de admin para "reemplazar el snapshot de una Asesoria agendada desde su Disponibilidad actual", no cambiar el modelo de snapshot en sí.

## Cómo se resolvió

Exactamente por la vía que anticipaba la señal de revisión, con el dueño ajustado: `POST /api/asesorias/disponibilidades/{id}/resincronizar/` (acción del `DisponibilidadViewSet`, restringida al asesor dueño del registro, no a `EsMiembroSAE` — es el asesor corrigiendo su propio dato). Copia `formato`, `ubicacion` y `liga_virtual` actuales del bloque a todas las sesiones de `Disponibilidad.sesiones_futuras()` y encola `enviar_notificacion_resincronizacion` por cada alumno afectado.

El modelo de snapshot **no cambió**: la propagación sigue siendo una acción explícita del asesor, no un efecto automático del `PATCH`. `hora_inicio` queda fuera a propósito — mover la hora de una sesión ya agendada es otra operación.

**Pendiente:** el backend está completo y probado, pero ningún botón del SPA dispara este endpoint todavía — ver [deuda 0025](0025-resincronizar-sin-boton-en-spa.md).
