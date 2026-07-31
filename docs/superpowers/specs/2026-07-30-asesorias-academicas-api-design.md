## Asesorías Académicas — Fase 2: capa DRF (API)

**Status:** Approved
**Date:** 2026-07-30

### Context

La Fase 0+1 de Asesorías Académicas (`docs/superpowers/plans/2026-07-30-asesorias-academicas.md`, respaldada por [ADR 0016](../../decisions/0016-asesorias-academicas.md)) implementa los perfiles de identidad (`PerfilAlumno`, `PerfilAcademico`) y los cuatro modelos de dominio (`PerfilAsesorAcademico`, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) con toda la lógica de negocio en métodos del modelo, deliberadamente sin capa DRF — ADR 0016 reserva esa capa para "un plan de Fase 2 separado, con su propia spec". Esta spec es esa Fase 2.

**Prerrequisito:** esta fase depende de que la Fase 0+1 esté completa, en particular el Task 5 (`Asesoria.clean()`, `marcar_asistencia()`, `guardar_notas()`, `cancelar()`) y el Task 6 (notificaciones Celery). No modifica el modelo de datos existente, salvo una extensión puntual a `Asesoria.clean()` (ver Decision 3).

Tampoco `carreras` ni `materias` (catálogo académico, [ADR 0015](../../decisions/0015-catalogo-academico.md)) tienen capa DRF todavía — el flujo de búsqueda del alumno (por carrera/materia) la necesita para poblar los filtros del frontend, así que esta spec también la cubre.

### Decisions captured

1. **Dos apps, misma pasada**: endpoints de solo lectura para `carreras`/`materias` (catálogo) + la superficie completa de `asesorias` (asesor y alumno). Se agrupan porque el flujo del alumno no es usable sin ambos.
2. **`ModelViewSet` + `@action` para los recursos CRUD del asesor** (`RegistroAsesor`, `Disponibilidad`, y la parte "administrativa" de `Asesoria`), siguiendo el precedente de [ADR 0002](../../decisions/0002-drf-for-api.md) (DRF, patrón viewsets/serializers). Los métodos de negocio ya escritos en el modelo (`agregar_materia`, `marcar_asistencia`, `guardar_notas`, `cancelar`) se exponen como `@action` — el serializer/vista no reimplementa la regla, solo la invoca y traduce el resultado a HTTP.
3. **Ventana de fechas agendable = semana en curso + la siguiente**, fija en código (no derivada de un modelo de calendario, que no existe — ver deuda técnica). Función `ventana_agendable(hoy=None) -> tuple[date, date]` en `asesorias/servicios.py`, devuelve `(hoy, domingo_que_cierra_la_semana_siguiente)`. Se usa en dos lugares:
   - el endpoint de búsqueda de disponibilidad (no ofrece fechas fuera de la ventana);
   - una extensión a `Asesoria.clean()` (agregada en este plan, junto al chequeo de día-de-semana ya existente de la Fase 1) — así la ventana queda protegida sin importar el punto de entrada (API, admin, shell), consistente con el principio ya establecido de que la lógica de negocio vive en el modelo.
4. **`AsesoriaViewSet` es compartido entre alumno y asesor**, no dos viewsets separados — evita duplicar el shape del recurso. `get_queryset()` y `get_permissions()` ramifican según `hasattr(request.user, "perfil_alumno")` vs `hasattr(request.user, "perfil_asesor_academico")`. Un alumno solo ve/crea/cancela sus propias `Asesoria`; un asesor solo ve/marca asistencia/agrega notas sobre sesiones ligadas a sus propias `Disponibilidad`.
5. **Búsqueda de disponibilidad como `APIView` dedicada, no un `ReadOnlyModelViewSet` de `Disponibilidad`**: el resultado no son filas de `Disponibilidad` tal cual, son instancias concretas `(fecha, disponibilidad)` dentro de la ventana agendable, ya excluyendo los bloques que ya tienen una `Asesoria` no cancelada en esa fecha — una transformación que no encaja en el shape CRUD estándar.
6. **Permisos en `asesorias/permissions.py`**: `EsAlumno`/`EsAsesorAcademico` (chequeo de rol vía `hasattr`) para acceso a la vista; permisos de objeto (`EsDueñoDelRegistro`, `EsDueñoDeLaAsesoria`) para que nadie opere sobre recursos ajenos — ver Error handling para el código HTTP en cada caso.
7. **Alta de `PerfilAsesorAcademico` sigue siendo solo por admin** — sin endpoint de auto-registro en esta fase, consistente con que el área queda fija tras la creación (ADR 0016) y con que el volumen esperado de altas es bajo (ver deuda técnica).
8. **Condición de carrera del anti-doble-booking se traduce a `409 Conflict`**: la vista de creación de `Asesoria` captura el `IntegrityError` del `UniqueConstraint` condicional (`unique_slot_disponibilidad_fecha_no_cancelada`, ya existente desde la Fase 1) y responde `409` con un mensaje explícito, en vez de dejar que DRF lo propague como `500`.
9. **Sin paginación** en los endpoints de listado — no hay convención de paginación establecida en el proyecto (`REST_FRAMEWORK` en `config/settings/base.py` no la define) y el volumen esperado por usuario es pequeño. Registrado como deuda técnica, no como decisión permanente.

### Resources & endpoints

```
# Catálogo (solo lectura)
GET  /api/carreras/areas/
GET  /api/carreras/carreras/
GET  /api/materias/materias/                 # filtrable por carrera, habilitada_asesorias

# Asesor (scoped a request.user.perfil_asesor_academico)
GET  /api/asesorias/registros/
POST /api/asesorias/registros/
POST /api/asesorias/registros/{id}/materias/  # {materia_id} -> RegistroAsesor.agregar_materia()

GET    /api/asesorias/disponibilidades/
POST   /api/asesorias/disponibilidades/
PATCH  /api/asesorias/disponibilidades/{id}/
DELETE /api/asesorias/disponibilidades/{id}/

# Búsqueda (alumno)
GET  /api/asesorias/disponibilidad/buscar/    # ?carrera=&materia=&formato=

# Asesoria (compartido alumno/asesor, ramificado por rol)
GET  /api/asesorias/asesorias/                # "mis sesiones", según rol de request.user
POST /api/asesorias/asesorias/                # solo alumno -> agenda
POST /api/asesorias/asesorias/{id}/cancelar/          # solo alumno dueño
POST /api/asesorias/asesorias/{id}/marcar_asistencia/ # solo asesor dueño
POST /api/asesorias/asesorias/{id}/notas/             # solo asesor dueño
```

### Data flow

- **Asesor, cada semestre**: `POST /registros/` (crea `RegistroAsesor`, usa `unique_together(asesor, semestre)` ya existente) → `POST /registros/{id}/materias/` por cada materia de su pool (la vista llama `agregar_materia()`, traduce `ValidationError` a `400`) → `POST/PATCH /disponibilidades/` por cada bloque de 30 min.
- **Alumno**: `GET /disponibilidad/buscar/?carrera=X&materia=Y` → recibe instancias `(fecha, disponibilidad_id, hora_inicio, hora_fin, formato, ubicacion/liga_virtual)` dentro de la ventana agendable, ya sin los slots ocupados → `POST /asesorias/` con `{disponibilidad_id, fecha, materia_id}` → la vista invoca la creación del modelo (dispara `clean()` con los dos chequeos: día-de-semana y ventana) dentro de una transacción, captura `IntegrityError` → `409` si otro alumno ganó la carrera.
- **Ciclo de vida**: `POST /asesorias/{id}/cancelar/` (alumno dueño) → `cancelar()`. `POST /asesorias/{id}/marcar_asistencia/` (asesor dueño, solo después de la fecha/hora — ya validado en el modelo) → `marcar_asistencia()`. `POST /asesorias/{id}/notas/` (asesor dueño, solo si `asistio=True` — ya validado en el modelo) → `guardar_notas()`.
- **Notificaciones**: sin cambios respecto a la Fase 1 — siguen disparándose desde la señal `post_save` y desde `cancelar()`, no desde la vista.

### Error handling

| Situación | Código | Origen |
|---|---|---|
| Sin autenticación | `401` | `IsAuthenticated` (default de DRF ya configurado) |
| Rol equivocado (ej. asesor llamando `POST /asesorias/` de agendado) | `403` | `EsAlumno`/`EsAsesorAcademico` |
| Objeto ajeno (cancelar la sesión de otro alumno, marcar asistencia de otro asesor) | `403` | `EsDueñoDelRegistro`/`EsDueñoDeLaAsesoria` |
| `ValidationError` de un método del modelo (`agregar_materia`, `clean()`, `marcar_asistencia`, `guardar_notas`, `cancelar`) | `400` | capturado en la vista, mensaje del modelo tal cual |
| Doble-booking (condición de carrera en `INSERT`) | `409` | `IntegrityError` del `UniqueConstraint`, capturado en la vista de creación |

### Testing

`APITestCase` + `force_authenticate`, por flujo:
- Catálogo: listado y filtro de `materias` por `carrera`/`habilitada_asesorias`.
- Permisos: rol equivocado → `403`; objeto ajeno → `403`.
- `RegistroAsesor`/`Disponibilidad`: CRUD scoped al asesor autenticado (no ve/edita los de otro asesor).
- Búsqueda de disponibilidad: respeta la ventana agendable (no devuelve fechas fuera de la semana en curso + siguiente), excluye slots con `Asesoria` no cancelada.
- Agendado: creación exitosa; `ValidationError` del modelo → `400`; doble-booking simulado (dos requests sobre el mismo `disponibilidad_id`+`fecha`) → segunda respuesta `409`.
- Ciclo de vida completo end-to-end: agendar (alumno) → marcar asistencia (asesor) → guardar notas (asesor) → verificar que un alumno no puede marcar asistencia ni un asesor no-dueño no puede operar sobre la sesión.
- Cancelación: libera el slot (una segunda `Asesoria` sobre el mismo `disponibilidad_id`+`fecha` se puede crear después de cancelar la primera), vía API.

### Out of scope

- Modelo de calendario/periodo académico real (la ventana agendable sigue siendo una regla fija en código) — deuda técnica.
- Alta de `PerfilAsesorAcademico` vía API (sigue siendo solo admin) — deuda técnica.
- Límites de uso (sesiones simultáneas por alumno, ventana mínima de cancelación, límite de cancelaciones) — deuda técnica, ya reservada en ADR 0016.
- Cierre automático (Celery Beat) de sesiones vencidas sin asistencia marcada, recordatorios periódicos por email — deuda técnica, ya reservada en ADR 0016.
- Paginación de listados — deuda técnica.
- Propagación de ediciones de `Disponibilidad` a `Asesoria` ya agendadas — sigue siendo snapshot inmutable, deuda técnica ya reservada en ADR 0016.
- Documentación OpenAPI/Swagger de los endpoints — puede agregarse después sin afectar el diseño de esta fase.

### Self-review

- Sin placeholders/TBD — cada decisión tiene un valor concreto (ventana = semana en curso + siguiente, alta de asesor = solo admin, catálogo incluido), confirmados explícitamente por el usuario antes de escribir esta spec.
- Alcance cohesivo: capa DRF completa para el MVP de Asesorías (catálogo read-only + asesorias), sin mezclar con cambios al modelo de datos salvo la extensión puntual y ya justificada a `Asesoria.clean()`.
- Sin contradicciones con ADR 0016: la ventana agendable y la búsqueda de disponibilidad estaban explícitamente en "Out of scope" de esa ADR como pendientes de Fase 2, y esta spec las resuelve sin reabrir ninguna decisión ya tomada de Fase 0+1.
- Consistente con patrones ya establecidos: ADR 0002 (DRF/viewsets), permisos como capa delgada sobre lógica de modelo (principio explícito de ADR 0016), `IsAuthenticated` + JWT ya configurados en `REST_FRAMEWORK`/`SIMPLE_JWT`.
- Deuda técnica generada por esta fase (ventana fija en código, sin paginación, alta de asesor solo admin) documentada en [`docs/technical-debt.md`](../../technical-debt.md), no solo mencionada aquí.
