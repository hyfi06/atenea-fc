# 0002 — Alta de `PerfilAsesorAcademico` solo por admin

**Estado:** Activa
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md), [ADR 0017](../decisions/0017-asesorias-academicas-api.md)

## Qué se simplificó

No existe endpoint ni flujo self-service para que un académico se registre como asesor — lo da de alta la SAE manualmente vía Django admin. El área queda fija tras la creación, sin flujo de edición propio.

## Por qué era razonable

El volumen esperado de asesores es bajo (altas ocasionales, gestionadas por la SAE), y automatizarlo antes de validar el flujo con usuarios reales es prematuro.

## Señal de revisión

Si el volumen de altas crece lo suficiente para volverse un cuello de botella operativo para la SAE, o si academia pide autoservicio.
