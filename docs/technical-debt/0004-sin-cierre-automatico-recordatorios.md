# 0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos

**Estado:** Activa
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

Una `Asesoria` en estado `agendada` cuya fecha ya pasó sin que el asesor marque asistencia se queda así indefinidamente — no hay tarea Celery Beat que la cierre. Tampoco hay recordatorio por email antes de la sesión, solo confirmación al agendar y notificación al cancelar.

## Por qué era razonable

Requiere Celery Beat (no solo tareas async puntuales) y una decisión de producto sobre qué hacer con una sesión "abandonada" (¿marcarla como no-asistida automáticamente? ¿dejarla pendiente?) que no estaba resuelta al diseñar el MVP.

## Señal de revisión

Cuando el volumen de sesiones "huérfanas" (agendadas, vencidas, sin marcar) sea alto en los reportes que use la SAE, o cuando se necesite el dato de asistencia agregado sin depender de que el asesor la marque manualmente.
