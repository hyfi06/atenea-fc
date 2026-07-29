# 0015 — Catálogo académico como apps `carreras` y `materias`

**Status:** Accepted
**Date:** 2026-07-29

## Context

El primer servicio funcional de producción de Atenea, Asesorías Académicas (spec y ADR aparte, construidos sobre esta decisión), necesita un catálogo de carreras, áreas y materias de la Facultad de Ciencias: un académico se registra con un área fija y elige materias; un alumno agenda eligiendo su carrera; las materias se ofrecen o no cada semestre y ese histórico debe conservarse para este y futuros servicios (ej. movilidad entrante).

Diseño detallado, alternativas de estructura de app y de almacenamiento de alias evaluadas, y ejemplos completos de modelo en [`docs/superpowers/specs/2026-07-29-catalogo-academico-design.md`](../superpowers/specs/2026-07-29-catalogo-academico-design.md).

## Decision

- **Dos apps de dominio**: `backend/carreras/` (`Area`, `Carrera`) y `backend/materias/` (`Materia`, `OfertaMateria`), siguiendo el patrón de layout de la [ADR 0011](0011-backend-project-layout.md).
- `Carrera.clave` (la clave oficial de carrera, ej. 101 para Actuaría, tomada del sistema legado en Google Apps Script) es un campo de negocio requerido y único, distinto de la PK autogenerada — junto con `siass_id`/`siassypp_id`/`dgeci_id` (también únicos, nullable) permite interconectar con esos sistemas externos.
- `Carrera.alias` es `ArrayField(CharField)` de Postgres, no un modelo relacional aparte — son pocas variantes fijas por carrera, usadas solo para matching de imports.
- `Materia.clave` es la llave natural: única globalmente, no compuesta con `carrera` ni `plan`. `Materia.carrera` es FK simple (nunca M2M) aunque en la práctica una materia se comparta entre carreras — la Facultad la responsabiliza administrativamente a una sola.
- `OfertaMateria` historiza la oferta por semestre con `unique_together(materia, semestre)` y carga idempotente (`update_or_create`); nunca se borran ni sobrescriben filas de semestres ya cerrados.
- `Materia.habilitada_asesorias` es el único flag de servicio agregado en esta pasada; flags de futuros servicios se agregan como campos propios cuando ese servicio exista.
- Carga de datos: `Area`/`Carrera` vía data migration (datos casi estáticos, sembrados desde el catálogo de `models.gs`); `Materia`/`OfertaMateria` vía management commands que leen CSV con upsert por clave natural. Los 4 modelos se registran en Django admin para correcciones puntuales.

## Consequences

- Agregar un servicio futuro que consuma el catálogo (ej. movilidad entrante) solo requiere agregar su propio campo booleano en `Materia` y su propia app de servicio — el catálogo no se toca salvo por ese campo.
- `Materia.carrera` como FK simple es una simplificación deliberada de la realidad académica (una materia puede impartirse en planes de varias carreras/áreas); si algún consumidor futuro necesita el conjunto real de carreras que ven una materia, esta decisión se revisita.
- Los IDs externos (`siass_id`, `siassypp_id`, `dgeci_id`) dependen de que esos sistemas sigan usando identificadores estables; no hay mecanismo de reconciliación automática si cambian en su sistema de origen.
- Corregir un semestre de `OfertaMateria` ya cerrado es una operación manual vía admin, no vía el comando de carga masiva — deliberado para no complicar el comando con lógica de reapertura que no se ha necesitado aún.

## Alternatives considered

- **Una sola app `catalogo`** con los 4 modelos juntos: más simple de entrada, pero mezcla el ciclo de vida casi estático de `Area`/`Carrera` con el de `Materia`/`OfertaMateria`, que se recarga cada semestre y crecerá mucho más. Se prefirió separar en `carreras` y `materias`.
- **`CarreraAlias` como modelo relacional** en vez de `ArrayField`: más consultable/indexable individualmente, pero agrega una tabla y JOINs para un catálogo de ~20 valores fijos en total — sin beneficio real hoy.
- **Llave natural de `Materia` compuesta `(Carrera, Clave, Plan)`**: propuesta inicial, descartada porque en la práctica `Clave` ya es única por materia en todo el catálogo de la Facultad, sin necesidad de calificarla por carrera o plan.
- **Sistema genérico de flags de servicio en `Materia`** (tabla de flags dinámica en vez de un campo booleano por servicio): rechazado por YAGNI — hoy solo existe un consumidor (`habilitada_asesorias`); se revisita si el número de servicios que consumen el catálogo crece lo suficiente para justificar la indirección.
