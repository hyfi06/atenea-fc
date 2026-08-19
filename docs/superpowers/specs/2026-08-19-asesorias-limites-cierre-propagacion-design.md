# Asesorías: límite de 2hrs, cierre automático y propagación de Disponibilidad

**Fecha:** 2026-08-19
**Estado:** Aprobado para plan de implementación

## Contexto

Tres deudas activas de la app `asesorias`, agrupadas por tocar el mismo modelo y compartir infraestructura (Celery):

1. **[Deuda 0003](../technical-debt/0003-sin-limites-uso-asesorias.md)** — sin límites de uso. Alcance de este sprint: ventana mínima de 2 horas antes de la sesión, tanto para agendar como para cancelar.
2. **[Deuda 0004](../technical-debt/0004-sin-cierre-automatico-recordatorios.md)** — sin cierre automático de sesiones vencidas. Alcance de este sprint: solo el cierre automático (los recordatorios periódicos quedan fuera).
3. **[Deuda 0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md)** — editar una `Disponibilidad` no propaga a sesiones ya agendadas.

## Hallazgos clave de la exploración

- **Agendado**: la validación de negocio vive en `AsesoriaSerializer.validate()` (`asesorias/serializers.py`), que construye una instancia no guardada y llama a `Asesoria.clean()` (`asesorias/models.py`). `clean()` ya valida día de semana y ventana agendable (semana en curso/siguiente) — es granularidad de **fecha**, no de hora. No existe ningún chequeo de "faltan N horas".
- **Cancelación**: `Asesoria.cancelar()` (`models.py`) solo valida `estado == "agendada"`. Se expone vía la acción `cancelar` del viewset, que ya captura `ValidationError` y devuelve 400 — el mecanismo de propagación de errores está listo.
- **Patrón de datetime aware ya existe**: `marcar_asistencia()` construye `timezone.make_aware(datetime.combine(self.fecha, self.hora_inicio))` — mismo patrón a reusar para comparar contra `timezone.now() + timedelta(hours=2)`.
- **Caso borde importante**: `Disponibilidad.desactivar()` invoca `asesoria.cancelar()` en bulk cuando un asesor da de baja un horario completo. Si la regla de 2hrs se mete dentro de `cancelar()` sin distinción, ese flujo administrativo queda bloqueado también — **decisión de diseño explícita**: la baja de un asesor debe poder saltarse la ventana de 2hrs (no es el alumno cancelando de último minuto, es el asesor invalidando el bloque).
- **Celery Beat no existe en el proyecto** — ni en `config/celery.py` (sin `beat_schedule`), ni en settings (`CELERY_BEAT_SCHEDULE` ausente), ni en `docker-compose.dev.yml` (solo `celery-worker`). `django-celery-beat` no está instalado. El ADR 0004 de topología Docker ya preveía el contenedor `celery-beat` como "solo necesario cuando existan tareas programadas" — este es ese momento.
- **Estados de `Asesoria`**: `agendada`, `cancelada`, `realizada` — no hay estado separado para "vencida sin marcar". La deuda 0004 señala que la decisión de producto (marcar automáticamente como no-asistida vs. dejar pendiente) no estaba tomada; este spec la resuelve: marcar automáticamente como `realizada` con `asistio=False`, reusando `marcar_asistencia(False)`, que ya modela exactamente esa transición.
- **Patrón de tarea async a reusar**: `asesorias/tasks.py` ya tiene `enviar_confirmacion_agenda` y `enviar_notificacion_cancelacion` (`@shared_task`, import diferido de modelos, `select_related`). La tarea periódica de cierre sigue el mismo estilo.
- **Snapshot de Disponibilidad → Asesoria**: campos `formato`, `ubicacion`, `liga_virtual` (más `hora_inicio`, que no debería resincronizarse — cambiar la hora de una sesión ya agendada es un cambio distinto, fuera de alcance). El copiado ocurre en `AsesoriaSerializer.validate()`/`create()`.
- **Query ya centralizado**: `Disponibilidad.sesiones_futuras()` filtra exactamente "asesorías agendadas, futuras, de este bloque" — es el criterio único a reusar para el bulk-update de resincronización (su docstring ya pide mantenerlo como fuente única de verdad).
- **Admin sin acciones custom**: `DisponibilidadAdmin`/`AsesoriaAdmin` son `ModelAdmin` simples. El resto del área SAE usa vistas DRF dedicadas (`Admin*View` en `views.py`, con permiso `EsMiembroSAE`) en vez de Django admin actions — es el patrón más consistente con el código existente.

## Diseño

### 1. Ventana de 2hrs (deuda 0003)

- Agregar validación en `Asesoria.clean()`: rechazar si `timezone.now() > inicio - timedelta(hours=2)` al agendar (mismo lugar que la validación de ventana agendable existente).
- Agregar validación equivalente en `Asesoria.cancelar()`, con un parámetro `forzar: bool = False` (o similar) que `Disponibilidad.desactivar()` pase explícitamente para saltarse la ventana en su flujo de baja masiva — así la regla vive en un solo lugar (`cancelar()`) sin duplicar lógica, y el caso borde queda resuelto de forma explícita y testeada, no accidental.
- Mensajes de error claros y distintos para "no puedes agendar, faltan menos de 2hrs" vs. "no puedes cancelar, faltan menos de 2hrs" — el frontend debe poder mostrarlos tal cual.

### 2. Cierre automático (deuda 0004)

- Instalar `django-celery-beat`, agregarlo a `THIRD_PARTY_APPS`, migrar.
- Agregar servicio `celery-beat` a `docker-compose.dev.yml` (y a la documentación de despliegue de producción, coordinando con el repo `services` igual que se hizo para SMTP).
- Nueva tarea periódica `cerrar_sesiones_vencidas` en `asesorias/tasks.py` (estilo `@shared_task`, import diferido): itera `Asesoria.objects.filter(estado="agendada", ...)` con fecha/hora ya pasada y llama `marcar_asistencia(False)` sobre cada una.
- `CELERY_BEAT_SCHEDULE` en settings: frecuencia a definir (propuesta: cada 15-30 min es suficiente, no es una operación sensible al segundo).
- Marcar deuda 0004 como resuelta (parcialmente — los recordatorios periódicos, que sí menciona el texto original de la deuda, quedan fuera de este sprint y deberían quedar anotados como pendiente dentro del mismo ítem, no como nueva deuda).

### 3. Resincronizar snapshot de Disponibilidad (deuda 0005)

- Nuevo endpoint DRF `POST /api/asesorias/disponibilidades/{id}/resincronizar/` (acción del `DisponibilidadViewSet`, permiso restringido al asesor dueño del registro — no requiere `EsMiembroSAE`, es el asesor corrigiendo su propio typo), que actualiza en bulk `formato`, `ubicacion`, `liga_virtual` de todas las asesorías en `sesiones_futuras()` de esa disponibilidad, tomando los valores actuales de la `Disponibilidad`.
- **No toca `hora_inicio`** — eso es un cambio de horario, no una corrección de datos de contacto, y está fuera de alcance de esta deuda.
- Dispara notificación por correo a los alumnos con sesión afectada (reusar `asesorias/tasks.py`, nueva tarea o extensión de una existente) — el alumno debe enterarse si cambió la liga de Zoom de su sesión ya agendada.

### Testing

- Extender `test_asesoria.py` / `test_api_asesoria.py`: agendar/cancelar rechazado dentro de la ventana de 2hrs, aceptado fuera de ella; `Disponibilidad.desactivar()` sigue funcionando dentro de la ventana (caso borde explícito).
- Nuevo test para la tarea periódica: `Asesoria` vencida sin marcar pasa a `realizada`/`asistio=False` tras ejecutar la tarea; una `Asesoria` futura o ya marcada no se toca.
- Nuevo test para el endpoint de resincronización: bulk-update solo afecta `sesiones_futuras()`, no toca sesiones pasadas ni canceladas, no toca `hora_inicio`.

### Fuera de alcance

- Recordatorios periódicos por email antes de la sesión (parte original de la deuda 0004, no pedida en este sprint).
- Límite de sesiones simultáneas / límite de cancelaciones (parte original de la deuda 0003, no pedida — el pedido explícito fue solo la ventana de 2hrs).
- Cambiar `hora_inicio` de sesiones ya agendadas vía resincronización.
