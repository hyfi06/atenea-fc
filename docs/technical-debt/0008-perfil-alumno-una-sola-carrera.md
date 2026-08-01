# 0008 — `PerfilAlumno` solo registra una carrera vigente

**Estado:** Activa
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

`PerfilAlumno.carrera` es un `ForeignKey` simple a una única `Carrera`, no un historial. No existe ningún modelo `HistoriaAcademica` que registre las carreras en las que un alumno ha estado inscrito a lo largo del tiempo — algo que la spec original de Asesorías Académicas ya dejaba explícitamente para el futuro.

## Por qué era razonable

Para el MVP, un alumno cursando activamente solo necesita su carrera actual para que `Asesoria` pueda registrarla al agendar una sesión. No hay caso de uso todavía de un alumno con doble carrera simultánea ni de cambio de carrera a mitad de semestre — modelar el historial completo ahora sería resolver un problema que no se ha presentado.

Esta simplificación no compromete el historial de `Asesoria`: `Asesoria.carrera` es un snapshot independiente tomado al momento de agendar (mismo patrón que `formato`/`ubicacion`/`liga_virtual`, ver deuda técnica 0005), así que una sesión pasada conserva la carrera correcta aunque `PerfilAlumno.carrera` cambie después.

## Señal de revisión

Si aparece un alumno con más de una carrera simultánea, o si la SAE necesita dar de baja/actualizar la carrera de un alumno que cambió de carrera formalmente, revisar si sigue bastando con sobreescribir `PerfilAlumno.carrera` o si hace falta el `HistoriaAcademica` completo (múltiples carreras, fechas de inicio/fin).
