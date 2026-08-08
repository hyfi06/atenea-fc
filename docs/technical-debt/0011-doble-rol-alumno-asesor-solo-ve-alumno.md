# 0011 — Un usuario con doble rol (alumno y asesor) solo ve el lado de alumno

**Estado:** Resuelta — 2026-08-08 (commits del [plan 2026-08-08-doble-rol-asesorias](../superpowers/plans/2026-08-08-doble-rol-asesorias.md))
**Origen:** [ADR 0017](../decisions/0017-asesorias-academicas-api.md); detectada en la revisión final de rama del [plan de backend 2026-08-04](../superpowers/plans/2026-08-04-login-oauth-backend.md)

## Qué se simplificó

`AsesoriaViewSet.get_queryset` (`backend/asesorias/views.py`) y la permission
class `EsDuenoDeLaAsesoria` (`backend/asesorias/permissions.py`) resuelven el rol
del usuario con una cadena `if perfil_alumno … elif/else perfil_asesor_academico`,
**alumno primero**. Como `PerfilAlumno` y `PerfilAsesorAcademico` son ambos
`OneToOneField` a `User` y nada impide que un mismo `User` tenga los dos, un
usuario con doble rol queda atrapado en la rama de alumno:

- **Listado** (`GET /api/asesorias/asesorias/`): solo ve las sesiones donde es
  **alumno** (`base.filter(alumno=user.perfil_alumno)`); la rama de asesor es un
  `elif` que nunca se alcanza, así que sus sesiones **como asesor** son invisibles.
- **Acciones de dueño** (`cancelar`, `marcar_asistencia`, `notas`):
  `EsDuenoDeLaAsesoria.has_object_permission` comprueba primero
  `obj.alumno_id == user.perfil_alumno.id` y hace `return` de inmediato — si el
  usuario es el **asesor** de esa sesión pero no su alumno, devuelve `False` →
  `403`, sin llegar a evaluar la rama de asesor.

En resumen: un asesor que además es alumno no puede ver ni gestionar sus propias
asesorías **como asesor**.

Nota de contexto: la Task 3 del plan de backend documentó `roles` como una
**lista** (`UserDetailsSerializer.get_roles` agrega todos los perfiles que
existan), de modo que el contrato de la API ya le promete multi-rol al frontend
([ver `docs/development/api-frontend.md`](../development/api-frontend.md)), pero el
filtrado de asesorías sigue asumiendo mono-rol. La contradicción es nueva y
alcanzable desde la UI.

## Por qué era razonable

En la Fase 1 los perfiles de alumno y de asesor son poblaciones disjuntas en la
práctica (a los asesores los da de alta la SAE, ver [deuda 0002](0002-alta-perfil-asesor-solo-admin.md)),
así que el caso de doble rol no ocurría con datos reales. La cadena `if/elif` es
más simple que decidir "¿en qué rol está actuando el usuario ahora mismo?" y no
había señal de que hiciera falta. El defecto es latente, no observable, mientras
nadie tenga los dos perfiles a la vez.

## Señal de revisión

El primer `User` con `perfil_alumno` y `perfil_asesor_academico` simultáneos
(p. ej. un estudiante de posgrado que asesora) es la señal: en cuanto exista, sus
asesorías como asesor desaparecen del listado y no puede gestionarlas. La otra
señal es el frontend empezando a consumir `roles` como lista de verdad (un switch
de "actuar como alumno / como asesor"): ese es el momento en que el backend tiene
que dejar de asumir un solo rol por usuario.

## Cómo se resolvió

Resuelta según el plan [`docs/superpowers/plans/2026-08-08-doble-rol-asesorias.md`](../superpowers/plans/2026-08-08-doble-rol-asesorias.md),
sin cambios de esquema:

- **Permiso** (`EsDuenoDeLaAsesoria.has_object_permission`): se sustituyó la cadena
  `if … return` por dos comprobaciones independientes combinadas con `or` —
  `es_alumno_dueno` (`hasattr(perfil_alumno) and obj.alumno_id == …`) **o**
  `es_asesor_dueno` (`hasattr(perfil_asesor_academico) and
  obj.disponibilidad.registro.asesor.user_id == user.id`). El usuario es dueño si
  es el alumno **o** el asesor de la sesión.
- **Listado** (`AsesoriaViewSet.get_queryset`): se sustituyó el `if/elif/else`
  alumno-primero por una unión con `Q` —
  `condiciones |= Q(alumno=…)` si tiene perfil de alumno,
  `condiciones |= Q(disponibilidad__registro__asesor__user=…)` si tiene perfil de
  asesor; sin perfiles, `Asesoria.objects.none()`. Un usuario con doble rol ve la
  unión de ambos lados, también en `/semestres/`.

Se preservaron intactos la rama de acciones que devuelve `base` sin filtrar por
dueño (para que el 403 del ADR 0017 lo dé `EsDuenoDeLaAsesoria`, no un 404), los
`select_related` (sin N+1) y el filtro `?semestre=` aplicado sobre la unión.
