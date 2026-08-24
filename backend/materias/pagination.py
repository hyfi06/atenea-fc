from rest_framework.pagination import PageNumberPagination


class PaginacionMaterias(PageNumberPagination):
    """Paginación del catálogo de materias (400+ registros).

    Propia de `MateriaViewSet`, no `DEFAULT_PAGINATION_CLASS`: el resto de los
    listados del proyecto sigue devolviendo la colección completa (deuda 0006)
    y cambiarlos globalmente los rompería sin haberlos revisado.

    50 por página: pocos round-trips para el loop de `useMaterias()` en el
    frontend, y primer render rápido en el scroll infinito del diálogo de
    agregar materia.
    """

    page_size = 50
