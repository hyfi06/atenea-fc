# 0031 — Paginación y búsqueda del catálogo de materias

**Status:** Accepted
**Date:** 2026-08-19

## Context

`GET /api/materias/materias/` devolvía el catálogo completo (400+ registros) en una sola respuesta, sin paginación y sin búsqueda por texto: `DialogoAgregarMateria` traía todo el array y filtraba en cliente con `.filter()`. Es el caso con volumen real del proyecto y la razón por la que la [deuda 0006](../technical-debt/0006-sin-paginacion-listados.md) sigue activa.

No había convención previa: `REST_FRAMEWORK` en `config/settings/base.py` nunca definió `DEFAULT_PAGINATION_CLASS`, y ningún viewset del proyecto declaraba `pagination_class`. Tampoco existía en el frontend ningún uso de `useInfiniteQuery`, `fetchNextPage` ni `IntersectionObserver`.

El resto de los listados (`RegistroAsesor`, `Disponibilidad`, `Asesoria`, `carreras`) no está en alcance de este sprint y no fue revisado.

## Decision

**Paginación acotada al viewset, no global.** `PaginacionMaterias(PageNumberPagination)` con `page_size = 50` vive en `materias/pagination.py` y se declara como `pagination_class` de `MateriaViewSet`. `REST_FRAMEWORK` queda intacto: agregar `DEFAULT_PAGINATION_CLASS` cambiaría el contrato de todos los listados del proyecto sin haberlos revisado ni testeado.

50 por página es el balance entre pocos round-trips para el consumidor que necesita el catálogo entero y primer render rápido en el scroll infinito. `Materia.Meta.ordering = ["nombre"]` ya garantiza un orden determinista, requisito de cualquier paginación por offset.

**La búsqueda se mueve al backend.** `filter_backends = [SearchFilter]` con `search_fields = ["nombre", "clave"]` (`icontains`, OR entre campos), combinable con los filtros `carrera` y `habilitada_asesorias` que ya resolvía `get_queryset`. Sin esto, paginar rompería silenciosamente el filtro en cliente: dejaría de ver el catálogo completo.

**Dos modos de fetching sobre el mismo endpoint, en el frontend:**

- `useMaterias()` conserva su firma (`Materia[]`) recorriendo todas las páginas dentro de `obtenerTodasLasMaterias()` hasta `next === null`. Los 6 consumidores de lookup (`useMapaMaterias` en `DetalleAsesoria`, `AgendarAsesoria`, `Asesorias`, `MisMaterias`, `AdminOfertaMateria`, `AdminAsesorias`) no listan para el usuario: resuelven nombre por id y necesitan el catálogo entero en memoria. El costo de N requests queda registrado como [deuda 0027](../technical-debt/0027-useMaterias-recorre-todas-las-paginas.md).
- `useMateriasInfinitas(params)` con `useInfiniteQuery` es el modo de listar+buscar, usado únicamente por `DialogoAgregarMateria`. `carrera`, `search` y `habilitada_asesorias` entran a la `queryKey`, así que cambiar cualquiera reinicia la paginación desde la página 1 sin código extra.

`apiGet` **no** se generaliza a un cliente consciente de paginación: el constructor de rutas y el envelope se manejan en `features/catalogo/api.ts`. Materias es hoy el único endpoint paginado; generalizar antes del segundo es prematuro.

`DialogoAgregarMateria` suma un `<select>` de carrera poblado con `useCarreras()` — el catálogo completo de carreras, no las carreras de las materias ya cargadas, que con scroll infinito estaría incompleto hasta scrollear todo.

## Consequences

- La respuesta de listado de materias es un **breaking change**: `{count, next, previous, results}` en vez de `Materia[]`. Todo consumidor nuevo debe leer `results`. El detalle (`/{id}/`) no cambia.
- El scroll infinito introduce el primer `IntersectionObserver` del proyecto; jsdom no lo implementa, así que `frontend/src/test/setup.ts` lleva un stub no-op y los tests que necesitan disparar la intersección lo sobreescriben en su archivo.
- La búsqueda deja de ser instantánea: cuesta un round-trip con 300ms de debounce, y a cambio busca sobre el catálogo completo (antes solo sobre lo que hubiera en memoria) y también por `clave`.
- Cargar el catálogo entero pasa de 1 request a 8 (400 materias / 50). Ver deuda 0027.
- La deuda 0006 **no se cierra**: sigue sin haber convención de paginación de proyecto y el resto de los listados sigue devolviendo la colección completa.

## Alternatives considered

- **`DEFAULT_PAGINATION_CLASS` global.** Fija la convención de una vez, que es justamente lo que pide la señal de revisión de la deuda 0006. Se descarta para este sprint: cambiaría el contrato de `asesorias`, `carreras` y `academico` sin revisar sus consumidores, y el pedido era acotado a materias. Queda como el camino natural cuando se ataque la deuda 0006 completa.
- **Endpoint aparte sin paginar para el caso de lookup.** Evitaría los N requests de `useMaterias()`. Se descarta: agrega superficie de API para un problema de rendimiento que todavía no se midió, y `staleTime: Infinity` hace que el costo se pague una sola vez por sesión. Registrado como deuda 0027 con su señal de revisión.
- **Exponer `page_size` como query param** para que el lookup pida una página gigante y el diálogo una chica. Se descarta por la misma razón: resuelve un costo no medido y deja al cliente decidir el tamaño de página, que es exactamente lo que la paginación existe para acotar.
- **Dejar la búsqueda en cliente sobre las páginas ya cargadas.** Cero cambios de backend. Se descarta porque rompe silenciosamente: el usuario buscaría solo dentro de lo que alcanzó a scrollear, sin ninguna señal de que el resto del catálogo existe.
- **Botón "cargar más" en vez de scroll infinito.** Más simple y sin `IntersectionObserver`. Se descarta porque el pedido explícito fue scroll infinito.
