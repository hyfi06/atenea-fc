# 0006 — Sin paginación en los endpoints de listado

**Estado:** Activa
**Origen:** [ADR 0017](../decisions/0017-asesorias-academicas-api.md)

## Qué se simplificó

Los endpoints DRF de Fase 2 (catálogo, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) no configuran paginación — devuelven la lista completa. No hay convención de paginación establecida todavía en el proyecto (`REST_FRAMEWORK` en `config/settings/base.py` no la define).

## Por qué era razonable

El volumen esperado por usuario (asesorías de un alumno o un asesor, materias de un área) es pequeño; introducir paginación antes de tener un segundo endpoint que la necesite es prematuro, y la convención debería decidirse una vez, a nivel de proyecto, no ad-hoc por app.

## Señal de revisión

El primer endpoint cuyo listado crezca sin límite natural (ej. historial de sesiones de un asesor con años de antigüedad) es la señal para decidir la convención de paginación del proyecto — no debería resolverse solo para ese endpoint.
