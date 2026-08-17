# 0002 — Alta de `PerfilAsesorAcademico` solo por admin

**Estado:** Resuelta — 2026-08-15 ([ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md))
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md), [ADR 0017](../decisions/0017-asesorias-academicas-api.md)

## Qué se simplificó

No existe endpoint ni flujo self-service para que un académico se registre como asesor — lo da de alta la SAE manualmente vía Django admin. El área queda fija tras la creación, sin flujo de edición propio.

## Por qué era razonable

El volumen esperado de asesores es bajo (altas ocasionales, gestionadas por la SAE), y automatizarlo antes de validar el flujo con usuarios reales es prematuro.

## Señal de revisión

Si el volumen de altas crece lo suficiente para volverse un cuello de botella operativo para la SAE, o si academia pide autoservicio.

## Cómo se resolvió

`POST /api/asesorias/asesores/solicitud/` deja que un `PerfilAcademico` cree su propio `PerfilAsesorAcademico`. La SAE ya no lo crea: solo lo activa tras la validación de vigencia (ver [deuda 0018](0018-validacion-academico-activo-con-stub.md)).
