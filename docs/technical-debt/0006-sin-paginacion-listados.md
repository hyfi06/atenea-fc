# 0006 — Sin paginación en los endpoints de listado

**Estado:** Activa
**Origen:** [ADR 0017](../decisions/0017-asesorias-academicas-api.md)

## Qué se simplificó

Los endpoints DRF de Fase 2 (catálogo, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) no configuran paginación — devuelven la lista completa. No hay convención de paginación establecida todavía en el proyecto (`REST_FRAMEWORK` en `config/settings/base.py` no la define).

## Por qué era razonable

El volumen esperado por usuario (asesorías de un alumno o un asesor, materias de un área) es pequeño; introducir paginación antes de tener un segundo endpoint que la necesite es prematuro, y la convención debería decidirse una vez, a nivel de proyecto, no ad-hoc por app.

## Señal de revisión

El primer endpoint cuyo listado crezca sin límite natural (ej. historial de sesiones de un asesor con años de antigüedad) es la señal para decidir la convención de paginación del proyecto — no debería resolverse solo para ese endpoint.

## Cobertura parcial (2026-08-04)

`GET /api/asesorias/asesorias/?semestre=<clave>` filtra el historial por semestre (`disponibilidad__registro__semestre`), acompañado de `GET /api/asesorias/asesorias/semestres/` para construir los subtabs. Eso acota el listado que más riesgo tenía de crecer sin límite natural (el historial de un asesor con años de antigüedad — el ejemplo exacto que menciona la señal de revisión de arriba) al caso de uso más común: ver un semestre a la vez.

**Esto no resuelve este ítem.** Sigue sin haber convención de paginación de proyecto (`REST_FRAMEWORK` en `config/settings/base.py` no la define), el resto de los listados sigue devolviendo la colección completa, y un solo semestre con volumen suficiente vuelve a exhibir el problema. La señal de revisión sigue vigente tal cual.

## Cobertura parcial (2026-08-19)

`GET /api/materias/materias/` quedó paginado (`PageNumberPagination`, 50 por página) y con búsqueda por texto en el backend (`SearchFilter` sobre `nombre`/`clave`), con scroll infinito en `DialogoAgregarMateria` — ver [ADR 0031](../decisions/0031-paginacion-busqueda-catalogo-materias.md). Es el listado con volumen real del proyecto (400+ registros) y el único que se navega como lista.

**Esto no resuelve este ítem.** La paginación es `pagination_class` propia de `MateriaViewSet`: `REST_FRAMEWORK` en `config/settings/base.py` sigue **sin** `DEFAULT_PAGINATION_CLASS`, y `RegistroAsesor`, `Disponibilidad`, `Asesoria` y `carreras` siguen devolviendo la colección completa. La señal de revisión sigue vigente tal cual: falta la convención de proyecto, decidida una vez y no ad-hoc por app.

Además, la forma en que se preservó el contrato del caso lookup (`useMaterias()` recorre todas las páginas) abrió la deuda [0027](0027-useMaterias-recorre-todas-las-paginas.md).
