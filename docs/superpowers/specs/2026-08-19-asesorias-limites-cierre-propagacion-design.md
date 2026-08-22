# Asesorías: límite de 2hrs y propagación de Disponibilidad

**Fecha:** 2026-08-19
**Estado:** Aprobado para plan de implementación

## Contexto

Tres deudas activas de la app `asesorias`, agrupadas por tocar el mismo modelo (`Disponibilidad`/`Asesoria`):

1. **[Deuda 0003](../technical-debt/0003-sin-limites-uso-asesorias.md)** — sin límites de uso. Alcance de este sprint: ventana mínima de 2 horas antes de la sesión, tanto para agendar como para cancelar.
2. **[Deuda 0004](../technical-debt/0004-sin-cierre-automatico-recordatorios.md)** — sin cierre automático de sesiones vencidas. **Fuera de alcance de este sprint** (ver sección "Fuera de alcance") — decisión posterior a la exploración inicial, revertida antes de arrancar el plan de implementación. La deuda completa (cierre automático y recordatorios periódicos) queda tal cual, sin tocar.
3. **[Deuda 0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md)** — editar una `Disponibilidad` no propaga a sesiones ya agendadas.

## Hallazgos clave de la exploración

- **Agendado**: la validación de negocio vive en `AsesoriaSerializer.validate()` (`asesorias/serializers.py`), que construye una instancia no guardada y llama a `Asesoria.clean()` (`asesorias/models.py`). `clean()` ya valida día de semana y ventana agendable (semana en curso/siguiente) — es granularidad de **fecha**, no de hora. No existe ningún chequeo de "faltan N horas".
- **Cancelación**: `Asesoria.cancelar()` (`models.py`) solo valida `estado == "agendada"`. Se expone vía la acción `cancelar` del viewset, que ya captura `ValidationError` y devuelve 400 — el mecanismo de propagación de errores está listo.
- **Patrón de datetime aware ya existe**: `marcar_asistencia()` construye `timezone.make_aware(datetime.combine(self.fecha, self.hora_inicio))` — mismo patrón a reusar para comparar contra `timezone.now() + timedelta(hours=2)`.
- **Caso borde importante**: `Disponibilidad.desactivar()` invoca `asesoria.cancelar()` en bulk cuando un asesor da de baja un horario completo. Si la regla de 2hrs se mete dentro de `cancelar()` sin distinción, ese flujo administrativo queda bloqueado también — **decisión de diseño explícita**: la baja de un asesor debe poder saltarse la ventana de 2hrs (no es el alumno cancelando de último minuto, es el asesor invalidando el bloque).
- **Celery Beat no existe en el proyecto** — ni en `config/celery.py` (sin `beat_schedule`), ni en settings (`CELERY_BEAT_SCHEDULE` ausente), ni en `docker-compose.dev.yml` (solo `celery-worker`). `django-celery-beat` no está instalado. El ADR 0004 de topología Docker ya preveía el contenedor `celery-beat` como "solo necesario cuando existan tareas programadas" — sigue pendiente para cuando el cierre automático (deuda 0004) se retome; no se agrega en este sprint.
- **Estados de `Asesoria`**: `agendada`, `cancelada`, `realizada` — no hay estado separado para "vencida sin marcar". La deuda 0004 señala que la decisión de producto (marcar automáticamente como no-asistida vs. dejar pendiente) no estaba tomada; queda sin resolver, fuera de este sprint.
- **Patrón de tarea async a reusar**: `asesorias/tasks.py` ya tiene `enviar_confirmacion_agenda` y `enviar_notificacion_cancelacion` (`@shared_task`, import diferido de modelos, `select_related`). La tarea de notificación de resincronización (deuda 0005) sigue el mismo estilo.
- **Snapshot de Disponibilidad → Asesoria**: campos `formato`, `ubicacion`, `liga_virtual` (más `hora_inicio`, que no debería resincronizarse — cambiar la hora de una sesión ya agendada es un cambio distinto, fuera de alcance). El copiado ocurre en `AsesoriaSerializer.validate()`/`create()`.
- **Query ya centralizado**: `Disponibilidad.sesiones_futuras()` filtra exactamente "asesorías agendadas, futuras, de este bloque" — es el criterio único a reusar para el bulk-update de resincronización (su docstring ya pide mantenerlo como fuente única de verdad).
- **Admin sin acciones custom**: `DisponibilidadAdmin`/`AsesoriaAdmin` son `ModelAdmin` simples. El resto del área SAE usa vistas DRF dedicadas (`Admin*View` en `views.py`, con permiso `EsMiembroSAE`) en vez de Django admin actions — es el patrón más consistente con el código existente.

## Diseño

### 1. Ventana de 2hrs (deuda 0003)

- Agregar validación en `Asesoria.clean()`: rechazar si `timezone.now() > inicio - timedelta(hours=2)` al agendar (mismo lugar que la validación de ventana agendable existente).
- Agregar validación equivalente en `Asesoria.cancelar()`, con un parámetro `forzar: bool = False` (o similar) que `Disponibilidad.desactivar()` pase explícitamente para saltarse la ventana en su flujo de baja masiva — así la regla vive en un solo lugar (`cancelar()`) sin duplicar lógica, y el caso borde queda resuelto de forma explícita y testeada, no accidental.
- Mensajes de error claros y distintos para "no puedes agendar, faltan menos de 2hrs" vs. "no puedes cancelar, faltan menos de 2hrs" — el frontend debe poder mostrarlos tal cual.

### 2. Resincronizar snapshot de Disponibilidad (deuda 0005)

- Nuevo endpoint DRF `POST /api/asesorias/disponibilidades/{id}/resincronizar/` (acción del `DisponibilidadViewSet`, permiso restringido al asesor dueño del registro — no requiere `EsMiembroSAE`, es el asesor corrigiendo su propio typo), que actualiza en bulk `formato`, `ubicacion`, `liga_virtual` de todas las asesorías en `sesiones_futuras()` de esa disponibilidad, tomando los valores actuales de la `Disponibilidad`.
- **No toca `hora_inicio`** — eso es un cambio de horario, no una corrección de datos de contacto, y está fuera de alcance de esta deuda.
- Dispara notificación por correo a los alumnos con sesión afectada (reusar `asesorias/tasks.py`, nueva tarea o extensión de una existente) — el alumno debe enterarse si cambió la liga de Zoom de su sesión ya agendada.

### 3. Bloques de 1 hora y nuevo flujo de agendado del alumno

**Origen:** feedback recibido tras la demo del 21 de agosto — fuera del alcance original de las deudas 0003/0004/0005, pero se agrega aquí porque cae sobre el mismo modelo (`Disponibilidad`) y el plan de implementación asociado todavía no arrancó (Task 1 es justo donde nace la constante de duración de sesión).

**Rejilla de 1 hora (antes 30 min):**

- `DURACION_SESION = datetime.timedelta(hours=1)` en vez de `minutes=30` — un solo valor, porque `Disponibilidad.hora_fin` ya queda parametrizado sobre esa constante en el Task 1 del plan.
- `Disponibilidad.clean()`: la rejilla pasa de `hora_inicio.minute not in (0, 30)` a `hora_inicio.minute != 0` (solo horas en punto).
- Sin migración de columnas — `hora_fin` es una `@property` calculada, no una columna; solo cambia la lógica de validación.
- Datos de la demo del 21 de agosto son descartables (confirmado con el usuario) — se limpian con el comando `limpiar_demo` existente. `backend/accounts/demo_data.py` ya usa horas en punto (10:00, 12:00), así que sigue siendo válido tal cual; se amplía con un segundo bloque por asesor en el mismo día (distinta hora) para que el nuevo drill-down materia→día→bloque tenga más de una tarjeta que mostrar en la siguiente demo. Un día con bloques de dos asesores distintos requeriría que `sembrar_demo` asignara la misma materia a dos académicos de la misma área — hoy asigna una materia por área automáticamente (`sembrar_demo.py`) — así que queda fuera de este ajuste, no es necesario para demostrar el flujo nuevo.
- ADR a actualizar: [0016](../../decisions/0016-asesorias-academicas.md) gana un Changelog nuevo documentando 30→60 min — no es una decisión arquitectónica nueva (es un cambio de parámetro sobre una ya aceptada), así que no amerita ADR propio ni superseder al 0016.
- Documentación de contrato a actualizar: `docs/development/api-frontend.md` (párrafo de `Disponibilidad` y el ejemplo de `hora_fin`), y el copy de `DialogoNuevoBloque` ("Bloque recurrente de 30 minutos" → "de 1 hora").

**Nuevo flujo de agendado en `/asesorias/nueva` (solo frontend):**

- `OfertaAsesorias` (lista de materias) no cambia — sigue siendo el primer paso.
- Al hacer clic en una materia, `AgendarAsesoria` deja de pedir primero un asesor: el wizard pasa de 4 pasos (asesor → día → bloque → carrera) a 3 (día → bloque → carrera).
- Se agrupan directamente los días con asesoría disponible para esa materia (across todos los asesores), reusando `GET /api/asesorias/disponibilidad/buscar/?materia=` **sin** `?asesor=` — el endpoint ya soporta la consulta sin ese filtro y ya devuelve `asesor_nombre`/`formato`/`ubicacion`/`liga_virtual` por slot; el agrupado por día ya existe client-side (`agruparPorDia`). No se toca el backend para esto.
- Hook nuevo `useDisponibilidadDeMateria(materiaId)`: mismo endpoint, habilitado solo con `materiaId` (sin depender de un `registroId` de asesor).
- Al elegir un día, las tarjetas de bloques de hora muestran profesor + modalidad (`asesor_nombre`, `formato`/`ubicacion`/`liga_virtual`) — campos que `SlotDisponibilidad` ya trae pero que hoy no se pintan porque el asesor ya estaba elegido de antemano.
- El paso de confirmación de carrera y el manejo de conflicto 409 al agendar (bloque tomado) no cambian.
- **No se toca** `useAsesoresDeMateria` / `AsesoresDeMateriaView` (`GET /oferta/{materia_id}/asesores/`) — los sigue usando `AdminOfertaMateria`, la pantalla de consulta del SAE, ajena a este cambio.

### Testing

- Extender `test_asesoria.py` / `test_api_asesoria.py`: agendar/cancelar rechazado dentro de la ventana de 2hrs, aceptado fuera de ella; `Disponibilidad.desactivar()` sigue funcionando dentro de la ventana (caso borde explícito).
- Nuevo test para el endpoint de resincronización: bulk-update solo afecta `sesiones_futuras()`, no toca sesiones pasadas ni canceladas, no toca `hora_inicio`.
- Nuevo test de rejilla: `Disponibilidad` con `hora_inicio` en `:30` es rechazada; en `:00` es aceptada; `hora_fin` = `hora_inicio` + 1h.
- Frontend: reescribir `AgendarAsesoria.test.tsx` para el wizard de 3 pasos (sin paso de asesor, con aserciones de `asesor_nombre`/`formato` en las tarjetas de bloque); actualizar `logica.test.ts` (`horasDelDia`) para 14 filas de 1h en vez de 28 de 30 min.

### Fuera de alcance

- **Cierre automático de sesiones vencidas y recordatorios periódicos por email antes de la sesión** (deuda 0004 completa) — decisión explícita de dejar la deuda 0004 sin tocar en este sprint; no se agrega Celery Beat ni `django-celery-beat`.
- Límite de sesiones simultáneas / límite de cancelaciones (parte original de la deuda 0003, no pedida — el pedido explícito fue solo la ventana de 2hrs).
- Cambiar `hora_inicio` de sesiones ya agendadas vía resincronización.
- Migración de datos reales de producción de la rejilla de 30 min a 1h — en producción todavía no hay datos (confirmado con el usuario); las pruebas se hicieron en staging con datos descartables.
- Cambiar el paso de confirmación de carrera o el endpoint `oferta/{materia_id}/asesores/` usado por la consulta del SAE.
