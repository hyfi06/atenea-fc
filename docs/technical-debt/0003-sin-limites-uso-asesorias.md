# 0003 — Sin límites de uso en Asesorías

**Estado:** Parcialmente resuelta — 2026-08-19 ([ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md))
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

Un alumno puede agendar cualquier número de sesiones simultáneas y cancelar sin restricción de tiempo mínimo antes de la sesión ni límite de cancelaciones.

## Por qué era razonable

El MVP prioriza validar el flujo completo con usuarios reales antes de diseñar límites que podrían no corresponder al patrón de abuso real (si lo hay).

## Señal de revisión

Evidencia de abuso en producción (acaparamiento de horarios, cancelaciones sistemáticas de último minuto que dejan al asesor sin aviso).

## Cómo se resolvió (parcialmente)

La **restricción de tiempo mínimo** existe desde el 2026-08-19: ni agendar ni cancelar se permiten a menos de 2 horas del inicio de la sesión (`VENTANA_MINIMA_ANTICIPACION` en `asesorias/models.py`, validada en `Asesoria.clean()` y `Asesoria.cancelar()`). `Disponibilidad.desactivar()` se salta la ventana a propósito vía `cancelar(forzar=True)`: la baja de un horario por parte del asesor no es una cancelación de último minuto del alumno.

## Qué sigue pendiente

- **Límite de sesiones simultáneas por alumno** — sigue sin existir; un alumno puede acaparar todos los horarios de la ventana agendable.
- **Límite de cancelaciones** — sigue sin existir; un alumno puede cancelar y reagendar indefinidamente mientras respete la ventana de 2 horas.

Ambos siguen esperando la misma señal de revisión de arriba: evidencia de abuso real en producción.
