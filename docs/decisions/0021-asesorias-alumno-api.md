# 0021 — Asesorías Académicas: API del lado alumno

**Status:** Accepted
**Date:** 2026-08-08

## Context

La [ADR 0017](0017-asesorias-academicas-api.md) expuso el flujo del asesor completo y un flujo de alumno mínimo: búsqueda de disponibilidad **anónima** (`GET /api/asesorias/disponibilidad/buscar/`) y agendado (`POST /api/asesorias/asesorias/`). El frontend del alumno ([ADR 0022](0022-asesorias-vista-unificada-frontend.md)) requiere un flujo **centrado en asesor** — elegir materia → elegir asesor → ver sus días en la ventana de dos semanas → elegir bloque → elegir carrera → agendar — que la API actual no soporta. Al diseñarlo aparecieron tres huecos y un leak de seguridad. Diseño completo en [`docs/superpowers/specs/2026-08-08-asesorias-alumno-api-design.md`](../superpowers/specs/2026-08-08-asesorias-alumno-api-design.md).

Estado actual: `BuscarDisponibilidadView` (`asesorias/views.py:96`) devuelve slots sin identidad de asesor; `AsesoriaSerializer` (`asesorias/serializers.py:88`) incluye `notas` y el `list`/`retrieve` del viewset sólo exige `IsAuthenticated`, por lo que **el alumno recibe hoy las notas del asesor**; y `carrera` está fija en `read_only_fields`, tomada siempre de `alumno.carrera`.

## Decision

- **Endpoint de oferta** `GET /api/asesorias/oferta/?carrera=&buscar=` (`APIView`, `EsAlumno`): materias con ≥1 asesor con `Disponibilidad.activa`, no las materias por flag `habilitada_asesorias`. Cierra la diferencia entre "materia habilitada" y "materia con asesores realmente disponibles".
- **Endpoint de asesores por materia** `GET /api/asesorias/oferta/{materia_id}/asesores/` (`APIView`, `EsAlumno`): `[{registro_id, asesor_nombre, area_nombre, formatos}]`. El nombre del asesor deja de aparecer sólo después de agendar.
- **Disponibilidad por asesor**: se extiende la `APIView` de búsqueda existente con `?asesor=<registro_id>` y se añaden `registro_id`/`asesor_nombre` al resultado, en vez de crear un endpoint nuevo — es la misma transformación (proyectar la recurrencia semanal sobre la ventana, excluir ocupados) con un filtro más.
- **Carrera elegible al agendar**: `carrera` pasa a escribible en `AsesoriaSerializer`, validada contra las carreras del alumno. Hoy el conjunto es `{alumno.carrera}` (una sola, [deuda 0008](../technical-debt/0008-perfil-alumno-una-sola-carrera.md)); el contrato queda listo para múltiples carreras sin otro cambio de API. Se conserva el snapshot de `carrera` al agendar.
- **Ocultar `notas` al alumno**: `AsesoriaSerializer` omite `notas` cuando el solicitante no es el asesor dueño de la sesión (condición sobre `context["request"].user`), sin duplicar serializers. Es una **corrección de seguridad**, no deuda diferida.
- **Sin nuevos modelos ni migraciones**: todo se resuelve en views/serializers; se reutilizan `EsAlumno`, `ventana_agendable()` y el `AsesoriaViewSet` compartido.

## Consequences

- La oferta refleja disponibilidad real, no configuración: una materia habilitada sin asesores con horarios no aparece, evitando callejones sin salida en el flujo de agendado.
- El alumno ya no recibe las notas privadas del asesor — se cierra un leak que ADR 0017 no había especificado. El dato sigue disponible para el asesor y para una futura vista de admin.
- La escritura de `carrera` introduce un punto de validación nuevo (`400` si es ajena); el frontend autoselecciona la única carrera actual, así que el cambio es invisible hasta que exista `HistoriaAcademica`.
- Dos endpoints `APIView` más siguen el precedente de la búsqueda de disponibilidad (transformaciones fuera del shape CRUD), manteniendo el viewset de `Asesoria` como única superficie de escritura.
- Deuda referenciada, no duplicada: carrera múltiple → [0008](../technical-debt/0008-perfil-alumno-una-sola-carrera.md); paginación de `/oferta/` → [0006](../technical-debt/0006-sin-paginacion-listados.md); calendario → [0001](../technical-debt/0001-sin-modelo-calendario-academico.md).

## Alternatives considered

- **Reusar `/materias/?habilitada_asesorias=true` como oferta**: descartado — filtra por flag, no por disponibilidad real; obligaría al frontend a una segunda pasada por asesor para descartar materias vacías.
- **Serializer de alumno separado para ocultar `notas`**: duplicaría el shape del recurso; se prefiere omitir el campo condicionalmente en el serializer compartido, coherente con el `AsesoriaViewSet` único de ADR 0017.
- **Endpoint nuevo de disponibilidad-por-asesor** en vez de extender la búsqueda: agregaría una vista casi idéntica; un query param evita la duplicación.
- **Devolver los asesores dentro de `/oferta/`** (anidados por materia): infla la respuesta de la lista y acopla dos pasos de navegación distintos; se separan en dos llamadas alineadas con las dos pantallas (lista → detalle).

## Changelog

- (sin enmiendas)
