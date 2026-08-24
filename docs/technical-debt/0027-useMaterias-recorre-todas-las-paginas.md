# 0027 — `useMaterias()` recorre todas las páginas: N requests por carga del catálogo

**Estado:** Activa
**Origen:** [ADR 0031](../decisions/0031-paginacion-busqueda-catalogo-materias.md)

## Qué se simplificó

Al paginar `GET /api/materias/materias/` (50 por página), `useMaterias()` conservó su contrato de devolver `Materia[]` completo recorriendo todas las páginas dentro de `obtenerTodasLasMaterias()` (`frontend/src/features/catalogo/api.ts`): pide `?page=1`, `?page=2`, … hasta que `next` es `null`, en serie. Con 400+ materias son 8 requests secuenciales en vez de 1.

## Por qué era razonable

Los 6 consumidores de `useMapaMaterias()` (`DetalleAsesoria`, `AgendarAsesoria`, `Asesorias`, `MisMaterias`, `AdminOfertaMateria`, `AdminAsesorias`) no listan materias para el usuario: resuelven nombre por id y asumen el catálogo entero disponible sincrónicamente. Migrarlos a paginado los rompería sin ningún beneficio para el usuario, y estaba fuera del alcance del sprint. El costo se paga una sola vez por sesión (`staleTime: Infinity`) y todavía no se midió en producción.

## Señal de revisión

Cualquiera de estas tres: (a) el catálogo crece lo suficiente para que la cascada de requests sea perceptible en la primera pantalla que monte `useMapaMaterias()`; (b) se ataca la deuda [0006](0006-sin-paginacion-listados.md) completa y se fija una convención de paginación de proyecto — ahí se decide de una vez cómo se sirve el caso lookup; (c) aparece un segundo consumidor que necesita el catálogo completo bajo una latencia peor (móvil, red institucional).
