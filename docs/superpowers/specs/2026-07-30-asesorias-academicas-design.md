## Asesorías Académicas (Fase 0: perfiles + Fase 1: modelos de dominio, sin DRF)

**Status:** Approved
**Date:** 2026-07-30

### Context

Primer servicio funcional de producción de Atenea: **Asesorías Académicas** (independiente del PIT / Programa Institucional de Tutorías). Se construye sobre el catálogo académico ya implementado (`carreras`, `materias`, ADR 0015).

Alcance de negocio validado con el usuario en sesión previa:

- Un académico se registra como asesor eligiendo un área de adscripción fija y, cada semestre, un subconjunto de materias y su disponibilidad horaria.
- Semestre en formato `AAAAN` (otoño = `AAAA1`, primavera = `AAAA2`), mismo formato que `OfertaMateria.semestre`.
- Un alumno busca asesores por carrera/materia/horario, agenda una sesión, puede cancelarla (nunca borrarla).
- El asesor recibe notificaciones por email, ve sus sesiones próximas/históricas, marca asistencia y agrega notas — **las notas no se pueden guardar si la sesión no ocurrió**.
- Formato de sesión: presencial (con ubicación) o virtual (con liga de video).

Al diseñar el modelo se encontró que `PerfilAlumno`/`PerfilAcademico` (patrón de identidad de la ADR 0012) no existen todavía en el código — solo `accounts.User` está implementado. Esta spec incluye crearlos como prerrequisito.

Decisión de disponibilidad confirmada explícitamente por el usuario: **slots discretos de 30 minutos**, no un rango con duración configurable — el asesor selecciona uno o más bloques de 30 min, no necesariamente contiguos.

### Decisions captured

1. **Fase 0 en `accounts`**: `PerfilAlumno` (`numero_cuenta`) y `PerfilAcademico` (`numero_trabajador`), `OneToOneField` a `User`, siguiendo exactamente el patrón de ADR 0012. Sin M2M de carreras (eso es de un futuro `HistoriaAcademica`).
2. **App nueva `asesorias`** (no se mezcla con `accounts`/`carreras`/`materias`), con 4 modelos: `PerfilAsesorAcademico`, `RegistroAsesor`, `Disponibilidad`, `Asesoria`.
3. **`PerfilAsesorAcademico.area`** es fija tras la creación — el asesor no la cambia semestre a semestre; solo cambia su `RegistroAsesor.materias` y `Disponibilidad`.
4. **`RegistroAsesor`** es el registro anual/semestral: `unique_together(asesor, semestre)`, M2M a `Materia` con validación explícita en `agregar_materia()` (área coincide, `habilitada_asesorias=True`, existe `OfertaMateria(semestre, se_imparte=True)`) en vez de dejarlo sin restricción a nivel de modelo.
5. **`Disponibilidad` = slots discretos de 30 min**, no rango + duración. Cada fila es un bloque `(dia_semana, hora_inicio)` con su propio `formato`/`ubicacion`/`liga_virtual`. `hora_fin` es una `@property` calculada (`hora_inicio + 30min`), no una columna. `clean()` valida que `hora_inicio` caiga en la rejilla de 30 min (minuto 0 o 30, segundo 0).
6. **Anti-doble-booking vía constraint de BD**, no `select_for_update`: `UniqueConstraint` condicional sobre `(disponibilidad, fecha)` excluyendo `estado="cancelada"`. Una condición de carrera falla con `IntegrityError` en el segundo `INSERT` — suficiente porque los bloques son de tamaño fijo, no hace falta `ExclusionConstraint` de rangos.
7. **`Asesoria` guarda un snapshot** de `hora_inicio`/`formato`/`ubicacion`/`liga_virtual` al agendar, copiado de la `Disponibilidad` elegida — editar la disponibilidad después no reescribe sesiones ya agendadas.
8. **`Asesoria.materia` es obligatoria** (`on_delete=PROTECT`, no nullable) — confirmado explícitamente por el usuario.
9. **Asistencia y notas**: `asistio` es tri-estado (`None`/`True`/`False`); `estado` pasa a `"realizada"` cuando el asesor marca asistencia. `guardar_notas()` rechaza la operación si `asistio is not True` (regla de negocio explícita del alcance).
10. **`on_delete=PROTECT`** en toda FK que forma parte de un historial (`RegistroAsesor.asesor`, `Asesoria.disponibilidad`, `Asesoria.materia`, `Asesoria.alumno`) — igual que el catálogo, nada se pierde por borrar un registro relacionado.
11. **Lógica de negocio vive en métodos del modelo** (`agregar_materia`, `marcar_asistencia`, `guardar_notas`, `cancelar`), no en vistas — prepara el terreno para que una futura capa DRF (Fase 2, fuera de este plan) sea delgada.
12. **Sin capa DRF en esta pasada** — mismo precedente que el catálogo académico. Serializers/viewsets/urls/permission classes quedan para un plan de Fase 2 separado.
13. **Notificaciones por email vía Celery**: esqueleto de tareas async (`enviar_confirmacion_agenda`, `enviar_notificacion_cancelacion`) en `asesorias/tasks.py`, invocadas desde los métodos de servicio. Sin tarea periódica (Celery beat) de recordatorio en esta pasada.

### Data model

```python
# backend/accounts/models.py (Fase 0, agregado al archivo existente)

class PerfilAlumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_alumno")
    numero_cuenta = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.numero_cuenta} — {self.user.email}"


class PerfilAcademico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_academico")
    numero_trabajador = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.numero_trabajador} — {self.user.email}"
```

```python
# backend/asesorias/models.py

import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

DIAS_SEMANA = [
    (0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"),
    (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
]
FORMATOS = [("presencial", "Presencial"), ("virtual", "Virtual")]
ESTADOS_ASESORIA = [("agendada", "Agendada"), ("cancelada", "Cancelada"), ("realizada", "Realizada")]


class PerfilAsesorAcademico(models.Model):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="perfil_asesor_academico"
    )
    area = models.ForeignKey(
        "carreras.Area", on_delete=models.PROTECT, related_name="asesores_academicos"
    )
    activo = models.BooleanField(default=True)

    def clean(self):
        if not hasattr(self.user, "perfil_academico"):
            raise ValidationError("Un asesor académico debe tener PerfilAcademico.")

    def __str__(self):
        return f"{self.user.email} — {self.area.nombre}"


class RegistroAsesor(models.Model):
    asesor = models.ForeignKey(PerfilAsesorAcademico, on_delete=models.PROTECT, related_name="registros")
    semestre = models.CharField(max_length=5)
    materias = models.ManyToManyField("materias.Materia", related_name="registros_asesor", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asesor", "semestre"], name="unique_registro_asesor_semestre"),
        ]

    def agregar_materia(self, materia):
        if materia.carrera.area_id != self.asesor.area_id:
            raise ValidationError("La materia no pertenece al área del asesor.")
        if not materia.habilitada_asesorias:
            raise ValidationError("La materia no está habilitada para asesorías.")
        if not materia.ofertas.filter(semestre=self.semestre, se_imparte=True).exists():
            raise ValidationError("La materia no se imparte en este semestre.")
        self.materias.add(materia)

    def __str__(self):
        return f"{self.asesor} — {self.semestre}"


class Disponibilidad(models.Model):
    registro = models.ForeignKey(RegistroAsesor, on_delete=models.CASCADE, related_name="disponibilidades")
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    formato = models.CharField(max_length=10, choices=FORMATOS)
    ubicacion = models.CharField(max_length=200, blank=True)
    liga_virtual = models.URLField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["registro", "dia_semana", "hora_inicio"], name="unique_bloque_registro"
            ),
        ]

    def clean(self):
        if self.hora_inicio.minute not in (0, 30) or self.hora_inicio.second != 0:
            raise ValidationError("hora_inicio debe caer en la rejilla de 30 minutos.")
        if self.formato == "presencial" and not self.ubicacion:
            raise ValidationError("Falta ubicación para una disponibilidad presencial.")
        if self.formato == "virtual" and not self.liga_virtual:
            raise ValidationError("Falta liga virtual para una disponibilidad virtual.")

    @property
    def hora_fin(self):
        inicio = datetime.datetime.combine(datetime.date.min, self.hora_inicio)
        return (inicio + datetime.timedelta(minutes=30)).time()

    def __str__(self):
        return f"{self.registro} — {self.get_dia_semana_display()} {self.hora_inicio}"


class Asesoria(models.Model):
    alumno = models.ForeignKey("accounts.PerfilAlumno", on_delete=models.PROTECT, related_name="asesorias")
    disponibilidad = models.ForeignKey(Disponibilidad, on_delete=models.PROTECT, related_name="asesorias")
    materia = models.ForeignKey("materias.Materia", on_delete=models.PROTECT, related_name="asesorias")

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    formato = models.CharField(max_length=10, choices=FORMATOS)
    ubicacion = models.CharField(max_length=200, blank=True)
    liga_virtual = models.URLField(blank=True)

    estado = models.CharField(max_length=10, choices=ESTADOS_ASESORIA, default="agendada")
    asistio = models.BooleanField(null=True, default=None)
    notas = models.TextField(blank=True)

    cancelado_por = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    motivo_cancelacion = models.TextField(blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["disponibilidad", "fecha"],
                condition=models.Q(estado__in=["agendada", "realizada"]),
                name="unique_slot_disponibilidad_fecha_no_cancelada",
            ),
        ]

    def clean(self):
        if self.fecha.weekday() != self.disponibilidad.dia_semana:
            raise ValidationError("La fecha no coincide con el día de la disponibilidad.")

    def marcar_asistencia(self, asistio: bool):
        inicio = timezone.make_aware(datetime.datetime.combine(self.fecha, self.hora_inicio))
        if timezone.now() < inicio:
            raise ValidationError("No se puede marcar asistencia antes de que ocurra la sesión.")
        self.asistio = asistio
        self.estado = "realizada"
        self.save()

    def guardar_notas(self, texto: str):
        if self.asistio is not True:
            raise ValidationError("No se pueden guardar notas si la sesión no ocurrió.")
        self.notas = texto
        self.save()

    def cancelar(self, usuario, motivo=""):
        if self.estado != "agendada":
            raise ValidationError("Solo se puede cancelar una sesión agendada.")
        self.estado = "cancelada"
        self.cancelado_por = usuario
        self.motivo_cancelacion = motivo
        self.save()

    def __str__(self):
        return f"{self.alumno} — {self.disponibilidad.registro.asesor} — {self.fecha}"
```

```python
# backend/asesorias/tasks.py (esqueleto)

from celery import shared_task


@shared_task
def enviar_confirmacion_agenda(asesoria_id: int):
    ...


@shared_task
def enviar_notificacion_cancelacion(asesoria_id: int):
    ...
```

### Data flow

- **Registro del asesor**: un académico con `PerfilAcademico` obtiene `PerfilAsesorAcademico` (área fija, vía admin en esta pasada). Cada semestre crea un `RegistroAsesor` y llama `agregar_materia()` por cada materia de su pool (validada contra área + `habilitada_asesorias` + `OfertaMateria` del semestre), y crea sus `Disponibilidad` (bloques de 30 min).
- **Agendado del alumno** (lógica de negocio, sin endpoint DRF todavía): dado un `PerfilAlumno`, se filtran `Disponibilidad.activa=True` cuyo `registro.materias` incluya la materia buscada y `registro.asesor.area` coincida con la carrera del alumno; se descartan bloques que ya tengan una `Asesoria` no cancelada en la fecha concreta elegida; se crea la `Asesoria` con el snapshot de formato/ubicación/liga — el `UniqueConstraint` de BD es la última línea de defensa ante condiciones de carrera.
- **Ciclo de vida de la sesión**: `agendada` → (`cancelar()`) → `cancelada`, o `agendada` → (`marcar_asistencia()`, solo después de la fecha/hora) → `realizada`. `guardar_notas()` solo aplica sobre una `Asesoria` con `asistio=True`.
- **Notificaciones**: al crear una `Asesoria` y al llamar `cancelar()`, se encola la tarea Celery correspondiente (`.delay(asesoria.id)`).

### Error handling

- `RegistroAsesor.agregar_materia()` lanza `ValidationError` (no crea la relación M2M) si la materia no es del área del asesor, no está habilitada para asesorías, o no tiene oferta activa ese semestre — el llamador decide si reporta el error al usuario o lo ignora en carga masiva.
- `Disponibilidad.clean()` rechaza horas fuera de la rejilla de 30 min y bloques presenciales sin ubicación / virtuales sin liga — se debe invocar `full_clean()` antes de guardar (o el admin lo hace automáticamente vía `ModelForm`).
- Doble-booking: el `UniqueConstraint` de `Asesoria` produce `IntegrityError` en el segundo `INSERT` sobre el mismo `(disponibilidad, fecha)` no cancelado — quien llame al método de creación debe capturarlo (en esta pasada, sin DRF, el llamador es un test o el admin).
- `marcar_asistencia()` antes de que ocurra la sesión, `guardar_notas()` sin asistencia confirmada, o `cancelar()` sobre una sesión que no está `agendada` — los tres lanzan `ValidationError` explícito, no fallan silenciosamente.

### Testing

- `accounts/tests/`: unicidad de `numero_cuenta`/`numero_trabajador`.
- `asesorias/tests/`: `clean()` de `PerfilAsesorAcademico` rechaza `user` sin `PerfilAcademico`; `unique_together(asesor, semestre)` de `RegistroAsesor`; las tres validaciones de `agregar_materia()` (área distinta, no habilitada, sin oferta); `clean()` de `Disponibilidad` (rejilla de 30 min, ubicación/liga según formato); constraint `unique_bloque_registro`; doble-booking real de `Asesoria` vía `IntegrityError` sobre `(disponibilidad, fecha)` no cancelada; `marcar_asistencia()` antes de tiempo lanza error; `guardar_notas()` sin asistencia lanza error; `cancelar()` sobre sesión no agendada lanza error; una `Asesoria` cancelada libera el slot (se puede crear otra sobre el mismo `(disponibilidad, fecha)`).

### Out of scope

- Capa DRF (serializers/viewsets/urls/permission classes) — plan de Fase 2 separado, con su propia spec.
- Modelo de calendario/periodo con fechas reales de inicio/fin de semestre — la ventana de fechas agendables queda como decisión de la Fase 2 (ej. ventana rodante), no se modela aquí.
- Límite de sesiones simultáneas por alumno, ventana mínima de cancelación, límite de cancelaciones — MVP permisivo, se revisita si hay abuso en producción.
- Cierre automático (Celery beat) de sesiones `agendada` cuya fecha ya pasó sin asistencia marcada — queda como dato "pendiente" en esta pasada.
- Recordatorio periódico por email antes de la sesión — solo confirmación y cancelación en esta pasada.
- Edición de `PerfilAsesorAcademico.area` una vez creada — se trata como fija; una corrección puntual sería manual vía admin.
- `HistoriaAcademica` (carreras en las que está inscrito un alumno) — `PerfilAlumno` no incluye esa relación en esta pasada.

### Self-review

- Sin placeholders/TBD — cada decisión tiene un valor concreto; lo que queda abierto está explícitamente en "Out of scope", no mezclado con las decisiones tomadas.
- Alcance cohesivo: Fase 0 (perfiles, prerrequisito mínimo) + Fase 1 (4 modelos de dominio, sin DRF) — no se mezcla con la Fase 2 (API).
- Sin contradicciones entre esta spec y la ADR 0016 asociada.
- Consistente con los patrones ya establecidos: perfiles como `PerfilX` (ADR 0012), `on_delete=PROTECT` para historial, `semestre` en formato `AAAAN` (ADR 0015), commits atómicos (ADR 0007).
