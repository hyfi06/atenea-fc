# Asesorías: límite de 2hrs, cierre automático y propagación de Disponibilidad — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar las deudas técnicas 0003 (parcial), 0004 (parcial) y 0005 de la app `asesorias`: ventana mínima de 2 horas para agendar/cancelar, cierre automático de sesiones vencidas vía Celery Beat, y endpoint de resincronización del snapshot de `Disponibilidad` hacia sus sesiones futuras.

**Architecture:** Toda la regla de negocio vive en `asesorias/models.py` (`Asesoria.clean()`, `Asesoria.cancelar()`, `Disponibilidad.resincronizar_sesiones_futuras()`); las vistas solo traducen `ValidationError` → 400, siguiendo el patrón ya presente en `asesorias/views.py`. El cierre automático es una `@shared_task` nueva en `asesorias/tasks.py` disparada por un contenedor `celery-beat` nuevo con `django-celery-beat` como scheduler. Sin cambios de esquema en modelos propios (solo las migraciones que trae `django_celery_beat`).

**Tech Stack:** Django 6 + DRF, Celery + Redis, `django-celery-beat`, PostgreSQL 16, Docker Compose, `uv` para dependencias.

**Spec:** `docs/superpowers/specs/2026-08-19-asesorias-limites-cierre-propagacion-design.md`

## Global Constraints

- 100% backend. **No se toca `frontend/`.** Los contratos nuevos se documentan en `docs/development/api-frontend.md` para que un plan de frontend futuro los consuma.
- Comando de tests: desde `backend/`, `uv run manage.py test <ruta> -v 2`. Requiere Postgres. Sin Postgres local: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test <ruta> -v 2` (desde la raíz del repo).
- Idioma del código, docstrings, comentarios y mensajes de error: **español**. Encabezados de ADR en inglés (`Context`/`Decision`/`Consequences`/`Alternatives considered`), cuerpo en español — igual que `docs/decisions/0028-*.md`.
- Formato de commit: `[type][scope] resumen` + lista de cambios + `Signed-off-by`. Ver `docs/development/commit-conventions.md`.
- Errores de negocio del modelo se propagan como `{"detail": ["mensaje"]}` (lista), convención ya vigente.
- **Valores fijados por este plan** (el spec los dejaba abiertos):
  - Ventana mínima de anticipación: **2 horas** — `VENTANA_MINIMA_ANTICIPACION = datetime.timedelta(hours=2)`.
  - Duración de sesión usada para el cierre automático: **30 minutos** — `DURACION_SESION = datetime.timedelta(minutes=30)`. El cierre solo toca sesiones que **ya terminaron** (`inicio + 30 min <= ahora`), no las que apenas arrancaron.
  - Frecuencia de `cerrar_sesiones_vencidas`: **cada 15 minutos** — `crontab(minute="*/15")`.
  - Parámetro de bypass en `cancelar()`: **keyword-only `forzar: bool = False`**, en español como el resto de la firma (`usuario`, `motivo`).
  - Notificación de resincronización: **tarea nueva** `enviar_notificacion_resincronizacion(asesoria_id)` en `asesorias/tasks.py` (no se extiende `enviar_notificacion_cancelacion`: distinto asunto, distinto cuerpo, distinto disparador).
  - Deuda 0003 y 0004 quedan **parcialmente resueltas** (no se crean deudas nuevas para lo pendiente); deuda 0005 queda **resuelta**.

## Archivos tocados

| Archivo | Responsabilidad |
|---|---|
| `backend/asesorias/models.py` | Constantes de ventana/duración, `Asesoria.momento_inicio`, validación en `clean()` y `cancelar(forzar=)`, `Disponibilidad.resincronizar_sesiones_futuras()` |
| `backend/asesorias/tasks.py` | `cerrar_sesiones_vencidas`, `enviar_notificacion_resincronizacion` |
| `backend/asesorias/views.py` | Acción `resincronizar` del `DisponibilidadViewSet` |
| `backend/config/settings/base.py` | `django_celery_beat` en `THIRD_PARTY_APPS`, `CELERY_BEAT_SCHEDULE` |
| `backend/pyproject.toml` / `uv.lock` | Dependencia `django-celery-beat` |
| `docker-compose.dev.yml` / `docker-compose.prod.yml` | Servicio `celery-beat` |
| `docs/development/despliegue-produccion.md` | Servicio `atenea-beat` en el repo `services` |
| `docs/development/api-frontend.md` | Mensajes de error nuevos + endpoint `resincronizar/` |
| `docs/decisions/0029-*.md` | ADR nuevo |
| `docs/technical-debt/0003|0004|0005*.md` + `README.md` | Cierre de deudas |
| `backend/asesorias/tests/*` | Tests nuevos + ajuste de tests existentes que agendan/cancelan fuera de la ventana |

---

### Task 1: Ventana de 2 horas al agendar (`Asesoria.clean()`)

**Files:**
- Modify: `backend/asesorias/models.py`
- Test: `backend/asesorias/tests/test_asesoria.py`
- Test: `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**
- Consumes: nada de tasks previos.
- Produces:
  - `asesorias.models.VENTANA_MINIMA_ANTICIPACION: datetime.timedelta`
  - `asesorias.models.DURACION_SESION: datetime.timedelta`
  - `asesorias.models.MENSAJE_AGENDAR_FUERA_DE_VENTANA: str`
  - `asesorias.models.MENSAJE_CANCELAR_FUERA_DE_VENTANA: str`
  - `Asesoria.momento_inicio -> datetime.datetime` (aware)

- [ ] **Step 1: Escribir los tests que fallan (modelo)**

Agregar al final de `backend/asesorias/tests/test_asesoria.py`:

```python
class VentanaAnticipacionAgendarTests(AsesoriaTestsBase):
    """Deuda 0003: no se puede agendar con menos de 2 horas de anticipación."""

    def _disponibilidad_de_hoy_a_medianoche(self):
        """Bloque de hoy a las 00:00 — su inicio siempre quedó en el pasado,
        así el test no depende de la hora a la que corra la suite."""
        hoy = timezone.localdate()
        return hoy, Disponibilidad.objects.create(
            registro=self.registro, dia_semana=hoy.weekday(),
            hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/hoy",
        )

    def test_agendar_dentro_de_la_ventana_falla(self):
        hoy, disponibilidad = self._disponibilidad_de_hoy_a_medianoche()
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=hoy, hora_inicio=disponibilidad.hora_inicio,
            formato=disponibilidad.formato, liga_virtual=disponibilidad.liga_virtual,
        )
        with self.assertRaises(ValidationError) as ctx:
            asesoria.clean()
        self.assertIn(
            "No puedes agendar una sesión con menos de 2 horas de anticipación.",
            ctx.exception.messages,
        )

    def test_agendar_fuera_de_la_ventana_pasa(self):
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes,
            hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato,
            liga_virtual=self.disponibilidad.liga_virtual,
        )
        asesoria.clean()  # no lanza

    def test_momento_inicio_combina_fecha_y_hora(self):
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes,
            hora_inicio=datetime.time(10, 0),
            formato=self.disponibilidad.formato,
            liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertEqual(asesoria.momento_inicio.date(), self.proximo_lunes)
        self.assertEqual(asesoria.momento_inicio.hour, 10)
        self.assertIsNotNone(asesoria.momento_inicio.tzinfo)
```

- [ ] **Step 2: Escribir los tests que fallan (API)**

Agregar al final de `backend/asesorias/tests/test_api_asesoria.py`:

```python
class AgendarDentroDeLaVentanaApiTests(AsesoriaApiTestsBase):
    """Deuda 0003: el POST de agendar devuelve 400 dentro de la ventana."""

    def test_agendar_hoy_a_medianoche_devuelve_400(self):
        hoy = timezone.localdate()
        disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=hoy.weekday(),
            hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/hoy",
        )
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": disponibilidad.id, "materia": self.materia.id,
            "fecha": str(hoy),
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "No puedes agendar una sesión con menos de 2 horas de anticipación.",
            response.data["detail"],
        )

    def test_agendar_fuera_de_la_ventana_sigue_devolviendo_201(self):
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })

        self.assertEqual(response.status_code, 201)
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `uv run manage.py test asesorias.tests.test_asesoria.VentanaAnticipacionAgendarTests asesorias.tests.test_api_asesoria.AgendarDentroDeLaVentanaApiTests -v 2`
Expected: FAIL — `AttributeError: 'Asesoria' object has no attribute 'momento_inicio'` y los tests de 400 devuelven 201.

- [ ] **Step 4: Implementar en `models.py`**

En `backend/asesorias/models.py`, reemplazar el bloque de constantes de módulo:

```python
DIAS_SEMANA = [
    (0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"),
    (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
]
FORMATOS = [("presencial", "Presencial"), ("virtual", "Virtual")]
ESTADOS_ASESORIA = [("agendada", "Agendada"), ("cancelada", "Cancelada"), ("realizada", "Realizada")]
```

por:

```python
DIAS_SEMANA = [
    (0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"),
    (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
]
FORMATOS = [("presencial", "Presencial"), ("virtual", "Virtual")]
ESTADOS_ASESORIA = [("agendada", "Agendada"), ("cancelada", "Cancelada"), ("realizada", "Realizada")]

# Duración de un bloque de asesoría. Fija la rejilla de `Disponibilidad.hora_fin`
# y el margen del cierre automático (`asesorias.tasks.cerrar_sesiones_vencidas`):
# una sesión solo se cierra cuando ya terminó, no cuando apenas arrancó.
DURACION_SESION = datetime.timedelta(minutes=30)

# Deuda 0003: ni agendar ni cancelar se permiten a menos de 2 horas del inicio.
# Agendar de último minuto no le da al asesor tiempo de enterarse; cancelar de
# último minuto lo deja plantado. `Disponibilidad.desactivar()` se salta la
# ventana a propósito (ver `Asesoria.cancelar(forzar=...)`).
VENTANA_MINIMA_ANTICIPACION = datetime.timedelta(hours=2)

MENSAJE_AGENDAR_FUERA_DE_VENTANA = (
    "No puedes agendar una sesión con menos de 2 horas de anticipación."
)
MENSAJE_CANCELAR_FUERA_DE_VENTANA = (
    "No puedes cancelar una sesión con menos de 2 horas de anticipación."
)
```

En `Disponibilidad.hora_fin`, reemplazar:

```python
    @property
    def hora_fin(self):
        inicio = datetime.datetime.combine(datetime.date.min, self.hora_inicio)
        return (inicio + datetime.timedelta(minutes=30)).time()
```

por:

```python
    @property
    def hora_fin(self):
        inicio = datetime.datetime.combine(datetime.date.min, self.hora_inicio)
        return (inicio + DURACION_SESION).time()
```

En `Asesoria`, reemplazar `clean()` y `marcar_asistencia()`:

```python
    def clean(self):
        if self.fecha.weekday() != self.disponibilidad.dia_semana:
            raise ValidationError("La fecha no coincide con el día de la disponibilidad.")
        inicio, fin = ventana_agendable()
        if not (inicio <= self.fecha <= fin):
            raise ValidationError("La fecha está fuera de la ventana agendable (semana en curso y la siguiente).")

    def marcar_asistencia(self, asistio: bool):
        inicio = timezone.make_aware(datetime.datetime.combine(self.fecha, self.hora_inicio))
        if timezone.now() < inicio:
            raise ValidationError("No se puede marcar asistencia antes de que ocurra la sesión.")
        self.asistio = asistio
        self.estado = "realizada"
        self.save()
```

por:

```python
    @property
    def momento_inicio(self):
        """Instante aware en que arranca la sesión (fecha + hora_inicio).

        Fuente única para toda comparación contra el reloj: la ventana de
        anticipación, marcar asistencia y el cierre automático.
        """
        return timezone.make_aware(datetime.datetime.combine(self.fecha, self.hora_inicio))

    def clean(self):
        if self.fecha.weekday() != self.disponibilidad.dia_semana:
            raise ValidationError("La fecha no coincide con el día de la disponibilidad.")
        inicio, fin = ventana_agendable()
        if not (inicio <= self.fecha <= fin):
            raise ValidationError("La fecha está fuera de la ventana agendable (semana en curso y la siguiente).")
        # La ventana agendable es de granularidad fecha; esto agrega la de hora.
        if timezone.now() > self.momento_inicio - VENTANA_MINIMA_ANTICIPACION:
            raise ValidationError(MENSAJE_AGENDAR_FUERA_DE_VENTANA)

    def marcar_asistencia(self, asistio: bool):
        if timezone.now() < self.momento_inicio:
            raise ValidationError("No se puede marcar asistencia antes de que ocurra la sesión.")
        self.asistio = asistio
        self.estado = "realizada"
        self.save()
```

- [ ] **Step 5: Correr los tests nuevos y verificar que pasan**

Run: `uv run manage.py test asesorias.tests.test_asesoria.VentanaAnticipacionAgendarTests asesorias.tests.test_api_asesoria.AgendarDentroDeLaVentanaApiTests -v 2`
Expected: PASS.

- [ ] **Step 6: Arreglar la regresión en `AgendarConHistorialTests`**

Esa clase agenda **para hoy a las 09:00**, lo que ahora falla si la suite corre después de las 07:00. Mover el fixture a mañana.

En `backend/asesorias/tests/test_api_asesoria.py`, dentro de `AgendarConHistorialTests.setUp`, reemplazar:

```python
        hoy = datetime.date.today()
        self.disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=hoy.weekday(), hora_inicio=datetime.time(9, 0),
            formato="virtual", liga_virtual="https://zoom.us/j/1",
        )
        self.fecha = hoy
```

por:

```python
        # Mañana, no hoy: con la ventana mínima de anticipación (deuda 0003)
        # agendar para hoy a las 09:00 falla si la suite corre después de las 07:00.
        self.fecha = datetime.date.today() + datetime.timedelta(days=1)
        self.disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=self.fecha.weekday(), hora_inicio=datetime.time(9, 0),
            formato="virtual", liga_virtual="https://zoom.us/j/1",
        )
```

- [ ] **Step 7: Correr la suite de `asesorias` completa**

Run: `uv run manage.py test asesorias -v 2`
Expected: PASS, sin fallos. En este task solo `clean()` valida la ventana (el camino de agendar), y el Step 6 ya arregló el único fixture que agendaba para hoy. Si algo más falla, arreglarlo antes de commitear.

- [ ] **Step 8: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/tests/test_asesoria.py backend/asesorias/tests/test_api_asesoria.py
git commit -m "$(cat <<'EOF'
[feat][backend] rechazar agendar una asesoría con menos de 2 horas de anticipación

- Agregar VENTANA_MINIMA_ANTICIPACION y DURACION_SESION a asesorias/models.py
- Agregar Asesoria.momento_inicio como fuente única de comparación con el reloj
- Validar la ventana en Asesoria.clean(); reusarla en marcar_asistencia()
- Mover el fixture de AgendarConHistorialTests de hoy a mañana

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 2: Ventana de 2 horas al cancelar, con bypass para `Disponibilidad.desactivar()`

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `docs/development/api-frontend.md`
- Test: `backend/asesorias/tests/test_asesoria.py`
- Test: `backend/asesorias/tests/test_disponibilidad.py`
- Test: `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**
- Consumes: `VENTANA_MINIMA_ANTICIPACION`, `MENSAJE_CANCELAR_FUERA_DE_VENTANA`, `Asesoria.momento_inicio` (Task 1).
- Produces: `Asesoria.cancelar(usuario, motivo="", *, forzar: bool = False) -> None`.

- [ ] **Step 1: Escribir el test que falla (modelo — cancelar)**

Agregar al final de `backend/asesorias/tests/test_asesoria.py`:

```python
class VentanaAnticipacionCancelarTests(AsesoriaTestsBase):
    """Deuda 0003: no se puede cancelar con menos de 2 horas de anticipación."""

    def _asesoria_de_hoy_a_medianoche(self):
        hoy = timezone.localdate()
        disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=hoy.weekday(),
            hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/hoy",
        )
        return self._crear_asesoria(
            hoy, disponibilidad=disponibilidad, hora_inicio=datetime.time(0, 0),
            liga_virtual="https://meet.example.com/hoy",
        )

    def test_cancelar_dentro_de_la_ventana_falla(self):
        asesoria = self._asesoria_de_hoy_a_medianoche()
        with self.assertRaises(ValidationError) as ctx:
            asesoria.cancelar(usuario=self.alumno.user)
        self.assertIn(
            "No puedes cancelar una sesión con menos de 2 horas de anticipación.",
            ctx.exception.messages,
        )
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "agendada")
        asesoria.delete()

    def test_cancelar_dentro_de_la_ventana_con_forzar_pasa(self):
        asesoria = self._asesoria_de_hoy_a_medianoche()
        asesoria.cancelar(usuario=self.alumno.user, forzar=True)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "cancelada")
        asesoria.delete()

    def test_cancelar_fuera_de_la_ventana_pasa(self):
        asesoria = self._crear_asesoria(self.proximo_lunes)
        asesoria.cancelar(usuario=self.alumno.user)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "cancelada")
        asesoria.delete()
```

- [ ] **Step 2: Escribir el test que falla (caso borde `desactivar()`)**

Agregar al final de `backend/asesorias/tests/test_disponibilidad.py`:

```python
class DesactivarDentroDeLaVentanaTests(SesionesFuturasTests):
    """Caso borde explícito del spec: la baja de un bloque por parte del asesor
    cancela también las sesiones que arrancan en menos de 2 horas — no es el
    alumno cancelando de último minuto, es el asesor invalidando el bloque."""

    def _bloque_que_arranca_en_menos_de_dos_horas(self):
        """Bloque cuya hora en punto cae entre 30 y 90 minutos en el futuro.

        `ahora + 90 min` truncado a la hora en punto da una separación de
        `60 - minuto` (si el minuto es < 30) o `120 - minuto` (si es >= 30):
        siempre > 30 min, así que entra en `sesiones_futuras()` sin carrera con
        el reloj, y siempre < 120 min, así que cae dentro de la ventana mínima.

        Vive en un registro aparte (otro semestre) para no chocar con el
        UniqueConstraint (registro, dia_semana, hora_inicio) del fixture base.
        """
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20262")
        pronto = timezone.localtime() + datetime.timedelta(minutes=90)
        hora = datetime.time(pronto.hour, 0)
        disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=pronto.weekday(), hora_inicio=hora,
            formato="virtual", liga_virtual="https://meet.example.com/pronto",
        )
        asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=pronto.date(), hora_inicio=hora,
            formato="virtual", liga_virtual="https://meet.example.com/pronto",
        )
        return disponibilidad, asesoria

    def test_la_sesion_esta_dentro_de_la_ventana_y_es_futura(self):
        """Guarda del propio fixture: si esto falla, los dos tests de abajo no
        prueban lo que dicen probar."""
        disponibilidad, asesoria = self._bloque_que_arranca_en_menos_de_dos_horas()

        self.assertEqual(list(disponibilidad.sesiones_futuras()), [asesoria])
        with self.assertRaises(ValidationError):
            asesoria.cancelar(usuario=self.asesor_user)

    def test_desactivar_cancela_aunque_falten_menos_de_dos_horas(self):
        disponibilidad, asesoria = self._bloque_que_arranca_en_menos_de_dos_horas()

        canceladas = disponibilidad.desactivar(
            usuario=self.asesor_user, cancelar_sesiones=True, motivo="Me enfermé.",
        )

        self.assertEqual(canceladas, 1)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "cancelada")
        self.assertEqual(asesoria.motivo_cancelacion, "Me enfermé.")
        disponibilidad.refresh_from_db()
        self.assertFalse(disponibilidad.activa)
```

- [ ] **Step 3: Escribir el test que falla (API — cancelar)**

Agregar al final de `backend/asesorias/tests/test_api_asesoria.py`:

```python
class CancelarDentroDeLaVentanaApiTests(AsesoriaApiTestsBase):
    """Deuda 0003: el POST de cancelar devuelve 400 dentro de la ventana."""

    def setUp(self):
        super().setUp()
        hoy = timezone.localdate()
        self.disponibilidad_hoy = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=hoy.weekday(),
            hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/hoy",
        )
        self.asesoria_hoy = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad_hoy, materia=self.materia,
            carrera=self.carrera, fecha=hoy, hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/hoy",
        )

    def test_alumno_no_puede_cancelar_dentro_de_la_ventana(self):
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria_hoy.id}/cancelar/", {}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "No puedes cancelar una sesión con menos de 2 horas de anticipación.",
            response.data["detail"],
        )

    def test_asesor_tampoco_puede_cancelar_dentro_de_la_ventana(self):
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria_hoy.id}/cancelar/", {}
        )

        self.assertEqual(response.status_code, 400)
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

Run: `uv run manage.py test asesorias.tests.test_asesoria.VentanaAnticipacionCancelarTests asesorias.tests.test_disponibilidad.DesactivarDentroDeLaVentanaTests asesorias.tests.test_api_asesoria.CancelarDentroDeLaVentanaApiTests -v 2`
Expected: FAIL — `cancelar()` no acepta `forzar` (`TypeError: cancelar() got an unexpected keyword argument 'forzar'`) y las cancelaciones dentro de la ventana devuelven 200 en vez de 400.

- [ ] **Step 5: Implementar en `models.py`**

En `backend/asesorias/models.py`, reemplazar `Asesoria.cancelar()`:

```python
    def cancelar(self, usuario, motivo=""):
        if self.estado != "agendada":
            raise ValidationError("Solo se puede cancelar una sesión agendada.")
        self.estado = "cancelada"
        self.cancelado_por = usuario
        self.motivo_cancelacion = motivo
        self.save()
        from asesorias.tasks import enviar_notificacion_cancelacion
        transaction.on_commit(lambda: enviar_notificacion_cancelacion.delay(self.id))
```

por:

```python
    def cancelar(self, usuario, motivo="", *, forzar=False):
        """Cancela la sesión y notifica por correo a ambas partes.

        `forzar=True` salta la ventana mínima de anticipación (deuda 0003). Lo
        usa `Disponibilidad.desactivar()`: ahí no es el alumno cancelando de
        último minuto, es el asesor invalidando el bloque completo, y
        bloquearlo dejaría al asesor sin forma de dar de baja su horario. La
        regla vive solo aquí; ningún otro punto la duplica.
        """
        if self.estado != "agendada":
            raise ValidationError("Solo se puede cancelar una sesión agendada.")
        if not forzar and timezone.now() > self.momento_inicio - VENTANA_MINIMA_ANTICIPACION:
            raise ValidationError(MENSAJE_CANCELAR_FUERA_DE_VENTANA)
        self.estado = "cancelada"
        self.cancelado_por = usuario
        self.motivo_cancelacion = motivo
        self.save()
        from asesorias.tasks import enviar_notificacion_cancelacion
        transaction.on_commit(lambda: enviar_notificacion_cancelacion.delay(self.id))
```

En `Disponibilidad.desactivar()`, reemplazar:

```python
                for asesoria in list(self.sesiones_futuras()):
                    asesoria.cancelar(
                        usuario=usuario, motivo=motivo or self.MOTIVO_BAJA_DE_HORARIO
                    )
                    canceladas += 1
```

por:

```python
                for asesoria in list(self.sesiones_futuras()):
                    # forzar=True: la baja de un horario por parte del asesor
                    # debe poder saltarse la ventana de anticipación.
                    asesoria.cancelar(
                        usuario=usuario,
                        motivo=motivo or self.MOTIVO_BAJA_DE_HORARIO,
                        forzar=True,
                    )
                    canceladas += 1
```

- [ ] **Step 6: Correr los tests nuevos y verificar que pasan**

Run: `uv run manage.py test asesorias.tests.test_asesoria.VentanaAnticipacionCancelarTests asesorias.tests.test_disponibilidad.DesactivarDentroDeLaVentanaTests asesorias.tests.test_api_asesoria.CancelarDentroDeLaVentanaApiTests -v 2`
Expected: PASS.

- [ ] **Step 7: Arreglar la regresión en `CicloDeVidaAsesoriaApiTests`**

Esa clase cancela una sesión de `lunes_pasado` (5 semanas atrás), que ahora cae dentro de la ventana. Se le agrega una sesión futura para los tests de cancelación, dejando la pasada para los de asistencia/notas.

En `backend/asesorias/tests/test_api_asesoria.py`, dentro de `CicloDeVidaAsesoriaApiTests`, reemplazar `setUp`:

```python
    def setUp(self):
        super().setUp()
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
```

por:

```python
    def setUp(self):
        super().setUp()
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)
        # Sesión pasada: sirve para marcar asistencia y guardar notas.
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        # Sesión futura: cancelar una sesión pasada ahora choca con la ventana
        # mínima de anticipación (deuda 0003), así que los tests de cancelación
        # usan esta.
        self.asesoria_futura = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
```

Reemplazar `test_alumno_cancela_y_libera_el_slot`:

```python
    def test_alumno_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)
```

por:

```python
    def test_alumno_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria_futura.id}/cancelar/", {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)
```

Reemplazar `test_asesor_dueño_cancela_y_libera_el_slot`:

```python
    def test_asesor_dueño_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)
```

por:

```python
    def test_asesor_dueño_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria_futura.id}/cancelar/", {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)
```

Reemplazar `test_cancelacion_expone_motivo_y_rol_de_quien_cancelo`:

```python
    def test_cancelacion_expone_motivo_y_rol_de_quien_cancelo(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/",
            {"motivo": "Se empalmó con un examen."},
        )
```

por:

```python
    def test_cancelacion_expone_motivo_y_rol_de_quien_cancelo(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria_futura.id}/cancelar/",
            {"motivo": "Se empalmó con un examen."},
        )
```

Reemplazar `test_el_asesor_ve_el_motivo_de_una_cancelacion_del_alumno`:

```python
    def test_el_asesor_ve_el_motivo_de_una_cancelacion_del_alumno(self):
        self.asesoria.cancelar(usuario=self.alumno_user, motivo="Ya no lo necesito.")

        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")
```

por:

```python
    def test_el_asesor_ve_el_motivo_de_una_cancelacion_del_alumno(self):
        self.asesoria_futura.cancelar(usuario=self.alumno_user, motivo="Ya no lo necesito.")

        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria_futura.id}/")
```

Reemplazar `test_cancelacion_del_asesor_reporta_rol_asesor`:

```python
    def test_cancelacion_del_asesor_reporta_rol_asesor(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/",
            {"motivo": "Junta académica."},
        )
```

por:

```python
    def test_cancelacion_del_asesor_reporta_rol_asesor(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria_futura.id}/cancelar/",
            {"motivo": "Junta académica."},
        )
```

- [ ] **Step 8: Documentar los mensajes de error en `api-frontend.md`**

En `docs/development/api-frontend.md`, reemplazar estas dos filas de la tabla de `asesorias`:

```markdown
| `POST` | `/api/asesorias/asesorias/{id}/cancelar/` | `EsAlumnoOAsesorAcademico` + dueño | `{motivo?}` — el alumno o el asesor dueño de la sesión pueden cancelarla |
```

por:

```markdown
| `POST` | `/api/asesorias/asesorias/{id}/cancelar/` | `EsAlumnoOAsesorAcademico` + dueño | `{motivo?}` — el alumno o el asesor dueño de la sesión pueden cancelarla. `400 {"detail": ["No puedes cancelar una sesión con menos de 2 horas de anticipación."]}` dentro de la ventana mínima (ver abajo) |
```

Y justo debajo del párrafo que empieza con `**Ventana agendable:**`, agregar:

```markdown
**Ventana mínima de anticipación (2 horas):** ni agendar ni cancelar se permiten a menos de 2 horas del inicio de la sesión. Los mensajes son distintos y el SPA puede mostrarlos tal cual:

- `POST /api/asesorias/asesorias/` → `400 {"detail": ["No puedes agendar una sesión con menos de 2 horas de anticipación."]}`
- `POST /api/asesorias/asesorias/{id}/cancelar/` → `400 {"detail": ["No puedes cancelar una sesión con menos de 2 horas de anticipación."]}`

`POST /api/asesorias/disponibilidades/{id}/desactivar/` **no** está sujeto a esta ventana: dar de baja un bloque cancela también las sesiones que arrancan en menos de 2 horas. Ver [ADR 0029](../decisions/0029-limites-cierre-y-propagacion-asesorias.md) y [deuda técnica 0003](../technical-debt/0003-sin-limites-uso-asesorias.md).
```

- [ ] **Step 9: Correr la suite de `asesorias` completa**

Run: `uv run manage.py test asesorias -v 2`
Expected: PASS, sin fallos.

- [ ] **Step 10: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/tests/ docs/development/api-frontend.md
git commit -m "$(cat <<'EOF'
[feat][backend] rechazar cancelar una asesoría con menos de 2 horas de anticipación

- Agregar el parámetro keyword-only forzar a Asesoria.cancelar()
- Pasar forzar=True desde Disponibilidad.desactivar(): la baja de un horario
  por parte del asesor sí puede cancelar dentro de la ventana
- Mover los tests de cancelación de CicloDeVidaAsesoriaApiTests a una sesión futura
- Documentar ambos mensajes de error en api-frontend.md

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 3: Tarea `cerrar_sesiones_vencidas`

**Files:**
- Modify: `backend/asesorias/tasks.py`
- Create: `backend/asesorias/tests/test_cierre_automatico.py`

**Interfaces:**
- Consumes: `DURACION_SESION` y `Asesoria.marcar_asistencia()` (Task 1).
- Produces: `asesorias.tasks.cerrar_sesiones_vencidas() -> int` (número de sesiones cerradas). Nombre registrado en Celery: `"asesorias.tasks.cerrar_sesiones_vencidas"`.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/asesorias/tests/test_cierre_automatico.py`:

```python
import datetime

from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.tasks import cerrar_sesiones_vencidas
from carreras.models import Area, Carrera
from materias.models import Materia


class CerrarSesionesVencidasTests(TestCase):
    """Deuda 0004: una sesión agendada cuya hora ya pasó sin que el asesor
    marque asistencia se cierra sola como `realizada` con `asistio=False`."""

    def setUp(self):
        self.area = Area.objects.create(nombre="Area cierre")
        self.carrera = Carrera.objects.create(clave=811, nombre="Carrera Cierre", area=self.area)
        self.materia = Materia.objects.create(
            clave="1811", nombre="Álgebra Cierre", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.asesor_user = User.objects.create_user(email="asesor.cierre@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12399")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.alumno_user = User.objects.create_user(email="alumno.cierre@ciencias.unam.mx", password="x")
        self.alumno = crear_alumno(
            user=self.alumno_user, numero_cuenta="312399999", carrera=self.carrera, generacion=2023,
        )
        self.contador_bloques = 0

    def _crear_asesoria(self, fecha, hora, estado="agendada", asistio=None):
        """Cada sesión vive en su propio registro/bloque: los UniqueConstraint
        (asesor, semestre) y (registro, dia_semana, hora_inicio) impiden
        reusarlos. Las claves de semestre "90001", "90002"… son ficticias a
        propósito: aquí solo sirven para desambiguar registros."""
        self.contador_bloques += 1
        registro = RegistroAsesor.objects.create(
            asesor=self.asesor, semestre=f"9000{self.contador_bloques}",
        )
        disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=fecha.weekday(), hora_inicio=hora,
            formato="virtual", liga_virtual="https://meet.example.com/c",
        )
        return Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=fecha, hora_inicio=hora,
            formato="virtual", liga_virtual="https://meet.example.com/c",
            estado=estado, asistio=asistio,
        )

    def test_una_sesion_de_ayer_sin_marcar_se_cierra_como_no_asistida(self):
        ayer = timezone.localdate() - datetime.timedelta(days=1)
        asesoria = self._crear_asesoria(ayer, datetime.time(10, 0))

        cerradas = cerrar_sesiones_vencidas()

        self.assertEqual(cerradas, 1)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "realizada")
        self.assertIs(asesoria.asistio, False)

    def test_una_sesion_futura_no_se_toca(self):
        manana = timezone.localdate() + datetime.timedelta(days=1)
        asesoria = self._crear_asesoria(manana, datetime.time(10, 0))

        cerradas = cerrar_sesiones_vencidas()

        self.assertEqual(cerradas, 0)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "agendada")
        self.assertIsNone(asesoria.asistio)

    def test_una_sesion_que_apenas_empezo_no_se_toca(self):
        """Margen de DURACION_SESION: el asesor todavía está en la sesión."""
        hace_diez_minutos = timezone.localtime() - datetime.timedelta(minutes=10)
        asesoria = self._crear_asesoria(
            hace_diez_minutos.date(), hace_diez_minutos.time().replace(microsecond=0),
        )

        cerradas = cerrar_sesiones_vencidas()

        self.assertEqual(cerradas, 0)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "agendada")

    def test_una_sesion_ya_marcada_no_se_toca(self):
        ayer = timezone.localdate() - datetime.timedelta(days=1)
        asesoria = self._crear_asesoria(
            ayer, datetime.time(11, 0), estado="realizada", asistio=True,
        )

        cerradas = cerrar_sesiones_vencidas()

        self.assertEqual(cerradas, 0)
        asesoria.refresh_from_db()
        self.assertIs(asesoria.asistio, True)

    def test_una_sesion_cancelada_no_se_toca(self):
        ayer = timezone.localdate() - datetime.timedelta(days=1)
        asesoria = self._crear_asesoria(ayer, datetime.time(12, 0), estado="cancelada")

        cerradas = cerrar_sesiones_vencidas()

        self.assertEqual(cerradas, 0)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "cancelada")
        self.assertIsNone(asesoria.asistio)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run manage.py test asesorias.tests.test_cierre_automatico -v 2`
Expected: FAIL — `ImportError: cannot import name 'cerrar_sesiones_vencidas' from 'asesorias.tasks'`.

- [ ] **Step 3: Implementar la tarea**

En `backend/asesorias/tasks.py`, reemplazar la cabecera de imports:

```python
from celery import shared_task
from django.core.mail import send_mail
```

por:

```python
from celery import shared_task
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
```

Y agregar al final del archivo:

```python
@shared_task
def cerrar_sesiones_vencidas():
    """Cierra las sesiones agendadas que ya terminaron sin que el asesor
    marcara asistencia: quedan `realizada` con `asistio=False` (deuda 0004).

    El corte es `inicio + DURACION_SESION <= ahora`, no `inicio <= ahora`: una
    sesión que apenas arrancó sigue en curso y el asesor todavía puede marcar
    asistencia. El criterio es el complemento exacto de
    `Disponibilidad.sesiones_futuras()`, desplazado por ese margen.

    La corre Celery Beat cada 15 minutos (`CELERY_BEAT_SCHEDULE`). Devuelve
    cuántas cerró, para que el resultado quede en los logs del worker.
    """
    from asesorias.models import DURACION_SESION, Asesoria

    limite = timezone.localtime() - DURACION_SESION
    vencidas = Asesoria.objects.filter(estado="agendada").filter(
        Q(fecha__lt=limite.date())
        | Q(fecha=limite.date(), hora_inicio__lte=limite.time())
    )
    cerradas = 0
    for asesoria in vencidas:
        asesoria.marcar_asistencia(False)
        cerradas += 1
    return cerradas
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `uv run manage.py test asesorias.tests.test_cierre_automatico -v 2`
Expected: PASS (5 tests).

- [ ] **Step 5: Correr la suite de `asesorias` completa**

Run: `uv run manage.py test asesorias -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/tasks.py backend/asesorias/tests/test_cierre_automatico.py
git commit -m "$(cat <<'EOF'
[feat][backend] cerrar automáticamente las sesiones vencidas sin marcar

- Agregar la tarea cerrar_sesiones_vencidas a asesorias/tasks.py
- Cerrar como realizada/asistio=False solo las sesiones que ya terminaron
  (inicio + DURACION_SESION), no las que apenas arrancaron

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 4: Infraestructura de Celery Beat (`django-celery-beat`, schedule, contenedores, runbook)

**Files:**
- Modify: `backend/pyproject.toml`, `backend/uv.lock` (los actualiza `uv add`)
- Modify: `backend/config/settings/base.py`
- Modify: `docker-compose.dev.yml`
- Modify: `docker-compose.prod.yml`
- Modify: `docs/development/despliegue-produccion.md`

**Interfaces:**
- Consumes: `asesorias.tasks.cerrar_sesiones_vencidas` (Task 3).
- Produces: `settings.CELERY_BEAT_SCHEDULE["cerrar-sesiones-vencidas"]`; servicio de compose `celery-beat`.

- [ ] **Step 1: Agregar la dependencia**

Desde `backend/`:

```bash
uv add django-celery-beat
```

Actualiza `pyproject.toml` (nueva entrada en `dependencies`) y `uv.lock`. No fijar la versión a mano — `uv` resuelve la compatible con Django 6.

Si `uv` no encuentra ninguna versión compatible con `django>=6.0.7`, instalar desde el repositorio upstream en vez de bajar la versión de Django:

```bash
uv add "django-celery-beat @ git+https://github.com/celery/django-celery-beat@main"
```

y anotarlo en el ADR del Task 7 (sección `Consequences`) como dependencia pinneada a `main`.

- [ ] **Step 2: Registrar la app y el schedule en settings**

En `backend/config/settings/base.py`, reemplazar el bloque de imports:

```python
from datetime import timedelta
from pathlib import Path

import environ
import sys
```

por:

```python
from datetime import timedelta
from pathlib import Path

import environ
import sys
from celery.schedules import crontab
```

Reemplazar `THIRD_PARTY_APPS`:

```python
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "dj_rest_auth",
]
```

por:

```python
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "dj_rest_auth",
    # Scheduler de Celery Beat respaldado por la base de datos: el contenedor
    # celery-beat no necesita un volumen para su archivo de estado, y la SAE
    # puede ajustar la frecuencia desde el admin sin redeploy (ADR 0029).
    "django_celery_beat",
]
```

Y reemplazar el bloque final de Celery:

```python
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = "test" in sys.argv
CELERY_TASK_EAGER_PROPAGATES = True
```

por:

```python
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = "test" in sys.argv
CELERY_TASK_EAGER_PROPAGATES = True

# Cada 15 minutos: el cierre de sesiones vencidas no es sensible al segundo
# (una sesión "huérfana" puede esperar un cuarto de hora) y a esa frecuencia el
# barrido es una sola consulta indexada por estado (ADR 0029, deuda 0004).
# DatabaseScheduler siembra esta entrada en la base al arrancar beat.
CELERY_BEAT_SCHEDULE = {
    "cerrar-sesiones-vencidas": {
        "task": "asesorias.tasks.cerrar_sesiones_vencidas",
        "schedule": crontab(minute="*/15"),
    },
}
```

- [ ] **Step 3: Verificar settings y migraciones**

Run: `uv run manage.py check`
Expected: `System check identified no issues`.

Run: `uv run manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

Run: `uv run manage.py migrate`
Expected: aplica las migraciones de `django_celery_beat` (`Applying django_celery_beat.0001_initial... OK`, etc.).

Sin Postgres local, desde la raíz del repo: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate`.

- [ ] **Step 4: Agregar el servicio `celery-beat` a `docker-compose.dev.yml`**

En `docker-compose.dev.yml`, insertar este servicio entre `celery-worker` y `frontend`:

```yaml
  celery-beat:
    build:
      context: ./backend
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    env_file:
      - ./backend/.env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.dev
      DATABASE_URL: postgres://atenea:atenea@postgres:5432/atenea
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

- [ ] **Step 5: Agregar el servicio `celery-beat` a `docker-compose.prod.yml`**

En `docker-compose.prod.yml`, insertar este servicio entre `celery-worker` y `frontend`:

```yaml
  celery-beat:
    build:
      context: ./backend
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file:
      - ./backend/.env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
```

- [ ] **Step 6: Verificar que ambos compose parsean**

Run (desde la raíz del repo): `docker compose -f docker-compose.dev.yml config -q && docker compose -f docker-compose.prod.yml config -q`
Expected: sin salida y exit 0.

- [ ] **Step 7: Documentar el contenedor en el runbook de producción**

En `docs/development/despliegue-produccion.md`:

**(a)** En el diagrama de topología, reemplazar la línea:

```
                                                   atenea-worker (Celery) ── atenea-redis
```

por:

```
                                    atenea-worker + atenea-beat (Celery) ── atenea-redis
```

**(b)** En la sección `## 2. Servicios en services/docker-compose.yml`, reemplazar el encabezado:

```markdown
Agregar tres servicios sobre `sae-network` (`atenea-db` y `atenea-redis` ya existen):
```

por:

```markdown
Agregar cuatro servicios sobre `sae-network` (`atenea-db` y `atenea-redis` ya existen):
```

**(c)** En esa misma sección, insertar este bloque YAML entre `atenea-worker` y `atenea-frontend`:

```yaml
  atenea-beat:
    image: ghcr.io/hyfi06/atenea-backend:latest   # misma imagen
    # Scheduler en base de datos (django-celery-beat, ADR 0029): sin volumen de
    # estado. NO pasa por migrate (ver entrypoint) — migra atenea-backend.
    command: >
      celery -A config beat -l info
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.prod
      - DJANGO_SECRET_KEY=${ATENEA_SECRET_KEY}
      - DJANGO_ALLOWED_HOSTS=atenea.unam.dev
      - DATABASE_URL=postgres://atenea:${ATENEA_DB_PASSWORD}@atenea-db:5432/atenea
      - REDIS_URL=redis://atenea-redis:6379/0
      - FRONTEND_URL=https://atenea.unam.dev
      - GOOGLE_OAUTH_CLIENT_ID=${ATENEA_GOOGLE_CLIENT_ID}
      - GOOGLE_OAUTH_CLIENT_SECRET=${ATENEA_GOOGLE_CLIENT_SECRET}
    networks: [sae-network]
    depends_on: [atenea-db, atenea-redis]
```

> `atenea-beat` **no** necesita las variables de correo: solo encola tareas, no envía correo. Quien envía es `atenea-worker`.
> Debe correr **una sola réplica**: dos schedulers duplicarían cada ejecución programada.

**(d)** En el bloque de restart policies de esa misma sección, reemplazar:

```yaml
  atenea-backend:
    restart: unless-stopped
  atenea-worker:
    restart: unless-stopped
  atenea-frontend:
    restart: unless-stopped
```

por:

```yaml
  atenea-backend:
    restart: unless-stopped
  atenea-worker:
    restart: unless-stopped
  atenea-beat:
    restart: unless-stopped
  atenea-frontend:
    restart: unless-stopped
```

**(e)** En la sección `## 6. Primer despliegue`, reemplazar:

```bash
make logs svc=atenea-worker    # debe decir "ready."
```

por:

```bash
make logs svc=atenea-worker    # debe decir "ready."
make logs svc=atenea-beat      # debe listar "cerrar-sesiones-vencidas" en el schedule
```

**(f)** En la sección `## 8. Verificación`, agregar como último bullet:

```markdown
- `make logs svc=atenea-beat` muestra `Scheduler: Sending due task cerrar-sesiones-vencidas` a más tardar 15 minutos después del arranque.
```

- [ ] **Step 8: Correr la suite completa del backend**

Run: `uv run manage.py test -v 1`
Expected: PASS (las tablas de `django_celery_beat` se crean en la base de test sin intervención).

- [ ] **Step 9: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/config/settings/base.py docker-compose.dev.yml docker-compose.prod.yml docs/development/despliegue-produccion.md
git commit -m "$(cat <<'EOF'
[feat][backend] agregar Celery Beat para la tarea de cierre de sesiones vencidas

- Agregar la dependencia django-celery-beat y registrarla en THIRD_PARTY_APPS
- Programar cerrar_sesiones_vencidas cada 15 minutos en CELERY_BEAT_SCHEDULE
- Agregar el servicio celery-beat a docker-compose.dev.yml y .prod.yml
- Documentar el contenedor atenea-beat en el runbook de despliegue

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 5: `Disponibilidad.resincronizar_sesiones_futuras()` + notificación por correo

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/tasks.py`
- Test: `backend/asesorias/tests/test_disponibilidad.py`

**Interfaces:**
- Consumes: `Disponibilidad.sesiones_futuras()` (ya existente).
- Produces:
  - `Disponibilidad.resincronizar_sesiones_futuras() -> list[Asesoria]`
  - `asesorias.tasks.enviar_notificacion_resincronizacion(asesoria_id: int) -> None`

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `backend/asesorias/tests/test_disponibilidad.py` (el archivo ya importa `datetime`, `TestCase`, `timezone`, `Asesoria`, `Disponibilidad`; agregar el import de `patch` en la cabecera del archivo, ver Step 2):

```python
class ResincronizarSesionesFuturasTests(SesionesFuturasTests):
    """Deuda 0005: corregir un dato del bloque se propaga a las sesiones ya
    agendadas que todavía no ocurren."""

    def test_actualiza_el_snapshot_de_las_sesiones_futuras(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        actualizadas = self.disponibilidad.resincronizar_sesiones_futuras()

        self.assertEqual(actualizadas, [futura])
        futura.refresh_from_db()
        self.assertEqual(futura.liga_virtual, "https://meet.example.com/CORREGIDA")

    def test_propaga_tambien_formato_y_ubicacion(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        self.disponibilidad.formato = "presencial"
        self.disponibilidad.ubicacion = "Salón 25, Yelizcalli"
        self.disponibilidad.liga_virtual = ""
        self.disponibilidad.save()
        self.disponibilidad.resincronizar_sesiones_futuras()

        futura.refresh_from_db()
        self.assertEqual(futura.formato, "presencial")
        self.assertEqual(futura.ubicacion, "Salón 25, Yelizcalli")
        self.assertEqual(futura.liga_virtual, "")

    def test_no_toca_la_hora_de_inicio(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        hora_original = futura.hora_inicio

        self.disponibilidad.hora_inicio = datetime.time(15, 30)
        self.disponibilidad.save()
        self.disponibilidad.resincronizar_sesiones_futuras()

        futura.refresh_from_db()
        self.assertEqual(futura.hora_inicio, hora_original)

    def test_no_toca_sesiones_pasadas_ni_canceladas(self):
        hoy = timezone.localdate()
        pasada = self._crear_asesoria(hoy - datetime.timedelta(days=7))
        cancelada = self._crear_asesoria(
            hoy + datetime.timedelta(days=14), estado="cancelada",
        )

        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        actualizadas = self.disponibilidad.resincronizar_sesiones_futuras()

        self.assertEqual(actualizadas, [])
        pasada.refresh_from_db()
        self.assertEqual(pasada.liga_virtual, "https://meet.example.com/x")
        cancelada.refresh_from_db()
        self.assertEqual(cancelada.liga_virtual, "https://meet.example.com/x")

    @patch("asesorias.tasks.enviar_notificacion_resincronizacion.delay")
    def test_encola_una_notificacion_por_sesion_afectada(self, mock_delay):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        self._crear_asesoria(hoy - datetime.timedelta(days=7))

        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        with self.captureOnCommitCallbacks(execute=True):
            self.disponibilidad.resincronizar_sesiones_futuras()

        mock_delay.assert_called_once_with(futura.id)
```

- [ ] **Step 2: Agregar el import de `patch` al archivo de tests**

En `backend/asesorias/tests/test_disponibilidad.py`, reemplazar la cabecera:

```python
import datetime

from django.core.exceptions import ValidationError
```

por:

```python
import datetime
from unittest.mock import patch

from django.core.exceptions import ValidationError
```

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad.ResincronizarSesionesFuturasTests -v 2`
Expected: FAIL — `AttributeError: 'Disponibilidad' object has no attribute 'resincronizar_sesiones_futuras'`.

- [ ] **Step 4: Implementar la tarea de correo**

Agregar al final de `backend/asesorias/tasks.py`:

```python
@shared_task
def enviar_notificacion_resincronizacion(asesoria_id: int):
    """Avisa al alumno y al asesor que cambiaron los datos de contacto de una
    sesión ya agendada (deuda 0005). Fecha y hora no cambian nunca por esta
    vía, y el correo lo dice explícitamente para que nadie llegue a destiempo.
    """
    from asesorias.models import Asesoria

    asesoria = Asesoria.objects.select_related(
        "alumno__user", "disponibilidad__registro__asesor__user", "materia"
    ).get(id=asesoria_id)
    asesor_email = asesoria.disponibilidad.registro.asesor.user.email
    if asesoria.formato == "virtual":
        detalle = f"Liga de la sesión: {asesoria.liga_virtual}"
    else:
        detalle = f"Ubicación de la sesión: {asesoria.ubicacion}"
    send_mail(
        subject=(
            f"Cambio en los datos de tu asesoría — {asesoria.materia.nombre} — {asesoria.fecha}"
        ),
        message=(
            f"El asesor actualizó los datos de la asesoría de {asesoria.materia.nombre} "
            f"del {asesoria.fecha} a las {asesoria.hora_inicio}. La fecha y la hora NO cambian. "
            f"Formato: {asesoria.get_formato_display()}. {detalle}"
        ),
        from_email=None,
        recipient_list=[asesoria.alumno.user.email, asesor_email],
    )
```

- [ ] **Step 5: Implementar el método del modelo**

En `backend/asesorias/models.py`, dentro de la clase `Disponibilidad`, insertar este método justo después de `desactivar()` y antes de `__str__`:

```python
    def resincronizar_sesiones_futuras(self):
        """Reemplaza el snapshot de contacto de las sesiones futuras de este
        bloque con los valores actuales. Devuelve la lista de las actualizadas.

        Cierra la deuda 0005: el snapshot de `formato`/`ubicacion`/
        `liga_virtual` que `Asesoria` congela al agendar deja de ser
        irreparable cuando el asesor corrige un typo (una liga de Zoom mal
        escrita, por ejemplo).

        NO toca `hora_inicio`: mover la hora de una sesión ya agendada es otra
        operación, con otras consecuencias para el alumno, y está fuera de
        alcance. El criterio de qué sesiones alcanza es `sesiones_futuras()`,
        el mismo que usan el endpoint de consulta y `desactivar()`.
        """
        from asesorias.tasks import enviar_notificacion_resincronizacion

        with transaction.atomic():
            sesiones = list(self.sesiones_futuras())
            for asesoria in sesiones:
                asesoria.formato = self.formato
                asesoria.ubicacion = self.ubicacion
                asesoria.liga_virtual = self.liga_virtual
                asesoria.save(
                    update_fields=["formato", "ubicacion", "liga_virtual", "actualizado_en"]
                )
                transaction.on_commit(
                    lambda asesoria_id=asesoria.id: (
                        enviar_notificacion_resincronizacion.delay(asesoria_id)
                    )
                )
        return sesiones
```

- [ ] **Step 6: Correr el test y verificar que pasa**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad.ResincronizarSesionesFuturasTests -v 2`
Expected: PASS (5 tests).

- [ ] **Step 7: Correr la suite de `asesorias` completa**

Run: `uv run manage.py test asesorias -v 2`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/tasks.py backend/asesorias/tests/test_disponibilidad.py
git commit -m "$(cat <<'EOF'
[feat][backend] propagar los datos de una Disponibilidad a sus sesiones futuras

- Agregar Disponibilidad.resincronizar_sesiones_futuras(), que reemplaza el
  snapshot de formato/ubicacion/liga_virtual sin tocar hora_inicio
- Agregar la tarea enviar_notificacion_resincronizacion para avisar al alumno

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 6: Endpoint `POST /api/asesorias/disponibilidades/{id}/resincronizar/`

**Files:**
- Modify: `backend/asesorias/views.py`
- Modify: `docs/development/api-frontend.md`
- Test: `backend/asesorias/tests/test_api_disponibilidad.py`

**Interfaces:**
- Consumes: `Disponibilidad.resincronizar_sesiones_futuras()` (Task 5); `SesionFuturaSerializer` y `DisponibilidadViewSet` (ya existentes).
- Produces: `POST /api/asesorias/disponibilidades/{id}/resincronizar/` → `200 {"sesiones_actualizadas": int, "sesiones": [{id, fecha, hora_inicio, alumno_nombre, materia_nombre}]}`.

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `backend/asesorias/tests/test_api_disponibilidad.py`:

```python
class ResincronizarApiTests(SesionesFuturasApiTests):
    """Deuda 0005: el asesor dueño corrige su bloque y propaga el cambio a las
    sesiones ya agendadas que aún no ocurren."""

    def test_asesor_dueno_resincroniza_y_recibe_el_resumen(self):
        futura = self._crear_asesoria_futura(7)
        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/resincronizar/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sesiones_actualizadas"], 1)
        self.assertEqual(response.data["sesiones"][0]["id"], futura.id)
        futura.refresh_from_db()
        self.assertEqual(futura.liga_virtual, "https://meet.example.com/CORREGIDA")

    def test_no_toca_la_hora_de_inicio(self):
        futura = self._crear_asesoria_futura(7)
        hora_original = futura.hora_inicio
        self.disponibilidad.hora_inicio = datetime.time(15, 30)
        self.disponibilidad.save()
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/resincronizar/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        futura.refresh_from_db()
        self.assertEqual(futura.hora_inicio, hora_original)

    def test_bloque_sin_sesiones_futuras_devuelve_cero(self):
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/resincronizar/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"sesiones_actualizadas": 0, "sesiones": []})

    def test_resincronizar_bloque_ajeno_devuelve_403(self):
        # Nombre distinto al `test_bloque_ajeno_devuelve_403` de la clase padre:
        # repetirlo lo sobrescribiría y se perdería la cobertura de
        # `sesiones-futuras/`.
        self.client.force_authenticate(user=self.otro_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/resincronizar/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_alumno_no_puede_resincronizar(self):
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/resincronizar/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run manage.py test asesorias.tests.test_api_disponibilidad.ResincronizarApiTests -v 2`
Expected: FAIL — 404 en vez de 200/403 (la ruta no existe).

- [ ] **Step 3: Implementar la acción del viewset**

En `backend/asesorias/views.py`, dentro de `DisponibilidadViewSet`, insertar este método justo después de la acción `desactivar`:

```python
    @action(detail=True, methods=["post"])
    def resincronizar(self, request, pk=None):
        """Propaga formato/ubicacion/liga_virtual del bloque a sus sesiones
        futuras (deuda 0005).

        Vive en el viewset del asesor y no en un `Admin*View` con
        `EsMiembroSAE`: es el asesor corrigiendo un dato suyo, no una
        intervención administrativa. `get_object()` ya aplica
        `EsDuenoDelRegistro`, así que un bloque ajeno da 403.
        """
        disponibilidad = self.get_object()
        sesiones = disponibilidad.resincronizar_sesiones_futuras()
        return Response({
            "sesiones_actualizadas": len(sesiones),
            "sesiones": SesionFuturaSerializer(sesiones, many=True).data,
        })
```

No hay cambios en `urls.py`: el `DefaultRouter` ya registra `disponibilidades` y genera la ruta a partir del nombre del método.

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `uv run manage.py test asesorias.tests.test_api_disponibilidad.ResincronizarApiTests -v 2`
Expected: PASS (5 tests).

- [ ] **Step 5: Documentar el endpoint en `api-frontend.md`**

En `docs/development/api-frontend.md`, insertar esta fila en la tabla de `asesorias`, justo debajo de la fila de `desactivar/`:

```markdown
| `POST` | `/api/asesorias/disponibilidades/{id}/resincronizar/` | body vacío → `{"sesiones_actualizadas": n, "sesiones": [{id, fecha, hora_inicio, alumno_nombre, materia_nombre}]}`. Copia `formato`, `ubicacion` y `liga_virtual` **actuales** del bloque a todas sus sesiones futuras y notifica por correo a los alumnos afectados. **No** toca `fecha` ni `hora_inicio`. Solo el asesor dueño (`403` si el bloque es ajeno) — ver [deuda técnica 0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md) |
```

- [ ] **Step 6: Correr la suite completa del backend**

Run: `uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/tests/test_api_disponibilidad.py docs/development/api-frontend.md
git commit -m "$(cat <<'EOF'
[feat][backend] exponer POST disponibilidades/{id}/resincronizar/

- Agregar la acción resincronizar al DisponibilidadViewSet, restringida al
  asesor dueño del bloque
- Documentar el contrato del endpoint en api-frontend.md

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 7: ADR 0029 y cierre de las deudas 0003, 0004 y 0005

**Files:**
- Create: `docs/decisions/0029-limites-cierre-y-propagacion-asesorias.md`
- Modify: `docs/technical-debt/0003-sin-limites-uso-asesorias.md`
- Modify: `docs/technical-debt/0004-sin-cierre-automatico-recordatorios.md`
- Modify: `docs/technical-debt/0005-editar-disponibilidad-no-propaga.md`
- Modify: `docs/technical-debt/README.md`

**Interfaces:**
- Consumes: todo lo implementado en Tasks 1–6. No produce código.

- [ ] **Step 1: Crear el ADR**

Crear `docs/decisions/0029-limites-cierre-y-propagacion-asesorias.md`:

```markdown
# 0029 — Ventana de anticipación, cierre automático y resincronización en Asesorías

**Status:** Accepted
**Date:** 2026-08-19

## Context

Tres deudas técnicas de la app `asesorias` comparten modelo (`Asesoria`,
`Disponibilidad`) e infraestructura (Celery), y se atacan juntas:

- [0003](../technical-debt/0003-sin-limites-uso-asesorias.md) — sin límites de
  uso: un alumno podía agendar o cancelar hasta el segundo anterior a la sesión,
  dejando al asesor sin margen para enterarse.
- [0004](../technical-debt/0004-sin-cierre-automatico-recordatorios.md) — una
  sesión `agendada` cuya hora pasó sin que el asesor marcara asistencia se
  quedaba así indefinidamente. La deuda señalaba dos bloqueos: faltaba Celery
  Beat, y faltaba la decisión de producto sobre qué hacer con una sesión
  abandonada.
- [0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md) — `Asesoria`
  congela un snapshot de `formato`/`ubicacion`/`liga_virtual` al agendar, y
  corregir un typo en la `Disponibilidad` (una liga de Zoom mal escrita) no
  llegaba a las sesiones ya agendadas.

El proyecto ya tenía `celery-worker` pero nunca un proceso `beat`, aunque el
[ADR 0004](0004-docker-topology.md) lo preveía "solo cuando existan tareas
programadas". Este es ese momento.

## Decision

1. **Ventana mínima de anticipación de 2 horas.** `Asesoria.clean()` rechaza
   agendar y `Asesoria.cancelar()` rechaza cancelar cuando falta menos de
   `VENTANA_MINIMA_ANTICIPACION = timedelta(hours=2)` para el inicio. Los dos
   mensajes de error son distintos y están redactados para mostrarse tal cual en
   el SPA. `Asesoria.momento_inicio` es la única fuente que combina `fecha` y
   `hora_inicio` en un datetime aware; también la usa `marcar_asistencia()`.
2. **`cancelar(..., forzar=True)` salta la ventana**, y es lo que pasa
   `Disponibilidad.desactivar()`. Dar de baja un horario no es el alumno
   cancelando de último minuto: es el asesor invalidando el bloque completo, y
   bloquearlo lo dejaría sin forma de darlo de baja. La regla vive en un solo
   lugar (`cancelar()`) y el bypass es explícito y testeado, no accidental.
3. **Una sesión vencida se cierra como `realizada` con `asistio=False`**,
   reusando `marcar_asistencia(False)`, que ya modela esa transición. No se
   agrega un estado "vencida": el dato que la SAE necesita es de asistencia, y
   `asistio=False` ya lo expresa. Lo hace la tarea
   `asesorias.tasks.cerrar_sesiones_vencidas`.
4. **El corte del cierre es `inicio + DURACION_SESION <= ahora`** (30 minutos),
   no `inicio <= ahora`: una sesión que apenas arrancó sigue en curso y el asesor
   todavía puede marcar asistencia. `DURACION_SESION` es la misma constante que
   define `Disponibilidad.hora_fin`.
5. **Celery Beat con `django-celery-beat` (`DatabaseScheduler`)**, en un
   contenedor propio (`celery-beat` en dev/prod, `atenea-beat` en `services/`).
   Frecuencia: `crontab(minute="*/15")`. El scheduler en base de datos evita un
   volumen de estado para el contenedor y deja la frecuencia ajustable desde el
   admin sin redeploy. Debe correr **una sola réplica**.
6. **`POST /api/asesorias/disponibilidades/{id}/resincronizar/`** copia
   `formato`, `ubicacion` y `liga_virtual` actuales del bloque a todas las
   sesiones de `sesiones_futuras()` y encola
   `enviar_notificacion_resincronizacion` por cada una. **No** toca
   `hora_inicio`. Vive en el `DisponibilidadViewSet` del asesor, restringido al
   dueño del registro, no en un `Admin*View` con `EsMiembroSAE`: es el asesor
   corrigiendo un dato suyo, no una intervención administrativa.

## Consequences

- El SPA debe mostrar los dos mensajes nuevos de `400` y, idealmente, dejar de
  ofrecer los botones de agendar/cancelar dentro de la ventana. El contrato está
  en [`api-frontend.md`](../development/api-frontend.md); la UI queda fuera del
  alcance de este ADR.
- Una tercera imagen-proceso corre en producción (misma imagen que backend y
  worker, distinto `command`). El runbook
  ([`despliegue-produccion.md`](../development/despliegue-produccion.md)) lo
  documenta junto con la verificación de logs.
- `django_celery_beat` agrega tablas propias (`migrate` obligatorio antes de
  arrancar `beat`). Migra `atenea-backend`; `atenea-beat` pasa `command:` y por
  tanto no migra (ver `docker-entrypoint.sh`).
- Los reportes de asistencia de la SAE dejan de depender de que el asesor marque
  manualmente: una sesión vencida sin marcar aparece como no asistida a más
  tardar 15 minutos después de terminar. Si un asesor marca tarde, ya no puede —
  `marcar_asistencia()` solo aplica sobre `estado == "agendada"` en la práctica,
  porque el cierre ya la movió a `realizada`.
- Las deudas 0003 y 0004 quedan **parcialmente** resueltas; 0005 queda resuelta.

## Alternatives considered

- **Meter la ventana de 2 horas en el serializer en vez del modelo:** dejaría
  `Disponibilidad.desactivar()` (que no pasa por el serializer) sin la regla y
  duplicaría la lógica entre agendar y cancelar. Rechazada: la validación de
  negocio de esta app ya vive en el modelo.
- **Un flag global tipo `saltar_validaciones` en vez de `forzar` en
  `cancelar()`:** más ancho de lo necesario y difícil de auditar. `forzar` es
  keyword-only, con un único call site.
- **Estado nuevo `vencida` en `ESTADOS_ASESORIA`:** obligaría a tocar todos los
  filtros, serializers y pantallas que hoy discriminan por estado, para un dato
  que `realizada` + `asistio=False` ya expresa.
- **Celery Beat con el scheduler de archivo (`celerybeat-schedule`) en vez de
  `django-celery-beat`:** una dependencia menos, pero exige un volumen
  persistente para el contenedor y deja la frecuencia solo cambiable por
  redeploy.
- **Acción de `django.contrib.admin` en `DisponibilidadAdmin` para
  resincronizar:** el resto del área administrativa del proyecto usa vistas DRF
  dedicadas, no admin actions, y además el dueño natural de la operación es el
  asesor, que no entra al admin de Django.
- **Propagar también `hora_inicio`:** cambiar la hora de una sesión ya agendada
  es otra operación, con otras consecuencias para el alumno (puede dejar de
  poder asistir). Fuera de alcance.
- **Propagar automáticamente en el `PATCH` de la disponibilidad, sin endpoint
  aparte:** rompería el snapshot deliberado que motiva la deuda 0005 — no todo
  cambio del bloque debe alcanzar a las sesiones ya agendadas. Que sea una
  acción explícita mantiene la decisión en manos del asesor.
```

- [ ] **Step 2: Actualizar la deuda 0003**

Reemplazar el contenido completo de `docs/technical-debt/0003-sin-limites-uso-asesorias.md` por:

```markdown
# 0003 — Sin límites de uso en Asesorías

**Estado:** Parcialmente resuelta — 2026-08-19 ([ADR 0029](../decisions/0029-limites-cierre-y-propagacion-asesorias.md))
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

Un alumno puede agendar cualquier número de sesiones simultáneas y cancelar sin restricción de tiempo mínimo antes de la sesión ni límite de cancelaciones.

## Por qué era razonable

El MVP prioriza validar el flujo completo con usuarios reales antes de diseñar límites que podrían no corresponder al patrón de abuso real (si lo hay).

## Señal de revisión

Evidencia de abuso en producción (acaparamiento de horarios, cancelaciones sistemáticas de último minuto que dejan al asesor sin aviso).

## Cómo se resolvió (parcialmente)

La **restricción de tiempo mínimo** existe desde el 2026-08-19: ni agendar ni cancelar se permiten a menos de 2 horas del inicio de la sesión (`VENTANA_MINIMA_ANTICIPACION` en `asesorias/models.py`, validada en `Asesoria.clean()` y `Asesoria.cancelar()`). `Disponibilidad.desactivar()` se salta la ventana a propósito vía `cancelar(forzar=True)`: la baja de un horario por parte del asesor no es una cancelación de último minuto del alumno.

## Qué sigue pendiente

- **Límite de sesiones simultáneas por alumno** — sigue sin existir; un alumno puede acaparar todos los horarios de la ventana agendable.
- **Límite de cancelaciones** — sigue sin existir; un alumno puede cancelar y reagendar indefinidamente mientras respete la ventana de 2 horas.

Ambos siguen esperando la misma señal de revisión de arriba: evidencia de abuso real en producción.
```

- [ ] **Step 3: Actualizar la deuda 0004**

Reemplazar el contenido completo de `docs/technical-debt/0004-sin-cierre-automatico-recordatorios.md` por:

```markdown
# 0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos

**Estado:** Parcialmente resuelta — 2026-08-19 ([ADR 0029](../decisions/0029-limites-cierre-y-propagacion-asesorias.md))
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

Una `Asesoria` en estado `agendada` cuya fecha ya pasó sin que el asesor marque asistencia se queda así indefinidamente — no hay tarea Celery Beat que la cierre. Tampoco hay recordatorio por email antes de la sesión, solo confirmación al agendar y notificación al cancelar.

## Por qué era razonable

Requiere Celery Beat (no solo tareas async puntuales) y una decisión de producto sobre qué hacer con una sesión "abandonada" (¿marcarla como no-asistida automáticamente? ¿dejarla pendiente?) que no estaba resuelta al diseñar el MVP.

## Señal de revisión

Cuando el volumen de sesiones "huérfanas" (agendadas, vencidas, sin marcar) sea alto en los reportes que use la SAE, o cuando se necesite el dato de asistencia agregado sin depender de que el asesor la marque manualmente.

## Cómo se resolvió (parcialmente)

El **cierre automático** existe desde el 2026-08-19. Se resolvieron los dos bloqueos que registraba esta deuda:

- **Celery Beat:** contenedor propio (`celery-beat` en `docker-compose.dev.yml`/`.prod.yml`, `atenea-beat` en el repo `services`), con `django-celery-beat` como `DatabaseScheduler`.
- **Decisión de producto:** una sesión vencida sin marcar pasa a `realizada` con `asistio=False`, reusando `marcar_asistencia(False)`. Lo hace `asesorias.tasks.cerrar_sesiones_vencidas`, programada cada 15 minutos, y solo alcanza sesiones que ya **terminaron** (`inicio + 30 min <= ahora`), no las que apenas arrancaron.

## Qué sigue pendiente

- **Recordatorios periódicos por email antes de la sesión** — siguen sin existir. `asesorias/tasks.py` solo manda confirmación al agendar, aviso al cancelar y aviso al resincronizar. Con Celery Beat ya en su lugar, el bloqueo de infraestructura desapareció: lo único pendiente es la decisión de producto sobre cuántos recordatorios y con cuánta anticipación. No se abrió un ítem de deuda nuevo para esto; se sigue rastreando aquí.
```

- [ ] **Step 4: Actualizar la deuda 0005**

Reemplazar el contenido completo de `docs/technical-debt/0005-editar-disponibilidad-no-propaga.md` por:

```markdown
# 0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas

**Estado:** Resuelta — 2026-08-19 ([ADR 0029](../decisions/0029-limites-cierre-y-propagacion-asesorias.md))
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

`Asesoria` guarda un snapshot de `formato`/`ubicacion`/`liga_virtual` al momento de agendar. Si el asesor corrige un dato erróneo en la `Disponibilidad` (ej. una liga de Zoom mal escrita) después de que ya hay sesiones agendadas sobre ese bloque, la corrección no llega a esas sesiones — hay que corregirlas una por una.

## Por qué era razonable

El snapshot es deliberado (una `Asesoria` no debe cambiar de lugar/formato retroactivamente sin que el alumno se entere), y el caso de "corregir un typo después de agendar" se juzgó infrecuente frente a la complejidad de decidir cuándo propagar y cuándo no.

## Señal de revisión

Si se vuelve un problema operativo recurrente, la opción más simple es un endpoint/acción de admin para "reemplazar el snapshot de una Asesoria agendada desde su Disponibilidad actual", no cambiar el modelo de snapshot en sí.

## Cómo se resolvió

Exactamente por la vía que anticipaba la señal de revisión, con el dueño ajustado: `POST /api/asesorias/disponibilidades/{id}/resincronizar/` (acción del `DisponibilidadViewSet`, restringida al asesor dueño del registro, no a `EsMiembroSAE` — es el asesor corrigiendo su propio dato). Copia `formato`, `ubicacion` y `liga_virtual` actuales del bloque a todas las sesiones de `Disponibilidad.sesiones_futuras()` y encola `enviar_notificacion_resincronizacion` por cada alumno afectado.

El modelo de snapshot **no cambió**: la propagación sigue siendo una acción explícita del asesor, no un efecto automático del `PATCH`. `hora_inicio` queda fuera a propósito — mover la hora de una sesión ya agendada es otra operación.
```

- [ ] **Step 5: Actualizar el índice de deuda técnica**

En `docs/technical-debt/README.md`, dentro de la sección `### Activa`, reemplazar estas tres líneas:

```markdown
- [0003 — Sin límites de uso en Asesorías](0003-sin-limites-uso-asesorias.md)
- [0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos](0004-sin-cierre-automatico-recordatorios.md)
- [0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas](0005-editar-disponibilidad-no-propaga.md)
```

por:

```markdown
- [0003 — Sin límites de uso en Asesorías](0003-sin-limites-uso-asesorias.md) — parcialmente resuelta 2026-08-19 (ventana de 2 horas lista; faltan límite de sesiones simultáneas y de cancelaciones)
- [0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos](0004-sin-cierre-automatico-recordatorios.md) — parcialmente resuelta 2026-08-19 (cierre automático listo; faltan los recordatorios periódicos)
```

Y en la sección `### Resuelta`, agregar al final:

```markdown
- [0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas](0005-editar-disponibilidad-no-propaga.md) — resuelta 2026-08-19
```

- [ ] **Step 6: Verificar que no quedaron enlaces rotos**

Run (desde la raíz del repo):

```bash
grep -rn "0029-limites-cierre-y-propagacion-asesorias.md" docs/ && ls docs/decisions/0029-limites-cierre-y-propagacion-asesorias.md
```

Expected: los enlaces aparecen en `docs/development/api-frontend.md` y en los tres ítems de deuda, y el archivo del ADR existe.

- [ ] **Step 7: Correr la suite completa del backend una última vez**

Run (desde `backend/`): `uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add docs/decisions/0029-limites-cierre-y-propagacion-asesorias.md docs/technical-debt/
git commit -m "$(cat <<'EOF'
[docs] registrar ADR 0029 y cerrar las deudas 0003, 0004 y 0005

- Agregar ADR 0029 (ventana de 2 horas, cierre automático, resincronización)
- Marcar 0003 y 0004 como parcialmente resueltas, con lo pendiente anotado
  dentro del mismo ítem
- Marcar 0005 como resuelta y moverla en el índice

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Verificación final

- [ ] Desde `backend/`: `uv run manage.py test -v 1` → PASS.
- [ ] Desde `backend/`: `uv run manage.py check` → sin issues.
- [ ] Desde `backend/`: `uv run manage.py makemigrations --check --dry-run` → `No changes detected`.
- [ ] Desde la raíz: `docker compose -f docker-compose.dev.yml config -q` → exit 0.
- [ ] Desde la raíz: `docker compose -f docker-compose.prod.yml config -q` → exit 0.
- [ ] Desde la raíz: `docker compose -f docker-compose.dev.yml up -d` y luego `docker compose -f docker-compose.dev.yml logs celery-beat` → el schedule lista `cerrar-sesiones-vencidas`.
- [ ] `git log --oneline` muestra 7 commits, uno por task.
