# Asesorías Académicas (Fase 0 + Fase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar el dominio de Asesorías Académicas: los perfiles de identidad prerrequisito (`PerfilAlumno`, `PerfilAcademico` en `accounts`) y los cuatro modelos de negocio (`PerfilAsesorAcademico`, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) en una app nueva `asesorias`, con validaciones, anti-doble-booking a nivel de BD, y notificación por email vía Celery — sin capa DRF en esta pasada.

**Architecture:** Fase 0 modifica `backend/accounts/` (agrega 2 modelos al archivo existente). Fase 1 crea `backend/asesorias/`, siguiendo el layout de la ADR 0011, dependiendo de `accounts` (perfiles), `carreras` (`Area`) y `materias` (`Materia`, `OfertaMateria`). Toda la lógica de negocio vive en métodos del modelo (`agregar_materia`, `marcar_asistencia`, `guardar_notas`, `cancelar`), no en vistas — no hay capa DRF en este plan. Las notificaciones por email se disparan vía Celery: al crear una `Asesoria` (señal `post_save`) y al cancelarla (llamada directa en `cancelar()`).

**Tech Stack:** Django 6.0, PostgreSQL 16 (constraints condicionales `UniqueConstraint(condition=Q(...))`), Celery (`shared_task`), `uv` como gestor de paquetes del backend.

## Global Constraints

- Layout de apps: directo en `backend/<nombre>/`, no bajo `backend/apps/` (ADR 0011).
- `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` en cada `AppConfig`, igual que `accounts`/`carreras`/`materias`.
- Commits atómicos, formato `[type][scope] resumen` + bullets + `Signed-off-by`, ver `docs/development/commit-conventions.md`.
- Todo comando se ejecuta desde `backend/` con `uv run python manage.py ...` (`DJANGO_SETTINGS_MODULE=config.settings.dev`, ya configurado en `backend/.env`).
- Base de datos de dev/test es Postgres real (`docker compose -f docker-compose.dev.yml up -d postgres`, requerido antes de `migrate`/`test`) — no SQLite.
- Perfiles de identidad y de rol siguen el patrón de la ADR 0012: `OneToOneField` a `User`, alcance fino en el mismo modelo, chequeo de rol con `hasattr(user, "perfil_x")`, prerequisitos validados en `clean()`.
- Semestre en formato `AAAAN` (`CharField(max_length=5)`), mismo formato que `materias.OfertaMateria.semestre` (ADR 0015).
- `on_delete=PROTECT` en toda FK que forma parte de un historial — nunca se pierde una fila por borrar un registro relacionado.
- Sin capa DRF (serializers/viewsets/urls) en este plan — solo modelos, admin, lógica de negocio Python y tests.

---

## File Structure

```
backend/accounts/
  models.py           (modificado: + PerfilAlumno, PerfilAcademico)
  admin.py             (modificado: + PerfilAlumnoAdmin, PerfilAcademicoAdmin)
  migrations/
    0002_perfiles.py   (autogenerada)
  tests/
    test_perfiles.py   (nuevo)

backend/asesorias/
  __init__.py
  apps.py
  models.py
  admin.py
  tasks.py
  signals.py
  migrations/
    __init__.py
    0001_initial.py
  tests/
    __init__.py
    test_perfil_asesor_academico.py
    test_registro_asesor.py
    test_disponibilidad.py
    test_asesoria.py

backend/config/settings/base.py   (modificado: LOCAL_APPS)
```

---

### Task 1: `PerfilAlumno` y `PerfilAcademico` en `accounts`

**Files:**
- Modify: `backend/accounts/models.py`
- Modify: `backend/accounts/admin.py`
- Create: `backend/accounts/migrations/0002_perfiles.py` (autogenerada)
- Test: `backend/accounts/tests/test_perfiles.py`

**Interfaces:**
- Produces: `accounts.models.PerfilAlumno` (`user: User` OneToOne, `numero_cuenta: str`), `accounts.models.PerfilAcademico` (`user: User` OneToOne, `numero_trabajador: str`).
- Consumidores futuros: Task 2 (`PerfilAsesorAcademico.clean()` exige `hasattr(user, "perfil_academico")`), Task 5 (`Asesoria.alumno` FK a `PerfilAlumno`).

- [ ] **Step 1: Agregar los modelos a `accounts/models.py`**

Al final de `backend/accounts/models.py`, después de la clase `User`:

```python
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

- [ ] **Step 2: Generar y aplicar la migración**

```bash
cd backend
docker compose -f ../docker-compose.dev.yml up -d postgres
uv run python manage.py makemigrations accounts
uv run python manage.py migrate accounts
```

Verifica que `backend/accounts/migrations/0002_perfiles.py` tenga `CreateModel` para `PerfilAlumno` y `PerfilAcademico`, ambos con un `OneToOneField` a `accounts.User`.

- [ ] **Step 3: Registrar en el admin**

En `backend/accounts/admin.py`, agregar al final:

```python
from .models import PerfilAcademico, PerfilAlumno


@admin.register(PerfilAlumno)
class PerfilAlumnoAdmin(admin.ModelAdmin):
    list_display = ("numero_cuenta", "user")
    search_fields = ("numero_cuenta", "user__email")


@admin.register(PerfilAcademico)
class PerfilAcademicoAdmin(admin.ModelAdmin):
    list_display = ("numero_trabajador", "user")
    search_fields = ("numero_trabajador", "user__email")
```

(El `from .models import User` ya existente en el archivo se mantiene; agrega el nuevo import junto a él, no lo dupliques.)

- [ ] **Step 4: Escribir los tests**

```python
# backend/accounts/tests/test_perfiles.py
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User


class PerfilAlumnoTests(TestCase):
    def test_numero_cuenta_unico(self):
        user1 = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        user2 = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(user=user1, numero_cuenta="312345678")
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAlumno.objects.create(user=user2, numero_cuenta="312345678")

    def test_un_user_no_puede_tener_dos_perfiles_alumno(self):
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(user=user, numero_cuenta="312345678")
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAlumno.objects.create(user=user, numero_cuenta="399999999")


class PerfilAcademicoTests(TestCase):
    def test_numero_trabajador_unico(self):
        user1 = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        user2 = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user1, numero_trabajador="12345")
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAcademico.objects.create(user=user2, numero_trabajador="12345")
```

- [ ] **Step 5: Correr los tests**

```bash
cd backend
uv run python manage.py test accounts.tests.test_perfiles -v 2
```

Expected: `OK` (3 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/accounts/models.py backend/accounts/admin.py backend/accounts/migrations/0002_perfiles.py backend/accounts/tests/test_perfiles.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar PerfilAlumno y PerfilAcademico

- agregar modelos PerfilAlumno (numero_cuenta) y PerfilAcademico (numero_trabajador) como OneToOneField a User, patrón de ADR 0012
- registrar ambos perfiles en el admin
- agregar tests de unicidad de numero_cuenta/numero_trabajador y de OneToOne

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 2: App `asesorias` — modelo `PerfilAsesorAcademico`

**Files:**
- Create: `backend/asesorias/__init__.py`
- Create: `backend/asesorias/apps.py`
- Create: `backend/asesorias/models.py`
- Modify: `backend/config/settings/base.py` (agregar `"asesorias"` a `LOCAL_APPS`)
- Create: `backend/asesorias/migrations/__init__.py`
- Create: `backend/asesorias/migrations/0001_initial.py` (autogenerada)
- Test: `backend/asesorias/tests/__init__.py`
- Test: `backend/asesorias/tests/test_perfil_asesor_academico.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.models.PerfilAcademico` (Task 1), `carreras.models.Area` (ya existe).
- Produces: `asesorias.models.PerfilAsesorAcademico` (`user: User` OneToOne, `area: Area`, `activo: bool`, método `clean()`).
- Consumidores futuros: Task 3 (`RegistroAsesor.asesor` FK), Task 5 (`Asesoria` vía `Disponibilidad.registro.asesor`).

- [ ] **Step 1: Crear el paquete de la app**

```bash
mkdir -p backend/asesorias/migrations backend/asesorias/tests
touch backend/asesorias/__init__.py backend/asesorias/migrations/__init__.py backend/asesorias/tests/__init__.py
```

- [ ] **Step 2: `apps.py`**

```python
# backend/asesorias/apps.py
from django.apps import AppConfig


class AsesoriasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "asesorias"
```

- [ ] **Step 3: Registrar la app en settings**

En `backend/config/settings/base.py`, cambiar:

```python
LOCAL_APPS = [
    "accounts",
    "carreras",
    "materias",
]
```

por:

```python
LOCAL_APPS = [
    "accounts",
    "carreras",
    "materias",
    "asesorias",
]
```

- [ ] **Step 4: `models.py` con `PerfilAsesorAcademico`**

```python
# backend/asesorias/models.py
from django.core.exceptions import ValidationError
from django.db import models

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
```

(`DIAS_SEMANA`, `FORMATOS`, `ESTADOS_ASESORIA` se usan en tasks posteriores — decláralos aquí, una sola vez, al inicio del archivo.)

- [ ] **Step 5: Generar y aplicar la migración**

```bash
cd backend
uv run python manage.py makemigrations asesorias
uv run python manage.py migrate asesorias
```

Verifica que `backend/asesorias/migrations/0001_initial.py` tenga `CreateModel` para `PerfilAsesorAcademico` con FK a `carreras.Area` y OneToOne a `accounts.User`.

- [ ] **Step 6: Escribir los tests**

```python
# backend/asesorias/tests/test_perfil_asesor_academico.py
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico
from carreras.models import Area


class PerfilAsesorAcademicoTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")

    def test_requiere_perfil_academico(self):
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        asesor = PerfilAsesorAcademico(user=user, area=self.area)
        with self.assertRaises(ValidationError):
            asesor.clean()

    def test_se_crea_con_perfil_academico(self):
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        asesor = PerfilAsesorAcademico(user=user, area=self.area)
        asesor.clean()  # no lanza
        asesor.save()
        self.assertEqual(PerfilAsesorAcademico.objects.count(), 1)

    def test_un_user_no_puede_tener_dos_perfiles_de_asesor(self):
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        PerfilAsesorAcademico.objects.create(user=user, area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAsesorAcademico.objects.create(user=user, area=self.area)
```

- [ ] **Step 7: Correr los tests**

```bash
cd backend
uv run python manage.py test asesorias -v 2
```

Expected: `OK` (3 tests).

- [ ] **Step 8: `admin.py`**

```python
# backend/asesorias/admin.py
from django.contrib import admin

from .models import PerfilAsesorAcademico


@admin.register(PerfilAsesorAcademico)
class PerfilAsesorAcademicoAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "activo")
    list_filter = ("area", "activo")
    search_fields = ("user__email",)
```

- [ ] **Step 9: Verificar y commit**

```bash
cd backend
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

```bash
git add backend/asesorias/__init__.py backend/asesorias/apps.py backend/asesorias/models.py backend/asesorias/admin.py backend/asesorias/migrations backend/asesorias/tests backend/config/settings/base.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar app asesorias con modelo PerfilAsesorAcademico

- crear la app asesorias y registrarla en LOCAL_APPS
- agregar PerfilAsesorAcademico (OneToOne a User, área fija, requiere PerfilAcademico)
- agregar admin y tests de la validación de prerequisito y de unicidad

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 3: Modelo `RegistroAsesor`

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/admin.py`
- Create: `backend/asesorias/migrations/0002_registroasesor.py` (autogenerada)
- Test: `backend/asesorias/tests/test_registro_asesor.py`

**Interfaces:**
- Consumes: `asesorias.models.PerfilAsesorAcademico` (Task 2), `materias.models.Materia` (ya existe, con `carrera.area_id`, `habilitada_asesorias`, `ofertas`).
- Produces: `asesorias.models.RegistroAsesor` (`asesor: PerfilAsesorAcademico`, `semestre: str`, `materias: M2M[Materia]`, método `agregar_materia(materia) -> None`, lanza `ValidationError`).
- Consumidores futuros: Task 4 (`Disponibilidad.registro` FK).

- [ ] **Step 1: Agregar `RegistroAsesor` a `models.py`**

Después de `PerfilAsesorAcademico`:

```python
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
```

- [ ] **Step 2: Generar y aplicar la migración**

```bash
cd backend
uv run python manage.py makemigrations asesorias
uv run python manage.py migrate asesorias
```

- [ ] **Step 3: Escribir los tests**

```python
# backend/asesorias/tests/test_registro_asesor.py
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria


class RegistroAsesorTests(TestCase):
    def setUp(self):
        self.area_mate = Area.objects.create(nombre="Matemáticas")
        self.area_bio = Area.objects.create(nombre="Biología")
        self.carrera = Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area_mate)
        self.carrera_bio = Carrera.objects.create(clave=201, nombre="Biología", area=self.area_bio)

        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=user, area=self.area_mate)

        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def _materia(self, **overrides):
        defaults = dict(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        defaults.update(overrides)
        return Materia.objects.create(**defaults)

    def test_unique_asesor_semestre(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def test_agregar_materia_exitoso(self):
        materia = self._materia()
        OfertaMateria.objects.create(materia=materia, semestre="20271", se_imparte=True)
        self.registro.agregar_materia(materia)
        self.assertIn(materia, self.registro.materias.all())

    def test_agregar_materia_de_otra_area_falla(self):
        materia = self._materia(clave="2001", carrera=self.carrera_bio)
        OfertaMateria.objects.create(materia=materia, semestre="20271", se_imparte=True)
        with self.assertRaises(ValidationError):
            self.registro.agregar_materia(materia)
        self.assertNotIn(materia, self.registro.materias.all())

    def test_agregar_materia_no_habilitada_falla(self):
        materia = self._materia(clave="1802", habilitada_asesorias=False)
        OfertaMateria.objects.create(materia=materia, semestre="20271", se_imparte=True)
        with self.assertRaises(ValidationError):
            self.registro.agregar_materia(materia)

    def test_agregar_materia_sin_oferta_del_semestre_falla(self):
        materia = self._materia(clave="1803")
        with self.assertRaises(ValidationError):
            self.registro.agregar_materia(materia)
```

- [ ] **Step 4: Correr los tests**

```bash
cd backend
uv run python manage.py test asesorias.tests.test_registro_asesor -v 2
```

Expected: `OK` (5 tests).

- [ ] **Step 5: Registrar en el admin**

En `backend/asesorias/admin.py`, agregar:

```python
from .models import PerfilAsesorAcademico, RegistroAsesor


@admin.register(RegistroAsesor)
class RegistroAsesorAdmin(admin.ModelAdmin):
    list_display = ("asesor", "semestre")
    list_filter = ("semestre",)
    search_fields = ("asesor__user__email",)
    filter_horizontal = ("materias",)
```

(Actualiza el `from .models import PerfilAsesorAcademico` existente para incluir también `RegistroAsesor` en la misma línea, no lo dupliques.)

- [ ] **Step 6: Verificar y commit**

```bash
cd backend
uv run python manage.py check
```

```bash
git add backend/asesorias/models.py backend/asesorias/admin.py backend/asesorias/migrations backend/asesorias/tests/test_registro_asesor.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar modelo RegistroAsesor

- agregar RegistroAsesor (asesor+semestre único) con M2M a Materia
- agregar agregar_materia() que valida área, habilitada_asesorias y oferta del semestre antes de asociar
- agregar admin con filter_horizontal para materias
- agregar tests de unicidad y de las 3 validaciones de agregar_materia

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 4: Modelo `Disponibilidad`

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/admin.py`
- Create: `backend/asesorias/migrations/0003_disponibilidad.py` (autogenerada)
- Test: `backend/asesorias/tests/test_disponibilidad.py`

**Interfaces:**
- Consumes: `asesorias.models.RegistroAsesor` (Task 3).
- Produces: `asesorias.models.Disponibilidad` (`registro: RegistroAsesor`, `dia_semana: int`, `hora_inicio: time`, `formato: str`, `ubicacion: str`, `liga_virtual: str`, `activa: bool`, propiedad `hora_fin: time`, método `clean()`).
- Consumidores futuros: Task 5 (`Asesoria.disponibilidad` FK).

- [ ] **Step 1: Agregar `Disponibilidad` a `models.py`**

Al inicio del archivo, agrega el import de `datetime` (junto a los imports existentes):

```python
import datetime
```

Después de `RegistroAsesor`:

```python
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
```

- [ ] **Step 2: Generar y aplicar la migración**

```bash
cd backend
uv run python manage.py makemigrations asesorias
uv run python manage.py migrate asesorias
```

- [ ] **Step 3: Escribir los tests**

```python
# backend/asesorias/tests/test_disponibilidad.py
import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area


class DisponibilidadTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        asesor = PerfilAsesorAcademico.objects.create(user=user, area=area)
        self.registro = RegistroAsesor.objects.create(asesor=asesor, semestre="20271")

    def test_bloque_valido_presencial(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 3",
        )
        disp.clean()  # no lanza
        disp.save()
        self.assertEqual(disp.hora_fin, datetime.time(10, 30))

    def test_bloque_valido_virtual(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 30),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        disp.clean()  # no lanza

    def test_hora_fuera_de_rejilla_falla(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 15),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        with self.assertRaises(ValidationError):
            disp.clean()

    def test_presencial_sin_ubicacion_falla(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial",
        )
        with self.assertRaises(ValidationError):
            disp.clean()

    def test_virtual_sin_liga_falla(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual",
        )
        with self.assertRaises(ValidationError):
            disp.clean()

    def test_bloque_duplicado_falla(self):
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Disponibilidad.objects.create(
                registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
                formato="presencial", ubicacion="Salón 1",
            )

    def test_bloques_no_contiguos_del_mismo_dia(self):
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(9, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(14, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.assertEqual(self.registro.disponibilidades.count(), 2)
```

- [ ] **Step 4: Correr los tests**

```bash
cd backend
uv run python manage.py test asesorias.tests.test_disponibilidad -v 2
```

Expected: `OK` (7 tests).

- [ ] **Step 5: Registrar en el admin**

En `backend/asesorias/admin.py`:

```python
from .models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ("registro", "dia_semana", "hora_inicio", "formato", "activa")
    list_filter = ("dia_semana", "formato", "activa")
    search_fields = ("registro__asesor__user__email",)
```

- [ ] **Step 6: Verificar y commit**

```bash
cd backend
uv run python manage.py check
```

```bash
git add backend/asesorias/models.py backend/asesorias/admin.py backend/asesorias/migrations backend/asesorias/tests/test_disponibilidad.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar modelo Disponibilidad

- agregar Disponibilidad como slot discreto de 30 min (dia_semana, hora_inicio, formato)
- validar rejilla de 30 min y ubicacion/liga_virtual según formato en clean()
- agregar constraint unique_bloque_registro y propiedad hora_fin calculada
- agregar admin y tests de validación y del constraint

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 5: Modelo `Asesoria` con anti-doble-booking y métodos de ciclo de vida

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/admin.py`
- Create: `backend/asesorias/migrations/0004_asesoria.py` (autogenerada)
- Test: `backend/asesorias/tests/test_asesoria.py`

**Interfaces:**
- Consumes: `accounts.models.PerfilAlumno` (Task 1), `asesorias.models.Disponibilidad` (Task 4), `materias.models.Materia` (ya existe).
- Produces: `asesorias.models.Asesoria` (`alumno`, `disponibilidad`, `materia`, `fecha`, `hora_inicio`, `formato`, `ubicacion`, `liga_virtual`, `estado`, `asistio`, `notas`, `cancelado_por`, `motivo_cancelacion`, métodos `clean()`, `marcar_asistencia(asistio: bool)`, `guardar_notas(texto: str)`, `cancelar(usuario, motivo="")`).
- Consumidores futuros: Task 6 (señal `post_save` y `cancelar()` disparan tareas Celery).

- [ ] **Step 1: Agregar `Asesoria` a `models.py`**

Agrega el import de `timezone` junto a los existentes:

```python
from django.utils import timezone
```

Después de `Disponibilidad`:

```python
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

- [ ] **Step 2: Generar y aplicar la migración**

```bash
cd backend
uv run python manage.py makemigrations asesorias
uv run python manage.py migrate asesorias
```

Verifica que `backend/asesorias/migrations/0004_asesoria.py` incluya el `UniqueConstraint` condicional (`condition=models.Q(estado__in=["agendada", "realizada"])`) sobre `("disponibilidad", "fecha")`.

- [ ] **Step 3: Escribir los tests**

```python
# backend/asesorias/tests/test_asesoria.py
import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia


class AsesoriaTestsBase(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        carrera = Carrera.objects.create(clave=101, nombre="Actuaría", area=area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=asesor_user, numero_trabajador="12345")
        asesor = PerfilAsesorAcademico.objects.create(user=asesor_user, area=area)
        registro = RegistroAsesor.objects.create(asesor=asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(user=alumno_user, numero_cuenta="312345678")

        # Próximo lunes (dia_semana=0) en el pasado o futuro según el test lo necesite.
        self.proximo_lunes = self._proximo_dia_semana(0)
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        delta = delta or 7
        return hoy + datetime.timedelta(days=delta)

    def _crear_asesoria(self, fecha, **overrides):
        defaults = dict(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=fecha, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        defaults.update(overrides)
        return Asesoria.objects.create(**defaults)


class AsesoriaConstraintTests(AsesoriaTestsBase):
    def test_fecha_no_coincide_con_dia_semana_falla_en_clean(self):
        martes = self.proximo_lunes + datetime.timedelta(days=1)
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=martes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        with self.assertRaises(ValidationError):
            asesoria.clean()

    def test_doble_booking_mismo_slot_mismo_dia_falla(self):
        self._crear_asesoria(self.proximo_lunes)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._crear_asesoria(self.proximo_lunes)

    def test_slot_distinto_fecha_no_choca(self):
        self._crear_asesoria(self.proximo_lunes)
        otro_lunes = self.proximo_lunes + datetime.timedelta(days=7)
        self._crear_asesoria(otro_lunes)
        self.assertEqual(Asesoria.objects.count(), 2)

    def test_cancelar_libera_el_slot(self):
        asesoria = self._crear_asesoria(self.proximo_lunes)
        asesoria.cancelar(usuario=self.alumno.user)
        self._crear_asesoria(self.proximo_lunes)
        self.assertEqual(Asesoria.objects.filter(fecha=self.proximo_lunes).count(), 2)


class AsesoriaCicloDeVidaTests(AsesoriaTestsBase):
    def test_marcar_asistencia_antes_de_tiempo_falla(self):
        asesoria = self._crear_asesoria(self.proximo_lunes)
        with self.assertRaises(ValidationError):
            asesoria.marcar_asistencia(True)

    def test_marcar_asistencia_despues_de_la_fecha(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(True)
        asesoria.refresh_from_db()
        self.assertTrue(asesoria.asistio)
        self.assertEqual(asesoria.estado, "realizada")

    def test_guardar_notas_sin_asistencia_falla(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        with self.assertRaises(ValidationError):
            asesoria.guardar_notas("texto")

    def test_guardar_notas_con_asistencia_confirmada(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(True)
        asesoria.guardar_notas("Repasamos series de Taylor.")
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.notas, "Repasamos series de Taylor.")

    def test_guardar_notas_con_asistencia_falsa_falla(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(False)
        with self.assertRaises(ValidationError):
            asesoria.guardar_notas("texto")

    def test_cancelar_sesion_no_agendada_falla(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(True)
        with self.assertRaises(ValidationError):
            asesoria.cancelar(usuario=self.alumno.user)
```

- [ ] **Step 4: Correr los tests**

```bash
cd backend
uv run python manage.py test asesorias.tests.test_asesoria -v 2
```

Expected: `OK` (10 tests).

- [ ] **Step 5: Registrar en el admin**

En `backend/asesorias/admin.py`:

```python
from .models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor


@admin.register(Asesoria)
class AsesoriaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "materia", "fecha", "hora_inicio", "estado", "asistio")
    list_filter = ("estado", "formato", "materia")
    search_fields = ("alumno__user__email", "alumno__numero_cuenta")
```

- [ ] **Step 6: Verificar y commit**

```bash
cd backend
uv run python manage.py check
```

```bash
git add backend/asesorias/models.py backend/asesorias/admin.py backend/asesorias/migrations backend/asesorias/tests/test_asesoria.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar modelo Asesoria con anti-doble-booking

- agregar Asesoria con snapshot de formato/ubicacion/liga_virtual al agendar
- agregar UniqueConstraint condicional (disponibilidad, fecha) excluyendo canceladas
- agregar marcar_asistencia/guardar_notas/cancelar con las reglas de negocio del alcance
- agregar admin y tests de doble-booking, ciclo de vida y de las reglas de asistencia/notas

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 6: Notificaciones por email vía Celery

**Files:**
- Create: `backend/asesorias/tasks.py`
- Create: `backend/asesorias/signals.py`
- Modify: `backend/asesorias/apps.py`
- Modify: `backend/asesorias/models.py` (método `cancelar()`)
- Modify: `backend/config/settings/base.py` (Celery eager en tests)
- Test: `backend/asesorias/tests/test_notificaciones.py`

**Interfaces:**
- Consumes: `asesorias.models.Asesoria` (Task 5), `celery.shared_task` (patrón ya usado en `backend/config/celery.py`).
- Produces: `asesorias.tasks.enviar_confirmacion_agenda(asesoria_id: int)`, `asesorias.tasks.enviar_notificacion_cancelacion(asesoria_id: int)` — ambas tareas Celery (`shared_task`), invocables como `.delay(id)`.

**⚠️ Riesgo que este task introduce:** a partir de aquí, *toda* creación de `Asesoria` dispara la señal `post_save` y llama `.delay(...)`, incluida cada `Asesoria` creada en los tests del Task 5 (`test_asesoria.py`) que no mockean la tarea — sin ajuste, esas llamadas intentan conectarse al broker de Celery real (Redis) durante `manage.py test`. El Step 1 de este task lo resuelve activando modo eager solo durante `manage.py test`, sin tocar el comportamiento de dev/prod.

- [ ] **Step 1: Activar Celery eager durante `manage.py test`**

En `backend/config/settings/base.py`, agrega el import de `sys` junto a los imports existentes, y después del bloque `CELERY_*` ya existente (líneas ~157-161):

```python
# Evita que las tareas Celery disparadas por señales (ej. asesorias.signals)
# intenten conectarse a un broker real durante `manage.py test`.
CELERY_TASK_ALWAYS_EAGER = "test" in sys.argv
CELERY_TASK_EAGER_PROPAGATES = True
```

- [ ] **Step 2: `tasks.py`**

```python
# backend/asesorias/tasks.py
from celery import shared_task
from django.core.mail import send_mail


@shared_task
def enviar_confirmacion_agenda(asesoria_id: int):
    from asesorias.models import Asesoria

    asesoria = Asesoria.objects.select_related(
        "alumno__user", "disponibilidad__registro__asesor__user", "materia"
    ).get(id=asesoria_id)
    asesor_email = asesoria.disponibilidad.registro.asesor.user.email
    send_mail(
        subject=f"Asesoría confirmada — {asesoria.materia.nombre} — {asesoria.fecha}",
        message=(
            f"Se agendó una asesoría de {asesoria.materia.nombre} el {asesoria.fecha} "
            f"a las {asesoria.hora_inicio}."
        ),
        from_email=None,
        recipient_list=[asesoria.alumno.user.email, asesor_email],
    )


@shared_task
def enviar_notificacion_cancelacion(asesoria_id: int):
    from asesorias.models import Asesoria

    asesoria = Asesoria.objects.select_related(
        "alumno__user", "disponibilidad__registro__asesor__user", "materia"
    ).get(id=asesoria_id)
    asesor_email = asesoria.disponibilidad.registro.asesor.user.email
    send_mail(
        subject=f"Asesoría cancelada — {asesoria.materia.nombre} — {asesoria.fecha}",
        message=(
            f"Se canceló la asesoría de {asesoria.materia.nombre} del {asesoria.fecha} "
            f"a las {asesoria.hora_inicio}. Motivo: {asesoria.motivo_cancelacion or 'no especificado'}."
        ),
        from_email=None,
        recipient_list=[asesoria.alumno.user.email, asesor_email],
    )
```

- [ ] **Step 3: `signals.py`**

```python
# backend/asesorias/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Asesoria
from .tasks import enviar_confirmacion_agenda


@receiver(post_save, sender=Asesoria)
def notificar_agenda(sender, instance, created, **kwargs):
    if created:
        enviar_confirmacion_agenda.delay(instance.id)
```

- [ ] **Step 4: Conectar la señal en `apps.py`**

```python
# backend/asesorias/apps.py
from django.apps import AppConfig


class AsesoriasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "asesorias"

    def ready(self):
        from . import signals  # noqa: F401
```

- [ ] **Step 5: Disparar la notificación de cancelación en `cancelar()`**

En `backend/asesorias/models.py`, modifica el método `cancelar` de `Asesoria`:

```python
    def cancelar(self, usuario, motivo=""):
        if self.estado != "agendada":
            raise ValidationError("Solo se puede cancelar una sesión agendada.")
        self.estado = "cancelada"
        self.cancelado_por = usuario
        self.motivo_cancelacion = motivo
        self.save()
        from asesorias.tasks import enviar_notificacion_cancelacion
        enviar_notificacion_cancelacion.delay(self.id)
```

(El import de `tasks` se hace dentro del método, no al inicio del archivo, para evitar un import circular — `tasks.py` importa `Asesoria` de `models.py` dentro de cada función por la misma razón.)

- [ ] **Step 6: Escribir los tests**

Los tests usan `unittest.mock.patch` sobre `.delay` para no requerir un worker de Celery ni Redis corriendo.

```python
# backend/asesorias/tests/test_notificaciones.py
import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia


class NotificacionesTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        carrera = Carrera.objects.create(clave=101, nombre="Actuaría", area=area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=asesor_user, numero_trabajador="12345")
        asesor = PerfilAsesorAcademico.objects.create(user=asesor_user, area=area)
        registro = RegistroAsesor.objects.create(asesor=asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(user=alumno_user, numero_cuenta="312345678")

        hoy = timezone.localdate()
        delta = (0 - hoy.weekday()) % 7 or 7
        self.proximo_lunes = hoy + datetime.timedelta(days=delta)

    @patch("asesorias.tasks.enviar_confirmacion_agenda.delay")
    def test_crear_asesoria_encola_confirmacion(self, mock_delay):
        asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        mock_delay.assert_called_once_with(asesoria.id)

    @patch("asesorias.tasks.enviar_notificacion_cancelacion.delay")
    @patch("asesorias.tasks.enviar_confirmacion_agenda.delay")
    def test_cancelar_encola_notificacion_de_cancelacion(self, _mock_confirmacion, mock_cancelacion):
        asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        asesoria.cancelar(usuario=self.alumno.user)
        mock_cancelacion.assert_called_once_with(asesoria.id)
```

- [ ] **Step 7: Correr los tests**

```bash
cd backend
uv run python manage.py test asesorias.tests.test_notificaciones -v 2
```

Expected: `OK` (2 tests).

- [ ] **Step 8: Verificar y commit**

```bash
cd backend
uv run python manage.py check
```

```bash
git add backend/asesorias/tasks.py backend/asesorias/signals.py backend/asesorias/apps.py backend/asesorias/models.py backend/asesorias/tests/test_notificaciones.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar notificaciones por email de Asesoria vía Celery

- agregar tareas Celery enviar_confirmacion_agenda y enviar_notificacion_cancelacion
- disparar confirmación vía señal post_save al crear una Asesoria
- disparar notificación de cancelación desde Asesoria.cancelar()
- agregar tests que verifican el encolado con mocks de .delay, sin requerir worker real

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 7: Verificación final

**Files:** ninguno nuevo — solo verificación de extremo a extremo.

- [ ] **Step 1: Migrar desde cero en una BD limpia**

```bash
cd backend
docker compose -f ../docker-compose.dev.yml down -v postgres
docker compose -f ../docker-compose.dev.yml up -d postgres
uv run python manage.py migrate
```

Expected: todas las migraciones de `accounts`, `carreras`, `materias` y `asesorias` aplican sin error.

- [ ] **Step 2: Correr la suite completa**

```bash
cd backend
uv run python manage.py test -v 2
```

Expected: `OK` — incluye los tests preexistentes de `accounts`/`carreras`/`materias` más los de `asesorias` (27 tests: 3+5+7+10+2).

- [ ] **Step 3: `manage.py check` sin advertencias**

```bash
cd backend
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Revisión manual vía admin**

```bash
cd backend
uv run python manage.py createsuperuser --email admin@ciencias.unam.mx
uv run python manage.py runserver
```

En `http://localhost:8000/admin/`: crear un `PerfilAsesorAcademico` (requiere primero un `User` con `PerfilAcademico`), un `RegistroAsesor` con al menos una materia de su área agregada vía shell (`registro.agregar_materia(materia)`, el admin no expone el método de validación directamente — `filter_horizontal` permite asociar materias sin esa validación, es una limitación conocida del admin dejada fuera de alcance), un par de `Disponibilidad`, y una `Asesoria` de prueba. Confirmar en el admin que un segundo intento de crear otra `Asesoria` sobre la misma `Disponibilidad`+fecha lanza error de integridad.

No requiere commit — es solo verificación de que las 6 tareas anteriores integran correctamente.
