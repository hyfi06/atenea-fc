# 0026 — El wizard de agendado ofrece bloques que la ventana mínima de 2 horas ya rechazaría

**Estado:** Activa
**Origen:** [ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md)

## Qué se simplificó

`GET /api/asesorias/disponibilidad/buscar/` no filtra por hora del día — devuelve todos los bloques dentro de la ventana agendable (semana en curso y la siguiente), incluyendo los de hoy que ya arrancaron o que arrancan en menos de 2 horas. El wizard de `/asesorias/nueva` los lista igual; el alumno puede elegir uno de esos bloques y confirmar, y sólo ahí recibe el `400` de `MENSAJE_AGENDAR_FUERA_DE_VENTANA` — el error se muestra correctamente, pero el bloque nunca debió ofrecerse como opción.

Relacionado: `Disponibilidad.resincronizar_sesiones_futuras()` (deuda 0005, resuelta) usa el mismo criterio de `sesiones_futuras()`, que tampoco excluye sesiones a menos de 2 horas — un asesor puede corregir su bloque y notificar a un alumno cuya sesión arranca en 20 minutos, y ese alumno ya no puede cancelar (`Asesoria.cancelar()` respeta la misma ventana). El correo aclara que fecha y hora no cambian, así que el impacto es bajo, pero la causa raíz es la misma: nada en el flujo del alumno anticipa la ventana de 2 horas.

## Por qué era razonable

[ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md) ya declaró esto explícitamente fuera de alcance en su sección Consequences ("idealmente, dejar de ofrecer los botones... la UI queda fuera del alcance de este ADR"); el backend rechaza correctamente cualquier intento fuera de la ventana pase lo que pase en el frontend, así que no hay riesgo de integridad de datos, solo una fricción de UX.

## Señal de revisión

Alumnos reportan confusión o quejas por ver un horario "disponible" que resulta rechazado al confirmar, o el volumen de 400s de `MENSAJE_AGENDAR_FUERA_DE_VENTANA` en producción es alto.
