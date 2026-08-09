# 0013 — Agendar no valida que la materia pertenezca al registro del asesor

**Estado:** Activa
**Origen:** [spec `2026-08-08-asesorias-alumno-api-design`](../decisions/0021-asesorias-alumno-api.md) / [ADR 0021](../decisions/0021-asesorias-alumno-api.md)

## Qué se simplificó

Al agendar una asesoría (`AsesoriaSerializer.validate` / `Asesoria.clean`) se valida el día y la ventana agendable, pero NO que la `materia` enviada pertenezca a `disponibilidad.registro.materias`. Un cliente puede POSTear el slot del asesor X declarando una materia Y que ese asesor no imparte, y la sesión se crea igual.

## Por qué era razonable

El flujo de UI encadena materia → asesor → slot pasando IDs coherentes entre pasos, así que en uso normal la materia siempre pertenece al registro del asesor elegido y la incoherencia no ocurre. Además es una laguna pre-existente, no introducida por esta entrega del lado alumno.

## Señal de revisión

Si se detecta una asesoría agendada con una materia incoherente con el registro del asesor, o antes de exponer la API a clientes no confiables (fuera del SPA propio), añadir la validación en `AsesoriaSerializer.validate`: rechazar cuando `materia` no esté en `disponibilidad.registro.materias`.
