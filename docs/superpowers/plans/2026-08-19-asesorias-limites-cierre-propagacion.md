# Asesorías: límite de 2hrs y propagación de Disponibilidad — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar las deudas técnicas 0003 (parcial) y 0005 de la app `asesorias`: ventana mínima de 2 horas para agendar/cancelar, y endpoint de resincronización del snapshot de `Disponibilidad` hacia sus sesiones futuras. **Cierre automático de sesiones vencidas (deuda 0004) queda fuera de alcance** — decisión posterior a la exploración inicial, ver spec. **Addendum post-demo (Tasks 6–8, 2026-08-21):** bloques de `Disponibilidad` de 1 hora en vez de 30 min, y el wizard de agendado del alumno en `/asesorias/nueva` deja de pedir asesor primero (pasa a materia → día → bloque).

**Architecture:** Toda la regla de negocio vive en `asesorias/models.py` (`Asesoria.clean()`, `Asesoria.cancelar()`, `Disponibilidad.resincronizar_sesiones_futuras()`); las vistas solo traducen `ValidationError` → 400, siguiendo el patrón ya presente en `asesorias/views.py`. Sin cambios de esquema en modelos propios. El addendum (Tasks 6–8) reusa el mismo endpoint de búsqueda de disponibilidad sin su filtro opcional de asesor — no agrega superficie de API nueva — y toca `frontend/` únicamente en `features/asesorias`.

**Tech Stack:** Django 6 + DRF, Celery + Redis, PostgreSQL 16, Docker Compose, `uv` para dependencias (backend); React + TypeScript + Vite, TanStack Query, Vitest (frontend, Tasks 7–8).

**Spec:** `docs/superpowers/specs/2026-08-19-asesorias-limites-cierre-propagacion-design.md`

## Global Constraints

- **Tasks 1–5: 100% backend**, tal como se diseñaron el 2026-08-19 (ajustado: el cierre automático de la deuda 0004 quedó fuera de alcance, ver spec — las Tasks originales de esa pieza se eliminaron de este plan en vez de renumerarse como "canceladas"). **Tasks 6–8 son un addendum post-demo (2026-08-21, ver spec sección 3)** y sí tocan `frontend/` — la restricción original "no se toca frontend" solo aplicaba al alcance de las deudas 0003/0005. Los contratos de las Tasks 1–5 se documentan en `docs/development/api-frontend.md`.
- Comando de tests backend: desde `backend/`, `uv run manage.py test <ruta> -v 2`. Requiere Postgres. Sin Postgres local: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test <ruta> -v 2` (desde la raíz del repo).
- Comando de tests frontend (Tasks 7–8): desde `frontend/`, `npm test` (Vitest). Lint: `npm run lint` (oxlint). Build: `npm run build` (`tsc -b && vite build`).
- Idioma del código, docstrings, comentarios y mensajes de error: **español**. Encabezados de ADR en inglés (`Context`/`Decision`/`Consequences`/`Alternatives considered`), cuerpo en español — igual que `docs/decisions/0028-*.md`.
- Formato de commit: `[type][scope] resumen` + lista de cambios + `Signed-off-by`. Ver `docs/development/commit-conventions.md`.
- Errores de negocio del modelo se propagan como `{"detail": ["mensaje"]}` (lista), convención ya vigente.
- **Valores fijados por este plan** (el spec los dejaba abiertos):
  - Ventana mínima de anticipación: **2 horas** — `VENTANA_MINIMA_ANTICIPACION = datetime.timedelta(hours=2)`.
  - Duración de sesión / bloque: **1 hora** (ajustado por el addendum de la Task 6 — antes 30 min) — `DURACION_SESION = datetime.timedelta(hours=1)`. Fija `Disponibilidad.hora_fin`.
  - Rejilla de `Disponibilidad.hora_inicio`: **solo horas en punto** (ajustado por la Task 6 — antes `:00`/`:30`); `hora_inicio.minute != 0` es inválido.
  - Parámetro de bypass en `cancelar()`: **keyword-only `forzar: bool = False`**, en español como el resto de la firma (`usuario`, `motivo`).
  - Notificación de resincronización: **tarea nueva** `enviar_notificacion_resincronizacion(asesoria_id)` en `asesorias/tasks.py` (no se extiende `enviar_notificacion_cancelacion`: distinto asunto, distinto cuerpo, distinto disparador).
  - Deuda 0003 queda **parcialmente resuelta** (no se crean deudas nuevas para lo pendiente); deuda 0004 queda **sin tocar** (cierre automático fuera de alcance, ver spec); deuda 0005 queda **resuelta**.
  - `/asesorias/nueva` (Task 8): el wizard de agendado pasa de 4 pasos (asesor → día → bloque → carrera) a 3 (día → bloque → carrera); no se toca `useAsesoresDeMateria`/`AsesoresDeMateriaView`, que sigue usando `AdminOfertaMateria` (consulta SAE).

## Archivos tocados

| Archivo | Responsabilidad |
|---|---|
| `backend/asesorias/models.py` | Constantes de ventana/duración, `Asesoria.momento_inicio`, validación en `clean()` y `cancelar(forzar=)`, `Disponibilidad.resincronizar_sesiones_futuras()` |
| `backend/asesorias/tasks.py` | `enviar_notificacion_resincronizacion` |
| `backend/asesorias/views.py` | Acción `resincronizar` del `DisponibilidadViewSet` |
| `docs/development/api-frontend.md` | Mensajes de error nuevos + endpoint `resincronizar/` |
| `docs/decisions/0030-*.md` | ADR nuevo |
| `docs/technical-debt/0003|0005*.md` + `README.md` | Cierre de deudas |
| `backend/asesorias/tests/*` | Tests nuevos + ajuste de tests existentes que agendan/cancelan fuera de la ventana |
| `docs/decisions/0016-asesorias-academicas.md` | Changelog: rejilla de 1h (Task 6) |
| `backend/accounts/demo_data.py` + `backend/accounts/tests/test_sembrar_demo.py` | Segundo bloque por asesor (Task 6) |
| `frontend/src/features/asesorias/logica.ts` + `logica.test.ts` | `horasDelDia()` a 14 filas de 1h (Task 7) |
| `frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx` | Copy "1 hora" (Task 7) |
| `frontend/src/features/asesorias/api.ts` | `useDisponibilidadDeMateria` (Task 8) |
| `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx` + `.test.tsx` | Wizard de 3 pasos, tarjetas con profesor/modalidad (Task 8) |

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

# Duración de un bloque de asesoría. Fija la rejilla de `Disponibilidad.hora_fin`.
# 1 hora (no 30 min): ajustado por feedback post-demo, ver Task 6.
DURACION_SESION = datetime.timedelta(hours=1)

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
        anticipación y marcar asistencia.
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

`POST /api/asesorias/disponibilidades/{id}/desactivar/` **no** está sujeto a esta ventana: dar de baja un bloque cancela también las sesiones que arrancan en menos de 2 horas. Ver [ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md) y [deuda técnica 0003](../technical-debt/0003-sin-limites-uso-asesorias.md).
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

### Task 3: `Disponibilidad.resincronizar_sesiones_futuras()` + notificación por correo

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

### Task 4: Endpoint `POST /api/asesorias/disponibilidades/{id}/resincronizar/`

**Files:**
- Modify: `backend/asesorias/views.py`
- Modify: `docs/development/api-frontend.md`
- Test: `backend/asesorias/tests/test_api_disponibilidad.py`

**Interfaces:**
- Consumes: `Disponibilidad.resincronizar_sesiones_futuras()` (Task 3); `SesionFuturaSerializer` y `DisponibilidadViewSet` (ya existentes).
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

### Task 5: ADR 0030 y cierre de las deudas 0003 y 0005

**Files:**
- Create: `docs/decisions/0030-limites-cierre-y-propagacion-asesorias.md`
- Modify: `docs/technical-debt/0003-sin-limites-uso-asesorias.md`
- Modify: `docs/technical-debt/0005-editar-disponibilidad-no-propaga.md`
- Modify: `docs/technical-debt/README.md`

**Interfaces:**
- Consumes: todo lo implementado en Tasks 1–4. No produce código.

- [ ] **Step 1: Crear el ADR**

Crear `docs/decisions/0030-limites-cierre-y-propagacion-asesorias.md`:

```markdown
# 0030 — Ventana de anticipación y resincronización en Asesorías

**Status:** Accepted
**Date:** 2026-08-19

## Context

Dos deudas técnicas de la app `asesorias` comparten modelo (`Asesoria`,
`Disponibilidad`) y se atacan juntas:

- [0003](../technical-debt/0003-sin-limites-uso-asesorias.md) — sin límites de
  uso: un alumno podía agendar o cancelar hasta el segundo anterior a la sesión,
  dejando al asesor sin margen para enterarse.
- [0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md) — `Asesoria`
  congela un snapshot de `formato`/`ubicacion`/`liga_virtual` al agendar, y
  corregir un typo en la `Disponibilidad` (una liga de Zoom mal escrita) no
  llegaba a las sesiones ya agendadas.

La exploración inicial de este plan agrupaba una tercera deuda —
[0004](../technical-debt/0004-sin-cierre-automatico-recordatorios.md), cierre
automático de sesiones vencidas vía Celery Beat — por compartir el mismo
modelo. Se decidió dejarla fuera de este sprint antes de arrancar la
implementación (ver el spec de este plan); la deuda 0004 sigue Activa, sin
cambios.

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
3. **`POST /api/asesorias/disponibilidades/{id}/resincronizar/`** copia
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
- La deuda 0003 queda **parcialmente** resuelta; la 0005 queda **resuelta**. La
  deuda 0004 (cierre automático, recordatorios periódicos) se evaluó y quedó
  fuera de este sprint — sigue Activa, sin ninguna pieza resuelta.

## Alternatives considered

- **Meter la ventana de 2 horas en el serializer en vez del modelo:** dejaría
  `Disponibilidad.desactivar()` (que no pasa por el serializer) sin la regla y
  duplicaría la lógica entre agendar y cancelar. Rechazada: la validación de
  negocio de esta app ya vive en el modelo.
- **Un flag global tipo `saltar_validaciones` en vez de `forzar` en
  `cancelar()`:** más ancho de lo necesario y difícil de auditar. `forzar` es
  keyword-only, con un único call site.
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

**Estado:** Parcialmente resuelta — 2026-08-19 ([ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md))
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

- [ ] **Step 3: Actualizar la deuda 0005**

Reemplazar el contenido completo de `docs/technical-debt/0005-editar-disponibilidad-no-propaga.md` por:

```markdown
# 0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas

**Estado:** Resuelta — 2026-08-19 ([ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md))
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

- [ ] **Step 4: Actualizar el índice de deuda técnica**

En `docs/technical-debt/README.md`, dentro de la sección `### Activa`, reemplazar estas tres líneas:

```markdown
- [0003 — Sin límites de uso en Asesorías](0003-sin-limites-uso-asesorias.md)
- [0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos](0004-sin-cierre-automatico-recordatorios.md)
- [0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas](0005-editar-disponibilidad-no-propaga.md)
```

por:

```markdown
- [0003 — Sin límites de uso en Asesorías](0003-sin-limites-uso-asesorias.md) — parcialmente resuelta 2026-08-19 (ventana de 2 horas lista; faltan límite de sesiones simultáneas y de cancelaciones)
- [0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos](0004-sin-cierre-automatico-recordatorios.md)
```

Nota: la fila de 0004 queda **idéntica** — esa deuda no se toca en este sprint (ver ADR 0030, sección Context). Solo desaparece de esta lista porque 0005 se mueve a `### Resuelta` en el paso siguiente, dejando el bloque de tres líneas en dos.

Y en la sección `### Resuelta`, agregar al final:

```markdown
- [0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas](0005-editar-disponibilidad-no-propaga.md) — resuelta 2026-08-19
```

- [ ] **Step 5: Verificar que no quedaron enlaces rotos**

Run (desde la raíz del repo):

```bash
grep -rn "0030-limites-cierre-y-propagacion-asesorias.md" docs/ && ls docs/decisions/0030-limites-cierre-y-propagacion-asesorias.md
```

Expected: los enlaces aparecen en `docs/development/api-frontend.md` y en los dos ítems de deuda que sí cierra este ADR (0003, 0005), y el archivo del ADR existe.

- [ ] **Step 6: Correr la suite completa del backend una última vez**

Run (desde `backend/`): `uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/decisions/0030-limites-cierre-y-propagacion-asesorias.md docs/technical-debt/
git commit -m "$(cat <<'EOF'
[docs] registrar ADR 0030 y cerrar las deudas 0003 y 0005

- Agregar ADR 0030 (ventana de 2 horas, resincronización) — el cierre
  automático de la deuda 0004 quedó fuera de alcance, ver spec
- Marcar 0003 como parcialmente resuelta, con lo pendiente anotado
  dentro del mismo ítem
- Marcar 0005 como resuelta y moverla en el índice

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 6: Rejilla de `Disponibilidad` a bloques de 1 hora (addendum post-demo)

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/tests/test_disponibilidad.py`
- Modify: `docs/decisions/0016-asesorias-academicas.md`
- Modify: `docs/development/api-frontend.md`
- Modify: `backend/accounts/demo_data.py`
- Modify: `backend/accounts/tests/test_sembrar_demo.py`

**Interfaces:**
- Consumes: `DURACION_SESION = datetime.timedelta(hours=1)` (Task 1, ya ajustado arriba).
- Produces: `Disponibilidad.clean()` rechaza cualquier `hora_inicio` que no caiga en una hora en punto.

- [ ] **Step 1: Escribir el test que falla**

En `backend/asesorias/tests/test_disponibilidad.py`, dentro de `DisponibilidadTests`, agregar este método justo después de `test_hora_fuera_de_rejilla_falla`:

```python
    def test_media_hora_ya_no_cae_en_la_rejilla(self):
        """Feedback post-demo (2026-08-21): la rejilla pasa de 30 min a 1h."""
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 30),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        with self.assertRaises(ValidationError):
            disp.clean()
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad.DisponibilidadTests.test_media_hora_ya_no_cae_en_la_rejilla -v 2`
Expected: FAIL — `10:30` todavía es válido con la rejilla actual (`ValidationError not raised`).

- [ ] **Step 3: Implementar el cambio de rejilla**

En `backend/asesorias/models.py`, dentro de `Disponibilidad`, reemplazar:

```python
    def clean(self):
        if self.hora_inicio.minute not in (0, 30) or self.hora_inicio.second != 0:
            raise ValidationError("hora_inicio debe caer en la rejilla de 30 minutos.")
```

por:

```python
    def clean(self):
        if self.hora_inicio.minute != 0 or self.hora_inicio.second != 0:
            raise ValidationError("hora_inicio debe caer en la rejilla de 1 hora.")
```

- [ ] **Step 4: Arreglar los dos tests existentes que asumían la rejilla de 30 min**

En `backend/asesorias/tests/test_disponibilidad.py`, dentro de `DisponibilidadTests`, reemplazar `test_bloque_valido_presencial`:

```python
    def test_bloque_valido_presencial(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 3",
        )
        disp.clean()  # no lanza
        disp.save()
        self.assertEqual(disp.hora_fin, datetime.time(10, 30))
        disp.delete()
```

por:

```python
    def test_bloque_valido_presencial(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 3",
        )
        disp.clean()  # no lanza
        disp.save()
        self.assertEqual(disp.hora_fin, datetime.time(11, 0))
        disp.delete()
```

Y reemplazar `test_bloque_valido_virtual` (usaba `10:30` como ejemplo de hora válida; con la rejilla de 1h ya no lo es):

```python
    def test_bloque_valido_virtual(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 30),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        disp.clean()  # no lanza
```

por:

```python
    def test_bloque_valido_virtual(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        disp.clean()  # no lanza
```

- [ ] **Step 5: Correr la suite de `test_disponibilidad.py` y verificar que todo pasa**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad -v 2`
Expected: PASS.

- [ ] **Step 6: Ampliar el guion de demo con un segundo bloque por asesor**

En `backend/accounts/demo_data.py`, reemplazar las `disponibilidades` de `DEMOTRAB1`:

```python
        "disponibilidades": [
            {"dia_semana": 0, "hora_inicio": datetime.time(10, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-lunes"},
            {"dia_semana": 2, "hora_inicio": datetime.time(10, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-miercoles"},
        ],
```

por:

```python
        "disponibilidades": [
            {"dia_semana": 0, "hora_inicio": datetime.time(10, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-lunes"},
            {"dia_semana": 0, "hora_inicio": datetime.time(14, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-lunes-tarde"},
            {"dia_semana": 2, "hora_inicio": datetime.time(10, 0), "formato": "virtual",
             "liga_virtual": "https://meet.atenea.demo/diego-miercoles"},
        ],
```

Y las de `DEMOTRAB2`:

```python
        "disponibilidades": [
            {"dia_semana": 1, "hora_inicio": datetime.time(12, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
            {"dia_semana": 3, "hora_inicio": datetime.time(12, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
        ],
```

por:

```python
        "disponibilidades": [
            {"dia_semana": 1, "hora_inicio": datetime.time(12, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
            {"dia_semana": 1, "hora_inicio": datetime.time(16, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
            {"dia_semana": 3, "hora_inicio": datetime.time(12, 0), "formato": "presencial",
             "ubicacion": "Salón 105, Edificio Principal"},
        ],
```

> Un bloque nuevo por asesor, mismo día distinta hora, para que el paso "elige un bloque" del wizard nuevo (Task 8) tenga más de una tarjeta que mostrar. Dos asesores compartiendo día **y** materia requeriría que `sembrar_demo.py` asignara la misma materia a dos académicos de la misma área — hoy asigna una materia por área automáticamente — así que queda fuera de este ajuste; los índices `"disponibilidad": 0` y `1` que usa `ASESORIAS_DEMO` para las 6 asesorías siguen apuntando a los mismos dos bloques de siempre, sin cambios.

- [ ] **Step 7: Ajustar las aserciones de `test_sembrar_demo.py` al nuevo conteo**

En `backend/accounts/tests/test_sembrar_demo.py`, dentro de `test_crea_dos_asesores_activos_y_uno_pendiente`, reemplazar:

```python
            self.assertEqual(asesor.registros.get().disponibilidades.count(), 2)
```

por:

```python
            self.assertEqual(asesor.registros.get().disponibilidades.count(), 3)
```

Y dentro de `test_es_idempotente`, reemplazar:

```python
        self.assertEqual(Disponibilidad.objects.count(), 4)
```

por:

```python
        self.assertEqual(Disponibilidad.objects.count(), 6)
```

- [ ] **Step 8: Correr la suite de demo y verificar que pasa**

Run: `uv run manage.py test accounts.tests.test_sembrar_demo accounts.tests.test_limpiar_demo -v 2`
Expected: PASS.

- [ ] **Step 9: Actualizar el contrato de `Disponibilidad` en `api-frontend.md`**

En `docs/development/api-frontend.md`, reemplazar:

```markdown
`Disponibilidad` es un slot fijo de 30 minutos, no un rango — `dia_semana` (0=Lunes…6=Domingo), `hora_inicio` debe caer en la rejilla `:00`/`:30`, `formato` (`presencial`/`virtual`) determina si `ubicacion` o `liga_virtual` es obligatorio. Validaciones fallidas → `400 {"detail": ["..."]}`.
```

por:

```markdown
`Disponibilidad` es un slot fijo de 1 hora, no un rango — `dia_semana` (0=Lunes…6=Domingo), `hora_inicio` debe caer en la rejilla de horas en punto (`:00`; antes de 2026-08-21 aceptaba también `:30`), `formato` (`presencial`/`virtual`) determina si `ubicacion` o `liga_virtual` es obligatorio. Validaciones fallidas → `400 {"detail": ["..."]}`.
```

Y en el ejemplo JSON de `GET /api/asesorias/disponibilidad/buscar/`, reemplazar:

```json
  "hora_inicio": "10:00:00",
  "hora_fin": "10:30:00",
```

por:

```json
  "hora_inicio": "10:00:00",
  "hora_fin": "11:00:00",
```

- [ ] **Step 10: Changelog en el ADR 0016**

En `docs/decisions/0016-asesorias-academicas.md`, al final de la sección `## Changelog`, agregar:

```markdown
- **2026-08-21** — La rejilla de `Disponibilidad.hora_inicio` pasa de bloques de 30 minutos a bloques de 1 hora: `hora_inicio.minute != 0` es inválido (antes `not in (0, 30)`). `DURACION_SESION` — la constante que fija `hora_fin` — pasa de `timedelta(minutes=30)` a `timedelta(hours=1)`. Motivo: feedback de la demo del 21 de agosto — media hora no correspondía a la duración real de una asesoría. Sin migración de columnas: `hora_fin` es una `@property` calculada, no una columna de base de datos, y el anti-doble-booking (`UniqueConstraint(disponibilidad, fecha)`, ver Consequences arriba) no depende del tamaño del bloque. Detalle en la [sección 3 del spec de límites y propagación](../superpowers/specs/2026-08-19-asesorias-limites-cierre-propagacion-design.md#3-bloques-de-1-hora-y-nuevo-flujo-de-agendado-del-alumno).
```

- [ ] **Step 11: Correr la suite completa del backend**

Run: `uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 12: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/tests/test_disponibilidad.py backend/accounts/demo_data.py backend/accounts/tests/test_sembrar_demo.py docs/decisions/0016-asesorias-academicas.md docs/development/api-frontend.md
git commit -m "$(cat <<'EOF'
[feat][backend] cambiar la rejilla de Disponibilidad de 30 min a 1 hora

- Disponibilidad.clean() ahora solo acepta horas en punto (antes :00/:30)
- Ampliar backend/accounts/demo_data.py con un segundo bloque por asesor
  (mismo día, distinta hora) para el nuevo wizard de agendado (Task 8)
- Changelog en ADR 0016 y contrato actualizado en api-frontend.md

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 7: Grid de "Mi horario" a bloques de 1 hora (frontend, asesor)

**Files:**
- Modify: `frontend/src/features/asesorias/logica.ts`
- Modify: `frontend/src/features/asesorias/logica.test.ts`
- Modify: `frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx`

**Interfaces:**
- Consumes: nada de tasks previos (independiente del backend — ya envía/recibe horas en punto).
- Produces: `horasDelDia(): string[]` con 14 elementos en vez de 28.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/features/asesorias/logica.test.ts`, reemplazar el bloque `describe('horasDelDia', ...)`:

```typescript
describe('horasDelDia', () => {
  it('produce los 28 slots de media hora de 07:00 a 20:30', () => {
    const horas = horasDelDia()
    expect(horas).toHaveLength(28)
    expect(horas[0]).toBe('07:00:00')
    expect(horas[1]).toBe('07:30:00')
    expect(horas.at(-1)).toBe('20:30:00')
  })
})
```

por:

```typescript
describe('horasDelDia', () => {
  it('produce las 14 horas en punto de 07:00 a 20:00', () => {
    const horas = horasDelDia()
    expect(horas).toHaveLength(14)
    expect(horas[0]).toBe('07:00:00')
    expect(horas[1]).toBe('08:00:00')
    expect(horas.at(-1)).toBe('20:00:00')
  })
})
```

Y dentro de `describe('slotsDelDia', ...)`, reemplazar:

```typescript
  it('devuelve un slot por cada media hora del día', () => {
    expect(slotsDelDia(0, [])).toHaveLength(28)
  })
```

por:

```typescript
  it('devuelve un slot por cada hora del día', () => {
    expect(slotsDelDia(0, [])).toHaveLength(14)
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run (desde `frontend/`): `npm test -- logica.test.ts`
Expected: FAIL — `horasDelDia()` sigue devolviendo 28 elementos.

- [ ] **Step 3: Implementar el cambio de rejilla**

En `frontend/src/features/asesorias/logica.ts`, reemplazar:

```typescript
/** Los 28 slots de 30 minutos que cubre un día de asesorías: 07:00–20:30. */
export function horasDelDia(): string[] {
  const horas: string[] = [];
  for (let h = 7; h <= 20; h++) {
    horas.push(`${String(h).padStart(2, "0")}:00:00`);
    horas.push(`${String(h).padStart(2, "0")}:30:00`);
  }
  return horas;
}
```

por:

```typescript
/** Las 14 horas en punto que cubre un día de asesorías: 07:00–20:00
 *  (bloques de 1h, así que el último cubre hasta las 21:00). */
export function horasDelDia(): string[] {
  const horas: string[] = [];
  for (let h = 7; h <= 20; h++) {
    horas.push(`${String(h).padStart(2, "0")}:00:00`);
  }
  return horas;
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run (desde `frontend/`): `npm test -- logica.test.ts`
Expected: PASS.

- [ ] **Step 5: Actualizar el copy de `DialogoNuevoBloque`**

En `frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx`, reemplazar:

```tsx
      descripcion="Bloque recurrente de 30 minutos cada semana."
```

por:

```tsx
      descripcion="Bloque recurrente de 1 hora cada semana."
```

- [ ] **Step 6: Correr la suite frontend completa**

Run (desde `frontend/`): `npm test`
Expected: PASS. (`DialogoNuevoBloque` no tiene test propio que fije el copy anterior — verificar con `grep -rn "30 minutos" frontend/src` que no queda ninguna referencia.)

- [ ] **Step 7: Lint y build**

Run (desde `frontend/`): `npm run lint && npm run build`
Expected: sin errores.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/asesorias/logica.ts frontend/src/features/asesorias/logica.test.ts frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx
git commit -m "$(cat <<'EOF'
[feat][frontend] llevar la rejilla de "Mi horario" a bloques de 1 hora

- horasDelDia() pasa de 28 filas de 30 min a 14 filas de 1h (07:00-20:00)
- Actualizar el copy de DialogoNuevoBloque

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 8: Nuevo flujo de agendado del alumno en `/asesorias/nueva`

**Files:**
- Modify: `frontend/src/features/asesorias/api.ts`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx`
- Modify: `docs/development/api-frontend.md`

**Interfaces:**
- Consumes: `GET /api/asesorias/disponibilidad/buscar/?materia=` (ya existente, ya acepta `?asesor=` opcional), `agruparPorDia` (ya existente en `logica.ts`).
- Produces: `useDisponibilidadDeMateria(materiaId: number | null)`; `AgendarAsesoria` con wizard de 3 pasos (`dia` → `bloque` → `carrera`).

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx`, reemplazar el archivo completo:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AgendarAsesoria } from './AgendarAsesoria'
import * as api from '../api'
import * as auth from '../../../auth/AuthContext'
import * as catalogo from '../../catalogo/api'
import { ApiError } from '../../../api/client'
import type { SlotDisponibilidad, InscripcionAlumno } from '../../../api/types'

const SLOTS: SlotDisponibilidad[] = [
  {
    registro_id: 7, asesor_nombre: 'Ana López', disponibilidad_id: 41, fecha: '2026-08-10',
    hora_inicio: '10:00:00', hora_fin: '11:00:00', formato: 'virtual', ubicacion: '', liga_virtual: 'https://x',
  },
]

const HISTORIAL_UNA: InscripcionAlumno[] = [
  { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
]

function mockComun(
  mutateImpl: ReturnType<typeof vi.fn>,
  historial: InscripcionAlumno[] = HISTORIAL_UNA,
) {
  vi.spyOn(api, 'useDisponibilidadDeMateria').mockReturnValue({
    data: SLOTS, isPending: false,
  } as ReturnType<typeof api.useDisponibilidadDeMateria>)
  vi.spyOn(api, 'useAgendarAsesoria').mockReturnValue({
    mutate: mutateImpl, isPending: false,
  } as unknown as ReturnType<typeof api.useAgendarAsesoria>)
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: { perfil_alumno: { id: 1, numero_cuenta: '312345678', historial } },
    status: 'authenticated',
  } as unknown as ReturnType<typeof auth.useAuth>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(
    new Map([
      [3, { id: 3, nombre: 'Actuaría' } as never],
      [6, { id: 6, nombre: 'Matemáticas' } as never],
    ]),
  )
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[12, { id: 12, nombre: 'Álgebra' } as never]]))
}

function montar(entrada = '/asesorias/nueva/12') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entrada]}>
        <Routes>
          <Route path="/asesorias/nueva/:materiaId" element={<AgendarAsesoria />} />
          <Route path="/asesorias" element={<p>lista de asesorías</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return queryClient
}

function avanzarHastaConfirmar() {
  fireEvent.click(screen.getByText(/10 de agosto/i))
  fireEvent.click(screen.getByText('10:00–11:00'))
  // Botón que abre el diálogo (etiqueta distinta a la acción del diálogo).
  fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
}

describe('AgendarAsesoria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('arranca directo en el paso de día, sin pedir asesor primero', () => {
    mockComun(vi.fn())
    montar()
    expect(screen.getByText('Elige un día')).toBeInTheDocument()
    expect(screen.queryByText('Elige un asesor')).not.toBeInTheDocument()
  })

  it('la tarjeta del bloque muestra profesor y modalidad', () => {
    mockComun(vi.fn())
    montar()
    fireEvent.click(screen.getByText(/10 de agosto/i))
    expect(screen.getByText('Ana López')).toBeInTheDocument()
    expect(screen.getByText('Virtual')).toBeInTheDocument()
  })

  it('confirmar dispara el POST con el payload correcto', () => {
    const mutate = vi.fn()
    mockComun(mutate)
    montar()
    avanzarHastaConfirmar()
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' })) // botón del diálogo
    expect(mutate).toHaveBeenCalledWith(
      { disponibilidad: 41, fecha: '2026-08-10', materia: 12, carrera: 3 },
      expect.anything(),
    )
  })

  it('un 409 regresa al paso de día', async () => {
    const mutate = vi.fn((_payload, { onError }) => onError(new ApiError(409, { detail: 'tomado' })))
    mockComun(mutate)
    montar()
    avanzarHastaConfirmar()
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(await screen.findByText('Elige un día')).toBeInTheDocument()
    expect(screen.getByText(/ya fue tomado/i)).toBeInTheDocument()
  })

  it('un 409 invalida la búsqueda de disponibilidad para forzar el refetch', () => {
    const mutate = vi.fn((_payload, { onError }) => onError(new ApiError(409, { detail: 'tomado' })))
    mockComun(mutate)
    const queryClient = montar()
    const invalidar = vi.spyOn(queryClient, 'invalidateQueries')
    avanzarHastaConfirmar()
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(invalidar).toHaveBeenCalledWith({ queryKey: ['disponibilidad'] })
  })

  it('un usuario sin perfil de alumno no puede agendar', () => {
    mockComun(vi.fn())
    vi.spyOn(auth, 'useAuth').mockReturnValue({
      user: { perfil_alumno: null },
      status: 'authenticated',
    } as unknown as ReturnType<typeof auth.useAuth>)
    montar()
    expect(screen.getByText(/sólo los alumnos pueden agendar/i)).toBeInTheDocument()
    expect(screen.queryByText('Elige un día')).not.toBeInTheDocument()
  })
})

describe('AgendarAsesoria — selección de carrera', () => {
  afterEach(() => vi.restoreAllMocks())

  function avanzarHastaCarrera() {
    fireEvent.click(screen.getByText(/10 de agosto/i))
    fireEvent.click(screen.getByText('10:00–11:00'))
  }

  it('con una sola inscripción deja la carrera preseleccionada', () => {
    mockComun(vi.fn())
    montar()
    avanzarHastaCarrera()
    expect((screen.getByLabelText('Carrera') as HTMLSelectElement).value).toBe('3')
  })

  it('con dos inscripciones ofrece ambas y no preselecciona ninguna', () => {
    mockComun(vi.fn(), [
      { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
      { carrera: 6, carrera_nombre: 'Matemáticas', generacion: 2025 },
    ])
    montar()
    avanzarHastaCarrera()
    const select = screen.getByLabelText('Carrera') as HTMLSelectElement
    expect(select.value).toBe('')
    expect([...select.options].map((o) => o.textContent)).toEqual([
      'Elige una carrera', 'Actuaría', 'Matemáticas',
    ])
  })

  it('con dos inscripciones el POST manda la que se eligió', () => {
    const mutate = vi.fn()
    mockComun(mutate, [
      { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
      { carrera: 6, carrera_nombre: 'Matemáticas', generacion: 2025 },
    ])
    montar()
    avanzarHastaCarrera()
    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '6' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ carrera: 6 }),
      expect.anything(),
    )
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run (desde `frontend/`): `npm test -- AgendarAsesoria.test.tsx`
Expected: FAIL — `api.useDisponibilidadDeMateria` no existe todavía, y `AgendarAsesoria` sigue pidiendo un asesor primero.

- [ ] **Step 3: Agregar el hook `useDisponibilidadDeMateria`**

En `frontend/src/features/asesorias/api.ts`, insertar esta función justo después de `useDisponibilidadDeAsesor`:

```typescript
/**
 * Días y bloques disponibles de una materia, a través de todos los
 * asesores que la imparten (sin elegir asesor primero). Mismo endpoint
 * que `useDisponibilidadDeAsesor` sin `?asesor=` — ya devuelve
 * `asesor_nombre`/`formato` por slot, así que la tarjeta de cada bloque
 * puede mostrarlos sin una consulta aparte.
 */
export function useDisponibilidadDeMateria(materiaId: number | null) {
  return useQuery({
    queryKey: ['disponibilidad', materiaId, null],
    queryFn: () =>
      apiGet<SlotDisponibilidad[]>(`/api/asesorias/disponibilidad/buscar/?materia=${materiaId}`),
    enabled: materiaId !== null,
  })
}
```

- [ ] **Step 4: Reescribir el wizard de `AgendarAsesoria`**

En `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx`, reemplazar el archivo completo:

```tsx
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useDisponibilidadDeMateria, useAgendarAsesoria } from '../api'
import { agruparPorDia } from '../logica'
import { useAuth } from '../../../auth/AuthContext'
import { useMapaCarreras, useMapaMaterias } from '../../catalogo/api'
import { Dialogo } from '../../../components/ui/Dialogo'
import { Skeleton } from '../../../components/ui/Skeleton'
import { primerMensajeDeError } from '../../../api/errores'
import { ApiError } from '../../../api/client'
import type { SlotDisponibilidad } from '../../../api/types'

const FORMATEADOR_DIA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })

export function AgendarAsesoria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const idMateria = Number(materiaId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const mapaCarreras = useMapaCarreras()
  const mapaMaterias = useMapaMaterias()

  const { data: slots = [], isPending: cargandoSlots } = useDisponibilidadDeMateria(
    Number.isInteger(idMateria) ? idMateria : null,
  )
  const dias = useMemo(() => agruparPorDia(slots), [slots])

  const [fecha, setFecha] = useState<string | null>(null)
  const [slot, setSlot] = useState<SlotDisponibilidad | null>(null)
  const historial = user?.perfil_alumno?.historial ?? []
  // Con una sola inscripción no hay nada que preguntar: se preselecciona.
  // Con dos o más, `carrera` arranca en null y el backend exige el campo.
  const [carrera, setCarrera] = useState<number | null>(
    historial.length === 1 ? historial[0].carrera : null,
  )
  const [confirmando, setConfirmando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const agendar = useAgendarAsesoria()

  const paso = fecha === null ? 'dia' : slot === null ? 'bloque' : 'carrera'

  function volver() {
    setError(null)
    if (slot !== null) return setSlot(null)
    if (fecha !== null) return setFecha(null)
    navigate('/asesorias')
  }

  function confirmar() {
    if (slot === null || carrera === null || fecha === null) return
    agendar.mutate(
      { disponibilidad: slot.disponibilidad_id, fecha, materia: idMateria, carrera },
      {
        onSuccess: (asesoria) => {
          setConfirmando(false)
          navigate('/asesorias', { state: { nuevaAsesoriaId: asesoria.id } })
        },
        onError: (err) => {
          setConfirmando(false)
          if (err instanceof ApiError && err.status === 409) {
            // El bloque tomado sigue en la caché de disponibilidad (y `num_asesores`
            // en la oferta pudo cambiar); invalidar ambos fuerza el refetch al
            // regresar al paso de día y evita reofrecer el bloque ya ocupado.
            queryClient.invalidateQueries({ queryKey: ['disponibilidad'] })
            queryClient.invalidateQueries({ queryKey: ['oferta'] })
            setError('Ese horario ya fue tomado. Elige otro día.')
            setSlot(null)
            setFecha(null)
          } else {
            setError(primerMensajeDeError(err))
          }
        },
      },
    )
  }

  const slotsDelDia = dias.find((d) => d.fecha === fecha)?.slots ?? []

  if (!Number.isInteger(idMateria)) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate('/asesorias')} className="foco-visible w-fit min-h-11 text-sm text-primary">← Volver a Asesorías</button>
        <p className="text-sm text-on-surface-variant">Materia inválida.</p>
      </main>
    )
  }

  if (historial.length === 0) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate('/asesorias')} className="foco-visible w-fit min-h-11 text-sm text-primary">← Volver a Asesorías</button>
        <p className="text-sm text-on-surface-variant">Sólo los alumnos pueden agendar asesorías.</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={volver} className="foco-visible w-fit min-h-11 text-sm text-primary">← Atrás</button>
      <h1 className="text-lg font-semibold text-on-background">
        {mapaMaterias.get(idMateria)?.nombre ?? `Materia #${idMateria}`}
      </h1>

      {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}

      {paso === 'dia' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un día</h2>
          {cargandoSlots ? (
            <Skeleton className="h-14" />
          ) : dias.length === 0 ? (
            <p className="text-sm text-on-surface-variant">Esta materia no tiene horarios en las próximas dos semanas.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {dias.map((d, indice) => (
                <li key={d.fecha} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
                  <button
                    type="button"
                    onClick={() => setFecha(d.fecha)}
                    className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
                  >
                    <span className="text-sm text-on-surface">
                      {FORMATEADOR_DIA.format(new Date(`${d.fecha}T00:00:00`))}
                    </span>
                    <span className="text-xs text-on-surface-variant">
                      {d.slots.length} bloque{d.slots.length === 1 ? '' : 's'}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {paso === 'bloque' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un bloque</h2>
          <ul className="flex flex-col gap-2">
            {slotsDelDia.map((s) => (
              <li key={s.disponibilidad_id}>
                <button
                  type="button"
                  onClick={() => setSlot(s)}
                  className="fila-interactiva foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg bg-surface-container px-4 py-3 text-left"
                >
                  <span className="flex w-full items-center justify-between text-sm text-on-surface">
                    <span>{s.hora_inicio.slice(0, 5)}–{s.hora_fin.slice(0, 5)}</span>
                    <span className="text-xs text-on-surface-variant">
                      {s.formato === 'virtual' ? 'Virtual' : s.ubicacion || 'Presencial'}
                    </span>
                  </span>
                  <span className="text-xs text-on-surface-variant">{s.asesor_nombre}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {paso === 'carrera' && slot !== null && fecha !== null && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-on-surface">Confirma tu asesoría</h2>
          <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
            <dt>Día</dt>
            <dd>{FORMATEADOR_DIA.format(new Date(`${fecha}T00:00:00`))}</dd>
            <dt>Hora</dt>
            <dd>{slot.hora_inicio.slice(0, 5)}</dd>
            <dt>Asesor</dt>
            <dd>{slot.asesor_nombre}</dd>
          </dl>

          <div className="flex flex-col gap-1">
            <label htmlFor="carrera-agendar" className="text-xs text-on-surface-variant">Carrera</label>
            <select
              id="carrera-agendar"
              value={carrera ?? ''}
              onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
              className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
            >
              {historial.length > 1 && <option value="">Elige una carrera</option>}
              {historial.map((inscripcion) => (
                <option key={inscripcion.carrera} value={inscripcion.carrera}>
                  {mapaCarreras.get(inscripcion.carrera)?.nombre ?? inscripcion.carrera_nombre}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => setConfirmando(true)}
            disabled={carrera === null}
            className="foco-visible flex min-h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-on-primary disabled:opacity-60"
          >
            Continuar
          </button>

          <Dialogo
            abierto={confirmando}
            titulo="Confirmar asesoría"
            descripcion={`${FORMATEADOR_DIA.format(new Date(`${fecha}T00:00:00`))} · ${slot.hora_inicio.slice(0, 5)}`}
            onCerrar={() => setConfirmando(false)}
            acciones={[{ etiqueta: 'Agendar', cargando: agendar.isPending, onClick: confirmar }]}
          />
        </section>
      )}
    </main>
  )
}
```

Cambios frente a la versión anterior: se quita el paso `asesor` (y la función `BotonAsesor`, que solo ese paso usaba), `useAsesoresDeMateria`/`useDisponibilidadDeAsesor` se reemplazan por `useDisponibilidadDeMateria`, y la tarjeta de bloque gana una segunda línea con `s.asesor_nombre`.

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run (desde `frontend/`): `npm test -- AgendarAsesoria.test.tsx`
Expected: PASS.

- [ ] **Step 6: Documentar `?asesor=` como opcional en `api-frontend.md`**

El endpoint ya soportaba `?asesor=` sin estar documentado; ahora que el wizard lo omite a propósito (Task 8) vale la pena dejarlo explícito. En `docs/development/api-frontend.md`, reemplazar:

```markdown
**`GET /api/asesorias/disponibilidad/buscar/`** — `EsAlumno`. Query params opcionales, combinados con AND: `?materia=<id>`, `?carrera=<id>`, `?formato=presencial|virtual`. Devuelve slots libres ya expandidos por fecha dentro de la ventana agendable:
```

por:

```markdown
**`GET /api/asesorias/disponibilidad/buscar/`** — `EsAlumno`. Query params opcionales, combinados con AND: `?materia=<id>`, `?carrera=<id>`, `?formato=presencial|virtual`, `?asesor=<registro_id>`. Sin `?asesor=` devuelve bloques de todos los asesores que imparten la materia (cada resultado ya trae `asesor_nombre`) — es lo que usa el wizard de agendado en `/asesorias/nueva` desde el 2026-08-21 para no pedir asesor antes de mostrar los días disponibles. Devuelve slots libres ya expandidos por fecha dentro de la ventana agendable:
```

- [ ] **Step 7: Correr la suite frontend completa**

Run (desde `frontend/`): `npm test`
Expected: PASS.

- [ ] **Step 8: Lint y build**

Run (desde `frontend/`): `npm run lint && npm run build`
Expected: sin errores. (`oxlint` debe señalar si queda algo sin usar — confirmar que `useAsesoresDeMateria`/`useDisponibilidadDeAsesor`/`AsesorDisponible` ya no se importan en `AgendarAsesoria.tsx`; siguen usándose en `AdminOfertaMateria.tsx`, así que no se tocan en `api.ts`.)

- [ ] **Step 9: Commit**

```bash
git add frontend/src/features/asesorias/api.ts frontend/src/features/asesorias/screens/AgendarAsesoria.tsx frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx docs/development/api-frontend.md
git commit -m "$(cat <<'EOF'
[feat][frontend] agendar sin elegir asesor primero: materia -> día -> bloque

- Nuevo hook useDisponibilidadDeMateria (mismo endpoint sin ?asesor=)
- AgendarAsesoria pasa de 4 pasos (asesor/día/bloque/carrera) a 3
- La tarjeta de bloque muestra profesor y modalidad
- Documentar ?asesor= como opcional en api-frontend.md
- useAsesoresDeMateria/AsesoresDeMateriaView no se tocan: los sigue
  usando AdminOfertaMateria (consulta SAE)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Verificación final

- [ ] Desde `backend/`: `uv run manage.py test -v 1` → PASS.
- [ ] Desde `backend/`: `uv run manage.py check` → sin issues.
- [ ] Desde `backend/`: `uv run manage.py makemigrations --check --dry-run` → `No changes detected`.
- [ ] Desde `frontend/`: `npm test` → PASS.
- [ ] Desde `frontend/`: `npm run lint` → sin errores.
- [ ] Desde `frontend/`: `npm run build` → sin errores.
- [ ] `git log --oneline` muestra 8 commits, uno por task (Tasks 1–5 del alcance original + Tasks 6–8 del addendum post-demo).
