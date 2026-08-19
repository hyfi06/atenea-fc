# Catálogo de materias: paginación + scroll infinito

**Fecha:** 2026-08-19
**Estado:** Aprobado para plan de implementación

## Contexto

**[Deuda 0006](../technical-debt/0006-sin-paginacion-listados.md)** — sin paginación en los endpoints de listado. Alcance de este sprint: solo el catálogo de `Materia` (400+ registros, el caso con volumen real hoy), no el resto de los listados del proyecto. Pedido explícito: si no se usa la búsqueda, scroll infinito con paginación.

## Hallazgos clave de la exploración

- `MateriaViewSet` (`materias/views.py`) no tiene `pagination_class`; filtra por `carrera` y `habilitada_asesorias` vía query params, pero **no tiene filtro de búsqueda por texto en el backend**. `REST_FRAMEWORK` en `config/settings/base.py` no define `DEFAULT_PAGINATION_CLASS` en ningún lado del proyecto — no hay convención previa ni patrón custom de otro listado para reusar; se introduce desde cero.
- Frontend: `useMaterias()` (`features/catalogo/api.ts`) usa TanStack Query (`useQuery`, no `useInfiniteQuery`) y trae el array completo de una sola llamada, con `staleTime: Infinity`. Se consume en 6 lugares distintos (`DetalleAsesoria`, `AgendarAsesoria`, `Asesorias`, `MisMaterias`, `AdminOfertaMateria`, `AdminAsesorias`) que construyen un `Map` en memoria vía `useMapaMaterias()` — todos asumen tener el catálogo completo disponible sincrónicamente.
- **El componente candidato real a scroll infinito** es `DialogoAgregarMateria.tsx` — el único lugar donde se navega/busca materias como lista (no como lookup por id), con un `<ul>` de altura fija y `overflow-y-auto` ya armado como contenedor de scroll. Filtra hoy en cliente sobre el array completo.
- **La búsqueda es 100% client-side hoy** — no hay parámetro `search`/`q` en el backend. Esto significa que paginar el backend **sí es un cambio de red, no solo de UI**: si se pagina, el filtro cliente actual deja de ver el catálogo completo y se rompe silenciosamente salvo que la búsqueda se mueva al backend también.
- No existe ningún patrón previo de `useInfiniteQuery`/`fetchNextPage`/`IntersectionObserver`/"cargar más" en todo el frontend — se introduce desde cero.

## Decisión de diseño clave

El pedido dice "si no se usa la búsqueda, hagamos scroll infinito" — esto implica **dos modos de fetching sobre el mismo endpoint paginado**, no una feature aparte de la búsqueda:

- **Sin término de búsqueda**: `useInfiniteQuery` contra `/api/materias/materias/?carrera=...&habilitada_asesorias=...`, páginas de tamaño fijo, cargando más al hacer scroll (IntersectionObserver sobre un sentinel al final de la lista).
- **Con término de búsqueda**: el filtro se mueve al backend (nuevo query param `search`, vía `SearchFilter` de DRF sobre `nombre`/`clave`), con debounce en el frontend; la respuesta ya viene acotada por el backend, así que no necesita scroll infinito (un resultado de búsqueda razonable cabe en una página).

Esto resuelve el único consumidor que lista+busca (`DialogoAgregarMateria`). Los otros 5 consumidores (`useMapaMaterias`) siguen necesitando el catálogo completo como lookup — **quedan sin cambio**, ya que no listan para el usuario, solo resuelven nombre por id. Cambiarlos a paginado los rompería sin necesidad; no están en el alcance del pedido.

## Diseño

### Backend

- `PageNumberPagination` de DRF, tamaño de página a definir (propuesta: 50 — suficientemente grande para pocos round-trips, suficientemente chico para que el primer render sea rápido con 400+ registros), como `pagination_class` propia de `MateriaViewSet` (no `DEFAULT_PAGINATION_CLASS` global — el resto de los listados del proyecto no están en alcance de este sprint, cambiarlo globalmente los afectaría sin haberlos revisado).
- Agregar `filter_backends = [SearchFilter]` con `search_fields = ["nombre", "clave"]` a `MateriaViewSet`.
- Respuesta pasa de array plano a envelope `{count, next, previous, results}` — **breaking change** para los 5 consumidores que esperan `Materia[]`.

### Frontend

- `apiGet` (`api/client.ts`) no maneja envelopes de paginación — decidir si se generaliza (`apiGetPaginated<T>`) o se maneja ad-hoc en `catalogo/api.ts`. Recomendado: función nueva específica en `catalogo/api.ts`, no generalizar `apiGet` todavía (YAGNI hasta que un segundo endpoint paginado lo pida).
- `useMaterias()` se mantiene para los 5 consumidores de lookup, pero debe recorrer todas las páginas internamente (loop de fetch hasta que `next` sea `null`) para no romperlos — siguen viendo un array completo, a costa de N requests en vez de 1. Alternativa a evaluar en el plan: si N requests resulta demasiado costoso, considerar un endpoint separado sin paginar solo para el caso de lookup (`?habilitada_asesorias=1` ya acota bastante). Esta decisión se deja para el plan de implementación, con el trade-off explícito.
- Nuevo hook `useMateriasInfinitas(params)` con `useInfiniteQuery`, usado únicamente por `DialogoAgregarMateria.tsx`.
- `DialogoAgregarMateria.tsx`: reemplazar el `.filter()` en cliente por el query param `search` (con debounce, propuesta 300ms) cuando hay término, y `fetchNextPage` disparado por `IntersectionObserver` sobre un `<li>` sentinel al fondo del `<ul>` cuando no hay término activo.

### Testing

- Backend: paginación (`count`/`next`/`previous`/tamaño de página), búsqueda por `nombre`/`clave` (parcial, insensible a mayúsculas), combinación de `search` con los filtros existentes (`carrera`, `habilitada_asesorias`).
- Frontend: `DialogoAgregarMateria` — carga inicial, scroll dispara siguiente página, escribir en búsqueda cancela el modo scroll infinito y dispara búsqueda en backend (con debounce), los 5 consumidores de `useMapaMaterias()` siguen viendo el catálogo completo sin cambios de comportamiento visible.

### Fuera de alcance

- Paginar otros listados del proyecto (`RegistroAsesor`, `Disponibilidad`, `Asesoria`, etc.) — la deuda 0006 los menciona, pero el pedido de este sprint es solo materias.
- Generalizar `apiGet` a un cliente consciente de paginación — se deja para cuando un segundo endpoint lo necesite.

## Enmienda: selector de carrera en `DialogoAgregarMateria`

Aprobada en brainstorming bounded (2026-08-19), sobre el mismo componente que ya se reescribe arriba — se integra al mismo plan, no aparte.

- `Materia` registra `carrera` (FK a `carreras.Carrera`); hoy `DialogoAgregarMateria` no deja filtrar por carrera, solo lista+busca en texto.
- Nuevo estado local `carrera: number | null` (default `null` = "Todas"), mismo patrón que `OfertaAsesorias.tsx:32`.
- `<select>` poblado con el catálogo completo de carreras vía el hook ya existente `useCarreras()` (`catalogo/api.ts`, pega a `/api/carreras/carreras/`) — no derivado de las materias ya cargadas (con scroll infinito estaría incompleto hasta scrollear todo).
- `carrera` se pasa como parámetro adicional a `useMateriasInfinitas({ habilitada_asesorias: true, carrera, search })`. El backend (`MateriaViewSet.get_queryset`) ya combina `carrera` + `habilitada_asesorias`; combinarlo también con `search` es parte del mismo trabajo de paginación de este spec, no un requisito nuevo.
- `carrera` entra a la `queryKey` de `useInfiniteQuery` — cambiar de carrera reinicia la paginación/búsqueda de forma natural.
- UI: mismo layout que `OfertaAsesorias.tsx:57-71` (label + `<select>` con opción "Todas"), colocado arriba del campo de búsqueda dentro del diálogo.
- Testing: caso nuevo en `DialogoAgregarMateria.test.tsx` — cambiar carrera dispara refetch con el query param correcto; combinar carrera + búsqueda funciona.
