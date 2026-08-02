# 0017 — Asesorías Académicas: capa DRF (Fase 2)

**Status:** Accepted
**Date:** 2026-07-30

## Context

La [ADR 0016](0016-asesorias-academicas.md) implementó el dominio de Asesorías Académicas (perfiles, `PerfilAsesorAcademico`, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) deliberadamente sin capa DRF, reservando serializers/viewsets/urls/permission classes para "un plan de Fase 2 separado, con su propia spec" — para no mezclar el diseño del modelo de datos con el diseño de la superficie de API en una sola revisión.

Esta ADR cubre esa Fase 2: la superficie HTTP que consume el frontend para los flujos de alumno (buscar disponibilidad, agendar, cancelar) y asesor (registrar materias, publicar disponibilidad, marcar asistencia, guardar notas). Diseño completo en [`docs/superpowers/specs/2026-07-30-asesorias-academicas-api-design.md`](../superpowers/specs/2026-07-30-asesorias-academicas-api-design.md).

Dos huecos adicionales aparecieron al diseñar el flujo de búsqueda del alumno: `carreras`/`materias` tampoco tienen capa DRF (el filtro de búsqueda del frontend la necesita), y no existe ningún modelo de calendario/periodo que defina qué fechas son agendables.

## Decision

- **Se agrega DRF read-only a `carreras`/`materias`** en la misma pasada — el flujo del alumno no es usable sin poder listar/filtrar el catálogo, y separarlo en otro plan solo movería la dependencia sin eliminarla.
- **`ModelViewSet` + `@action`** para los recursos que el asesor administra directamente (`RegistroAsesor`, `Disponibilidad`) y para las transiciones de ciclo de vida de `Asesoria` (`cancelar`, `marcar_asistencia`, `notas` como actions) — siguiendo el patrón viewsets/serializers ya establecido por la [ADR 0002](0002-drf-for-api.md). Las vistas/serializers son delgados: invocan los métodos de modelo ya escritos en la Fase 1 (`agregar_materia`, `marcar_asistencia`, `guardar_notas`, `cancelar`) y traducen `ValidationError`/`IntegrityError` a códigos HTTP, sin reimplementar ninguna regla de negocio.
- **`AsesoriaViewSet` único, compartido entre alumno y asesor** — `get_queryset()`/`get_permissions()` ramifican según el perfil del usuario autenticado (`hasattr(user, "perfil_alumno")` vs `"perfil_asesor_academico"`), en vez de dos viewsets separados que duplicarían el shape del recurso.
- **Búsqueda de disponibilidad como `APIView` dedicada** (`GET /api/asesorias/disponibilidad/buscar/`), no un `ReadOnlyModelViewSet` de `Disponibilidad` — el resultado son instancias concretas `(fecha, disponibilidad)` dentro de una ventana agendable, ya excluyendo bloques ocupados, una transformación fuera del shape CRUD estándar.
- **Ventana de fechas agendable: semana en curso + la siguiente**, fija en código (`asesorias.servicios.ventana_agendable()`), no derivada de un modelo de calendario académico (que no existe). Se aplica en dos lugares: al construir los resultados de búsqueda, y como extensión a `Asesoria.clean()` — así queda protegida sin importar el punto de entrada (API, admin, shell), preservando el principio de la ADR 0016 de que la lógica de negocio vive en el modelo, no en la vista.
- **Condición de carrera del anti-doble-booking → `409 Conflict`**: la vista de creación de `Asesoria` captura el `IntegrityError` del `UniqueConstraint` condicional ya existente desde la Fase 1 y responde `409` explícito en vez de dejarlo propagar como `500`.
- **Alta de `PerfilAsesorAcademico` sigue siendo solo por Django admin** — sin endpoint de auto-registro en esta fase; consistente con que el área queda fija tras la creación (ADR 0016).
- **Sin paginación** en los endpoints de listado — el proyecto no tiene todavía una convención de paginación establecida (`REST_FRAMEWORK` en `config/settings/base.py` no la define) y el volumen esperado por usuario es pequeño.

## Consequences

- Los serializers/viewsets de esta fase quedan delgados porque toda la validación de negocio ya vivía en el modelo desde la Fase 1 — confirma la apuesta de diseño de la ADR 0016.
- Un segundo servicio de la SAE que también necesite exponer catálogo vía API puede reutilizar el mismo `ReadOnlyModelViewSet` de `carreras`/`materias` en vez de reimplementarlo.
- La ventana agendable fija en código (no en un modelo de calendario) es deuda técnica documentada: si un segundo flujo necesita fechas de semestre reales, hay que introducir un modelo `PeriodoAcademico` y esta regla deja de ser código, pasa a ser dato.
- Sin paginación ([deuda 0006](../technical-debt/0006-sin-paginacion-listados.md)), alta de asesor solo por admin ([deuda 0002](../technical-debt/0002-alta-perfil-asesor-solo-admin.md)), y los límites de uso/cierre automático/recordatorios ya diferidos por la ADR 0016 ([deuda 0003](../technical-debt/0003-sin-limites-uso-asesorias.md), [deuda 0004](../technical-debt/0004-sin-cierre-automatico-recordatorios.md)) quedan todos registrados como ítems de deuda técnica buscables (ver [`docs/technical-debt/`](../technical-debt/README.md)), en vez de dispersos entre ADRs.
- El `409` explícito en la creación de `Asesoria` significa que el frontend debe manejar ese código específicamente (reintentar la búsqueda de disponibilidad, no reintentar el mismo POST ciegamente) — es un contrato de API nuevo que no existía en ningún otro endpoint del proyecto todavía.

## Alternatives considered

- **Dos `ModelViewSet` separados para `Asesoria`** (uno para alumno, otro para asesor): más simple de razonar permiso por permiso, pero duplica el serializer y el shape del recurso; se prefirió un viewset compartido con ramificación por rol, ya usado implícitamente en el patrón de perfiles de la ADR 0012 (un mismo `User` puede tener distintos perfiles/roles).
- **Modelar `PeriodoAcademico` ahora** para que la ventana agendable derive de fechas reales de semestre: más correcto a largo plazo, pero specular sobre un requisito (fechas exactas de inicio/fin de semestre, periodo de exámenes, etc.) que nadie ha confirmado todavía — se prefiere una regla simple en código, documentada como deuda técnica explícita, sobre modelar algo que podría no coincidir con el requisito real cuando aparezca.
- **`ReadOnlyModelViewSet` de `Disponibilidad` con un `@action` de búsqueda** en vez de una `APIView` dedicada: se descartó porque el resultado de la búsqueda no son instancias de `Disponibilidad` — son fechas concretas derivadas de expandir la recurrencia semanal dentro de la ventana agendable, ya sin los slots ocupados; forzar ese resultado en el serializer de `Disponibilidad` habría sido más confuso que una vista dedicada.
- **Alta de `PerfilAsesorAcademico` vía API en esta fase**: se consideró para completar el flujo de principio a fin, pero el volumen esperado de altas es bajo y gestionado por la SAE, así que automatizarlo antes de validar el flujo con usuarios reales es prematuro — queda como deuda técnica explícita, no como decisión permanente.

## Changelog

- **2026-08-02:** El permiso de `cancelar` se amplía de EsAlumno-únicamente a EsAlumno-o-EsAsesorAcademico (nueva clase `EsAlumnoOAsesorAcademico`) — el asesor también puede cancelar una sesión propia, no solo el alumno. `EsDuenoDeLaAsesoria` ya soportaba ambos roles en el chequeo de dueño; solo cambió el gate de clase. Motivado por el flujo de asesor construido en el frontend (docs/superpowers/plans/2026-08-01-asesorias-frontend-asesor.md).
