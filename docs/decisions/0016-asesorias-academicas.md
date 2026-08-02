# 0016 — Asesorías Académicas: perfiles, disponibilidad en slots de 30 min, sin DRF en esta pasada

**Status:** Accepted
**Date:** 2026-07-30

## Context

Asesorías Académicas (independiente del PIT / Programa Institucional de Tutorías) es el primer servicio funcional de producción de Atenea, construido sobre el catálogo académico (ADR 0015). El alcance de negocio ya fue validado con el usuario en una sesión previa: un académico se registra como asesor con un área fija y, cada semestre, elige un subconjunto de materias y su disponibilidad horaria; un alumno agenda una sesión con un asesor filtrando por carrera/materia/horario, puede cancelarla (nunca borrarla); el asesor marca asistencia y solo entonces puede agregar notas; hay notificaciones por email.

Diseño detallado, modelo de datos completo y preguntas resueltas en [`docs/superpowers/specs/2026-07-30-asesorias-academicas-design.md`](../superpowers/specs/2026-07-30-asesorias-academicas-design.md).

Al diseñar el modelo de datos se encontró que `PerfilAlumno` y `PerfilAcademico` — el patrón de identidad que documenta la [ADR 0012](0012-perfiles-identidad-roles.md) — no existen todavía en el código, solo `accounts.User`. `PerfilAsesorAcademico` requiere `PerfilAcademico` por el mismo patrón que `PerfilTutor`/`PerfilRevisor`, y `Asesoria.alumno` debe apuntar a `PerfilAlumno`, así que esta decisión también cubre crear esos dos perfiles base.

## Decision

- **Fase 0, en `backend/accounts/`**: se crean `PerfilAlumno` (`numero_cuenta`, único) y `PerfilAcademico` (`numero_trabajador`, único) como `OneToOneField` a `User`, siguiendo exactamente el patrón de la ADR 0012, sin campos de carreras/M2M (eso pertenece a un futuro `HistoriaAcademica`).
- **App de dominio nueva `backend/asesorias/`**, siguiendo el layout de la [ADR 0011](0011-backend-project-layout.md), con cuatro modelos:
  - `PerfilAsesorAcademico`: `OneToOneField` a `User` + `area` (FK fija a `carreras.Area`) + `activo`; `clean()` exige que el `user` tenga `PerfilAcademico`.
  - `RegistroAsesor`: registro anual/semestral del asesor — FK a `PerfilAsesorAcademico`, `semestre` (mismo formato `AAAAN` que `OfertaMateria`), M2M a `Materia` con método `agregar_materia()` que valida área + `habilitada_asesorias` + oferta del semestre. `unique_together(asesor, semestre)`.
  - `Disponibilidad`: **slots discretos de 30 minutos**, no rangos con duración configurable — el asesor selecciona uno o más bloques (`dia_semana`, `hora_inicio` en la rejilla de 30 min), no necesariamente contiguos, cada uno con su propio `formato` (presencial/virtual) y `ubicacion`/`liga_virtual`.
  - `Asesoria`: la sesión agendada — FK a `PerfilAlumno`, `Disponibilidad`, `Materia` (obligatoria); `fecha` concreta; snapshot de `hora_inicio`/`formato`/`ubicacion`/`liga_virtual` copiado al agendar (no leído en vivo de `Disponibilidad`); `estado` (agendada/cancelada/realizada, nunca se borra); `asistio` tri-estado: `notas` solo se puede guardar si `asistio is True`.
- **Anti-doble-booking a nivel de base de datos**: `UniqueConstraint` condicional de Postgres sobre `(disponibilidad, fecha)` excluyendo `estado="cancelada"` — una condición de carrera entre dos alumnos agendando el mismo bloque falla con `IntegrityError` en el segundo `INSERT`. No se usa `ExclusionConstraint` de rangos porque los bloques son de tamaño fijo (30 min), no rangos arbitrarios.
- **`on_delete=PROTECT`** en toda relación que forma parte del historial (`RegistroAsesor.asesor`, `Disponibilidad` vía `Asesoria`, `Asesoria.materia`, `Asesoria.alumno`), igual que en el catálogo — nada se pierde por borrar un registro relacionado.
- **Sin capa DRF en esta pasada**: solo modelos, admin y lógica de negocio en Python (`agregar_materia`, `marcar_asistencia`, `guardar_notas`, `cancelar` como métodos del modelo, no en vistas), replicando el precedente del catálogo académico. Serializers/viewsets/urls/permission classes quedan para un plan de Fase 2 separado, con su propia spec.
- **Notificaciones por email** vía tareas Celery async (`asesorias/tasks.py`), enganchadas a los métodos de servicio (creación de `Asesoria`, `cancelar()`) — sin tarea periódica (Celery beat) de recordatorio en esta pasada.

## Consequences

- Los métodos de servicio viven en el modelo, no en la futura vista — cuando se construya la Fase 2 (DRF), los serializers/viewsets son delgados y no reimplementan validación, reduciendo el riesgo de que la lógica de negocio diverja entre el admin y la API.
- El anti-doble-booking depende de que los bloques de disponibilidad sean siempre de 30 minutos fijos; si en el futuro se necesitan sesiones de duración variable, el constraint `(disponibilidad, fecha)` deja de ser suficiente y hay que migrar a un mecanismo de traslape de rangos (`ExclusionConstraint` + `btree_gist`).
- Editar una `Disponibilidad` (formato, ubicación, liga) no afecta sesiones ya agendadas sobre ella, porque `Asesoria` guarda su propio snapshot — esto es deliberado, pero significa que corregir un dato erróneo de disponibilidad (ej. una liga de Zoom mal escrita) no se propaga automáticamente a sesiones ya creadas; requiere corrección manual por sesión.
- Sin modelo de calendario/periodo con fechas reales de inicio/fin de semestre, sin límite de sesiones simultáneas por alumno, sin ventana mínima de cancelación, y sin cierre automático de sesiones `agendada` cuya fecha ya pasó — todo esto queda como deuda de producto documentada en la spec, a resolver si se vuelve un problema real en uso.
- `PerfilAsesorAcademico.area` se trata como fija tras su creación, sin flujo de edición propio; una corrección requeriría intervención directa vía admin.

## Alternatives considered

- **Disponibilidad como rango con duración configurable** (`hora_inicio`/`hora_fin` + `duracion_sesion_minutos`, slots calculados al vuelo): más flexible, pero el usuario confirmó explícitamente que la disponibilidad se define seleccionando bloques discretos de 30 minutos (no necesariamente contiguos) — el modelo de rango añadiría complejidad de cálculo de slots sin necesidad real hoy.
- **`ExclusionConstraint` de Postgres para el anti-doble-booking**: resuelve el caso general de traslape de rangos arbitrarios, pero requiere la extensión `btree_gist` y es más difícil de razonar; innecesario cuando todos los bloques son de tamaño fijo — un `UniqueConstraint` simple sobre `(disponibilidad, fecha)` da la misma garantía con menos mecanismo.
- **Incluir la capa DRF en este mismo plan**: se consideró para no tener que "abrir" la app dos veces, pero se descartó por el mismo argumento que ya validó el catálogo — mezclar el diseño del modelo de datos con el diseño de la superficie de API (shape de búsqueda de horarios, permission classes por perfil, manejo de condiciones de carrera en HTTP) en un solo plan lo vuelve más difícil de revisar; se prefiere una Fase 2 con su propia spec.
- **Materia opcional en `Asesoria`** (sesiones "generales" sin materia): descartada — el usuario confirmó que la materia es obligatoria, consistente con que el asesor se registra por materia y el alumno busca por materia.

## Changelog

- **2026-08-01** — `PerfilAlumno` gana `carrera` (FK a `carreras.Carrera`) y `generacion` (año de ingreso, `YYYY`), revirtiendo la decisión de Fase 0 de no incluir campos de carrera. Motivo: `Asesoria` necesita poder registrar la carrera del alumno al agendar, igual que ya snapshotea `formato`/`ubicacion`/`liga_virtual` (`Asesoria.carrera`, FK a `carreras.Carrera`, poblada desde `alumno.carrera` en `AsesoriaSerializer.validate()`). Se optó por un campo simple en `PerfilAlumno` en vez del `HistoriaAcademica` que esta ADR dejaba para el futuro — ver [deuda técnica 0008](../technical-debt/0008-perfil-alumno-una-sola-carrera.md).
- **2026-08-02** — Se amplía la regla de negocio de cancelación: además del alumno, el asesor académico dueño de la sesión también puede cancelarla (antes esta ADR y la ADR 0017 solo contemplaban "el alumno... puede cancelarla"). Detalle de implementación (nueva permission class `EsAlumnoOAsesorAcademico`, gate de vista) en el [Changelog de la ADR 0017](0017-asesorias-academicas-api.md#changelog).
