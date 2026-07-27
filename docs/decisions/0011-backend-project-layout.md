# 0011 — Convención de layout del proyecto backend

**Status:** Accepted
**Date:** 2026-07-27

## Context

Django distingue entre el "proyecto" (el paquete de configuración global: settings, URLconf raíz, WSGI/ASGI) y las "apps" (unidades de dominio con sus propios modelos/migraciones/vistas). Como los servicios de la SAE se van a integrar de forma incremental (ver [architecture-overview.md](../architecture-overview.md)), conviene fijar desde el inicio dónde vive cada cosa para que agregar la siguiente app sea mecánico.

## Decision

- El paquete de proyecto Django se llama `config/` (no `backend/` ni el nombre del producto) y vive en `backend/config/`. Contiene `settings/` (ver [0009](0009-settings-split-django-environ.md)), `urls.py`, `wsgi.py`, `asgi.py`, `celery.py` y, para piezas verdaderamente transversales sin modelo propio (como un health check), un `views.py` a nivel de proyecto.
- Cada app de dominio vive directamente en `backend/<nombre-app>/` (ej. `backend/accounts/`), no anidada bajo un paquete intermedio tipo `apps/`.
- Umbral para crear una app nueva en vez de agregar código a `config/`: en cuanto algo tiene modelo propio, más de un par de vistas relacionadas, o lógica de dominio que se pueda probar de forma aislada, se vuelve su propia app. Un solo endpoint sin estado (como el health check) no lo amerita.

## Consequences

- El nombre `config` para el paquete de proyecto es una convención común en la comunidad Django (evita la confusión de tener una carpeta con el mismo nombre que el proyecto repetida dos veces, ej. `backend/backend/`).
- Agregar el siguiente servicio de la SAE es: crear `backend/<app>/`, registrarla en `INSTALLED_APPS`, y opcionalmente su propio ADR si introduce una decisión de arquitectura nueva.
- Si en algún momento hay múltiples vistas/utilidades de proyecto sin dueño claro, se promueven a una app `core` — no se crea preventivamente ahora.

## Alternatives considered

- **Nombrar el paquete de proyecto igual que el producto (`atenea/`):** es lo que genera `django-admin startproject atenea` por default, pero mezcla el nombre del producto con el nombre técnico del paquete de configuración, y complica renombrar el producto más adelante.
- **Apps bajo `backend/apps/<app>/`:** un nivel de anidamiento extra sin beneficio real dado el tamaño actual del proyecto.
