# Catálogo académico (apps `carreras` y `materias`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar el catálogo académico de la Facultad de Ciencias (Area, Carrera, Materia, OfertaMateria) como dos apps Django nuevas, con datos sembrados de las 9 carreras reales y comandos de carga idempotentes para el catálogo de materias y su oferta semestral.

**Architecture:** Dos apps de dominio siguiendo el layout de la ADR 0011 (`backend/carreras/`, `backend/materias/`), sin capa DRF propia en esta pasada — es infraestructura de datos consumida más adelante por el servicio de Asesorías Académicas. `materias` depende de `carreras` vía FK cruzada (`Materia.carrera`); `carreras` no depende de `materias`.

**Tech Stack:** Django 6.0, PostgreSQL 16 (`django.contrib.postgres.fields.ArrayField` para `Carrera.alias`), `uv` como gestor de paquetes del backend.

## Global Constraints

- Layout de apps: directo en `backend/<nombre>/`, no bajo `backend/apps/` (ADR 0011).
- `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` en cada `AppConfig`, igual que `accounts`.
- Commits atómicos, formato `[type][scope] resumen` + bullets + `git commit -s` (Signed-off-by), ver `docs/development/commit-conventions.md`.
- Todo comando se ejecuta desde `backend/` con `uv run python manage.py ...` (settings de dev vía `DJANGO_SETTINGS_MODULE=config.settings.dev`, ya configurado en `backend/.env`).
- La base de datos de dev/test es Postgres real (`docker compose -f docker-compose.dev.yml up -d postgres`, requerido antes de `migrate`/`test`) — no SQLite, porque `ArrayField` es específico de Postgres.
- No se agregan endpoints DRF, serializers ni vistas en este plan — fuera de alcance (ver spec).

---

## File Structure

```
backend/carreras/
  __init__.py
  apps.py
  models.py
  admin.py
  migrations/
    __init__.py
    0001_initial.py
    0002_seed_areas_carreras.py
  tests/
    __init__.py
    test_models.py

backend/materias/
  __init__.py
  apps.py
  models.py
  admin.py
  migrations/
    __init__.py
    0001_initial.py
  management/
    __init__.py
    commands/
      __init__.py
      cargar_materias.py
      cargar_oferta.py
  tests/
    __init__.py
    test_models.py
    test_cargar_materias.py
    test_cargar_oferta.py

backend/config/settings/base.py   (modificado: LOCAL_APPS)
```

---

### Task 1: App `carreras` — modelos `Area` y `Carrera`

**Files:**
- Create: `backend/carreras/__init__.py`
- Create: `backend/carreras/apps.py`
- Create: `backend/carreras/models.py`
- Modify: `backend/config/settings/base.py` (agregar `"carreras"` a `LOCAL_APPS`)
- Create: `backend/carreras/migrations/__init__.py`
- Create: `backend/carreras/migrations/0001_initial.py` (autogenerada)
- Test: `backend/carreras/tests/__init__.py`
- Test: `backend/carreras/tests/test_models.py`

**Interfaces:**
- Produces: `carreras.models.Area` (`nombre: str`), `carreras.models.Carrera` (`clave: int`, `nombre: str`, `area: Area`, `alias: list[str]`, `acepta_nuevo_ingreso: bool`, `siass_id: int | None`, `siassypp_id: int | None`, `dgeci_id: int | None`), `carreras.models.CarreraManager.resolve(texto: str) -> Carrera` (lanza `Carrera.DoesNotExist` si no matchea `nombre` ni `alias`, normalizando acentos/mayúsculas).
- Consumidores futuros: Task 5 (`Materia.carrera` FK), Task 7 (`cargar_materias` usa `Carrera.objects.resolve(...)`).

- [ ] **Step 1: Crear el paquete de la app**

```bash
mkdir -p backend/carreras/migrations backend/carreras/tests
touch backend/carreras/__init__.py backend/carreras/migrations/__init__.py backend/carreras/tests/__init__.py
```

- [ ] **Step 2: `apps.py`**

```python
# backend/carreras/apps.py
from django.apps import AppConfig


class CarrerasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "carreras"
```

- [ ] **Step 3: Registrar la app en settings**

En `backend/config/settings/base.py`, cambiar:

```python
LOCAL_APPS = [
    "accounts",
]
```

por:

```python
LOCAL_APPS = [
    "accounts",
    "carreras",
]
```

- [ ] **Step 4: `models.py` con `Area`, `Carrera` y su manager**

```python
# backend/carreras/models.py
import unicodedata

from django.contrib.postgres.fields import ArrayField
from django.db import models


def normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_acentos.strip().upper()


class Area(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


class CarreraManager(models.Manager):
    def resolve(self, texto: str) -> "Carrera":
        objetivo = normalizar(texto)
        for carrera in self.all():
            if normalizar(carrera.nombre) == objetivo:
                return carrera
            if objetivo in [normalizar(a) for a in carrera.alias]:
                return carrera
        raise Carrera.DoesNotExist(f"No se encontró la carrera '{texto}'")


class Carrera(models.Model):
    clave = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=150, unique=True)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="carreras")
    alias = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    acepta_nuevo_ingreso = models.BooleanField(default=True)
    siass_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    siassypp_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    dgeci_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    objects = CarreraManager()

    def __str__(self):
        return self.nombre
```

- [ ] **Step 5: Generar y aplicar la migración inicial**

```bash
cd backend
docker compose -f ../docker-compose.dev.yml up -d postgres
uv run python manage.py makemigrations carreras
uv run python manage.py migrate carreras
```

Verifica que `backend/carreras/migrations/0001_initial.py` tenga `CreateModel` para `Area` y `Carrera` con los campos de Step 4 (incluyendo `alias` como `django.contrib.postgres.fields.ArrayField`).

- [ ] **Step 6: Escribir los tests de unicidad y de `resolve()`**

```python
# backend/carreras/tests/test_models.py
from django.db import IntegrityError, transaction
from django.test import TestCase

from carreras.models import Area, Carrera


class CarreraUnicidadTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")

    def test_clave_unica(self):
        Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=101, nombre="Otra", area=self.area)

    def test_nombre_unico(self):
        Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=102, nombre="Actuaría", area=self.area)

    def test_ids_externos_nulos_no_chocan_entre_si(self):
        Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area)
        # dos carreras sin siass_id no deben violar la unicidad (NULL != NULL en Postgres)
        Carrera.objects.create(clave=102, nombre="Biología", area=self.area)


class CarreraResolveTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        self.actuaria = Carrera.objects.create(
            clave=101, nombre="Actuaría", area=area, alias=["ACTUARIA", "ACT"]
        )

    def test_resolve_por_nombre_exacto(self):
        self.assertEqual(Carrera.objects.resolve("Actuaría"), self.actuaria)

    def test_resolve_por_alias_sin_acentos_ni_mayusculas(self):
        self.assertEqual(Carrera.objects.resolve("actuaria"), self.actuaria)

    def test_resolve_no_encontrada(self):
        with self.assertRaises(Carrera.DoesNotExist):
            Carrera.objects.resolve("Carrera Inexistente")
```

- [ ] **Step 7: Correr los tests**

```bash
cd backend
uv run python manage.py test carreras -v 2
```

Expected: `OK` (6 tests).

- [ ] **Step 8: Commit**

```bash
git add backend/carreras backend/config/settings/base.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar app carreras con modelos Area y Carrera

- agregar modelos Area y Carrera con clave/alias/IDs externos (siass, siassypp, dgeci)
- agregar CarreraManager.resolve() para matching por nombre o alias
- registrar carreras en LOCAL_APPS y agregar migración inicial
- agregar tests de unicidad y de resolve()

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 2: Admin de `carreras`

**Files:**
- Create: `backend/carreras/admin.py`

**Interfaces:**
- Consumes: `carreras.models.Area`, `carreras.models.Carrera` (Task 1).

- [ ] **Step 1: `admin.py`**

```python
# backend/carreras/admin.py
from django.contrib import admin

from .models import Area, Carrera


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "area", "acepta_nuevo_ingreso")
    list_filter = ("area", "acepta_nuevo_ingreso")
    search_fields = ("clave", "nombre")
```

- [ ] **Step 2: Verificar manualmente**

```bash
cd backend
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add backend/carreras/admin.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] registrar Area y Carrera en el admin

- agregar CarreraAdmin y AreaAdmin con list_display/search_fields por clave/nombre

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 3: Sembrar las 3 áreas y 9 carreras reales

**Files:**
- Create: `backend/carreras/migrations/0002_seed_areas_carreras.py`

**Interfaces:**
- Consumes: `carreras.models.Area`, `carreras.models.Carrera` (Task 1).
- Produces: filas reales en BD — 3 `Area` (Matemáticas, Física, Biología), 9 `Carrera` con `clave`/`alias`/IDs externos tomados de `models.gs` (`CAREERS()`).

- [ ] **Step 1: Escribir la data migration**

```python
# backend/carreras/migrations/0002_seed_areas_carreras.py
from django.db import migrations

AREAS = ["Matemáticas", "Física", "Biología"]

# (clave, nombre, area, alias, acepta_nuevo_ingreso, siass_id, dgeci_id, siassypp_id)
CARRERAS = [
    (101, "Actuaría", "Matemáticas", ["ACTUARIA", "ACT"], True, 1, 11, 1),
    (201, "Biología", "Biología", ["BIOLOGIA", "BIO"], True, 28, 16, 39),
    (104, "Ciencias de la Computación", "Matemáticas",
     ["CIENCIAS DE LA COMPUTACION", "C. COMPUTACION", "CC"], True, 4, 12, 4),
    (127, "Ciencias de la Tierra", "Física", [
        "CIENCIAS DE LA TIERRA",
        "CIENCIAS DE LA TIERRA - CAMPUS CU",
        "CIENCIAS DE LA TIERRA - CU",
        "CIENCIAS DE LA TIERRA - JURIQUILLA",
        "CIENCIAS DE LA TIERRA - CAMPUS JURIQUILLA",
        "CIENCIAS DE LA TIERRA, CIENCIAS ACUATICAS",
        "CIENCIAS DE LA TIERRA, CIENCIAS AMBIENTALES",
        "CIENCIAS DE LA TIERRA, CIENCIAS ATMOSFERICAS",
        "CIENCIAS DE LA TIERRA, CIENCIAS ESPACIALES",
        "CIENCIAS DE LA TIERRA, CIENCIAS DE LA TIERRA SOLIDA",
        "CT",
    ], False, 27, 15, 27),
    (106, "Física", "Física", ["FISICA", "FIS"], True, 6, 13, 6),
    (134, "Física Biomédica", "Física", ["FISICA BIOMEDICA", "FB"], True, 96, 10, 34),
    (217, "Manejo Sustentable de Zonas Costeras", "Biología", [
        "MANEJO SUSTENTABLE DE ZONAS COSTERAS", "MANEJO SUSTENTABLE", "MSZC",
    ], False, 44, 17, 55),
    (122, "Matemáticas", "Matemáticas", ["MATEMATICAS", "MAT"], True, 22, 14, 22),
    (136, "Matemáticas Aplicadas", "Matemáticas",
     ["MATEMATICAS APLICADAS", "APLICADAS", "MA"], True, 119, 182, 36),
]


def sembrar(apps, schema_editor):
    Area = apps.get_model("carreras", "Area")
    Carrera = apps.get_model("carreras", "Carrera")

    areas_por_nombre = {}
    for nombre in AREAS:
        areas_por_nombre[nombre], _ = Area.objects.get_or_create(nombre=nombre)

    for clave, nombre, area_nombre, alias, nuevo_ingreso, siass_id, dgeci_id, siassypp_id in CARRERAS:
        Carrera.objects.get_or_create(
            clave=clave,
            defaults={
                "nombre": nombre,
                "area": areas_por_nombre[area_nombre],
                "alias": alias,
                "acepta_nuevo_ingreso": nuevo_ingreso,
                "siass_id": siass_id,
                "dgeci_id": dgeci_id,
                "siassypp_id": siassypp_id,
            },
        )


def despoblar(apps, schema_editor):
    Area = apps.get_model("carreras", "Area")
    Carrera = apps.get_model("carreras", "Carrera")
    Carrera.objects.filter(clave__in=[c[0] for c in CARRERAS]).delete()
    Area.objects.filter(nombre__in=AREAS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("carreras", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sembrar, despoblar),
    ]
```

- [ ] **Step 2: Aplicar la migración**

```bash
cd backend
uv run python manage.py migrate carreras
```

- [ ] **Step 3: Escribir un test que verifique el seed**

```python
# backend/carreras/tests/test_seed.py
from django.test import TestCase

from carreras.models import Area, Carrera


class SeedAreasCarrerasTests(TestCase):
    def test_tres_areas(self):
        self.assertEqual(Area.objects.count(), 3)
        self.assertTrue(Area.objects.filter(nombre="Matemáticas").exists())
        self.assertTrue(Area.objects.filter(nombre="Física").exists())
        self.assertTrue(Area.objects.filter(nombre="Biología").exists())

    def test_nueve_carreras(self):
        self.assertEqual(Carrera.objects.count(), 9)

    def test_ciencias_de_la_tierra_sin_nuevo_ingreso(self):
        carrera = Carrera.objects.get(clave=127)
        self.assertFalse(carrera.acepta_nuevo_ingreso)
        self.assertEqual(carrera.area.nombre, "Física")

    def test_actuaria_en_area_matematicas_con_ids_externos(self):
        carrera = Carrera.objects.get(clave=101)
        self.assertEqual(carrera.area.nombre, "Matemáticas")
        self.assertEqual(carrera.siass_id, 1)
        self.assertEqual(carrera.dgeci_id, 11)
        self.assertEqual(carrera.siassypp_id, 1)
```

Nota: como las migraciones ya insertaron los datos en la BD de test (se aplican todas las migraciones antes de correr tests), este test no necesita fixtures adicionales — solo lee lo que la migración de Step 1 sembró.

- [ ] **Step 4: Correr los tests**

```bash
cd backend
uv run python manage.py test carreras -v 2
```

Expected: `OK` (10 tests: los 6 de Task 1 + los 4 nuevos).

- [ ] **Step 5: Commit**

```bash
git add backend/carreras/migrations/0002_seed_areas_carreras.py backend/carreras/tests/test_seed.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] sembrar áreas y carreras reales de la Facultad

- agregar data migration con las 3 áreas y las 9 carreras (clave, alias, IDs externos)
- agregar tests que verifican el seed

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 4: App `materias` — modelos `Materia` y `OfertaMateria`

**Files:**
- Create: `backend/materias/__init__.py`
- Create: `backend/materias/apps.py`
- Create: `backend/materias/models.py`
- Modify: `backend/config/settings/base.py` (agregar `"materias"` a `LOCAL_APPS`)
- Create: `backend/materias/migrations/__init__.py`
- Create: `backend/materias/migrations/0001_initial.py` (autogenerada)
- Test: `backend/materias/tests/__init__.py`
- Test: `backend/materias/tests/test_models.py`

**Interfaces:**
- Consumes: `carreras.models.Carrera` (Task 1).
- Produces: `materias.models.Materia` (`clave: str`, `nombre: str`, `carrera: Carrera`, `nivel: int | None`, `plan: int`, `habilitada_asesorias: bool`), `materias.models.OfertaMateria` (`materia: Materia`, `semestre: str`, `se_imparte: bool`, constraint única `(materia, semestre)`).
- Consumidores futuros: Task 7 (`cargar_materias`), Task 8 (`cargar_oferta`).

- [ ] **Step 1: Crear el paquete de la app**

```bash
mkdir -p backend/materias/migrations backend/materias/tests
touch backend/materias/__init__.py backend/materias/migrations/__init__.py backend/materias/tests/__init__.py
```

- [ ] **Step 2: `apps.py`**

```python
# backend/materias/apps.py
from django.apps import AppConfig


class MateriasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "materias"
```

- [ ] **Step 3: Registrar la app en settings**

En `backend/config/settings/base.py`:

```python
LOCAL_APPS = [
    "accounts",
    "carreras",
    "materias",
]
```

- [ ] **Step 4: `models.py`**

```python
# backend/materias/models.py
from django.db import models


class Materia(models.Model):
    clave = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    carrera = models.ForeignKey(
        "carreras.Carrera", on_delete=models.PROTECT, related_name="materias"
    )
    nivel = models.PositiveSmallIntegerField(null=True, blank=True)
    plan = models.PositiveIntegerField()
    habilitada_asesorias = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.clave} — {self.nombre}"


class OfertaMateria(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT, related_name="ofertas")
    semestre = models.CharField(max_length=5)
    se_imparte = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["materia", "semestre"], name="unique_oferta_materia_semestre"
            )
        ]

    def __str__(self):
        return f"{self.materia.clave} — {self.semestre}"
```

- [ ] **Step 5: Generar y aplicar la migración**

```bash
cd backend
uv run python manage.py makemigrations materias
uv run python manage.py migrate materias
```

Verifica que `backend/materias/migrations/0001_initial.py` tenga `dependencies = [("carreras", "0001_initial")]` (por la FK a `Carrera`) y el `UniqueConstraint` de `OfertaMateria`.

- [ ] **Step 6: Escribir los tests de unicidad y constraint**

```python
# backend/materias/tests/test_models.py
from django.db import IntegrityError, transaction
from django.test import TestCase

from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria


class MateriaClaveUnicaTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        self.carrera = Carrera.objects.create(clave=101, nombre="Actuaría", area=area)

    def test_clave_unica(self):
        Materia.objects.create(
            clave="1801", nombre="Administración Actuarial", carrera=self.carrera,
            nivel=8, plan=2006,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Materia.objects.create(
                clave="1801", nombre="Otra materia", carrera=self.carrera,
                nivel=1, plan=2006,
            )

    def test_nivel_nulo_es_optativa(self):
        materia = Materia.objects.create(
            clave="1817", nombre="Administración de Riesgos", carrera=self.carrera,
            nivel=None, plan=2006,
        )
        self.assertIsNone(materia.nivel)


class OfertaMateriaConstraintTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        carrera = Carrera.objects.create(clave=101, nombre="Actuaría", area=area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Administración Actuarial", carrera=carrera,
            nivel=8, plan=2006,
        )

    def test_una_oferta_por_materia_y_semestre(self):
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=False)

    def test_misma_materia_en_semestres_distintos(self):
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)
        OfertaMateria.objects.create(materia=self.materia, semestre="20272", se_imparte=False)
        self.assertEqual(self.materia.ofertas.count(), 2)
```

- [ ] **Step 7: Correr los tests**

```bash
cd backend
uv run python manage.py test materias -v 2
```

Expected: `OK` (4 tests).

- [ ] **Step 8: Commit**

```bash
git add backend/materias backend/config/settings/base.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar app materias con modelos Materia y OfertaMateria

- agregar Materia (clave única, FK a Carrera) y OfertaMateria (constraint materia+semestre)
- registrar materias en LOCAL_APPS y agregar migración inicial
- agregar tests de unicidad y del constraint de OfertaMateria

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 5: Admin de `materias`

**Files:**
- Create: `backend/materias/admin.py`

**Interfaces:**
- Consumes: `materias.models.Materia`, `materias.models.OfertaMateria` (Task 4).

- [ ] **Step 1: `admin.py`**

```python
# backend/materias/admin.py
from django.contrib import admin

from .models import Materia, OfertaMateria


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "carrera", "nivel", "plan", "habilitada_asesorias")
    list_filter = ("carrera", "habilitada_asesorias")
    search_fields = ("clave", "nombre")


@admin.register(OfertaMateria)
class OfertaMateriaAdmin(admin.ModelAdmin):
    list_display = ("materia", "semestre", "se_imparte")
    list_filter = ("semestre", "se_imparte")
    search_fields = ("materia__clave", "materia__nombre")
```

- [ ] **Step 2: Verificar**

```bash
cd backend
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add backend/materias/admin.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] registrar Materia y OfertaMateria en el admin

- agregar MateriaAdmin y OfertaMateriaAdmin con list_display/search_fields por clave

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 6: Management command `cargar_materias`

**Files:**
- Create: `backend/materias/management/__init__.py`
- Create: `backend/materias/management/commands/__init__.py`
- Create: `backend/materias/management/commands/cargar_materias.py`
- Test: `backend/materias/tests/test_cargar_materias.py`

**Interfaces:**
- Consumes: `carreras.models.Carrera.objects.resolve(texto: str) -> Carrera` (Task 1), `materias.models.Materia` (Task 4).
- Produces: comando `python manage.py cargar_materias <csv_path>`, invocable en tests vía `django.core.management.call_command("cargar_materias", csv_path)`.

- [ ] **Step 1: Crear el paquete de management commands**

```bash
mkdir -p backend/materias/management/commands
touch backend/materias/management/__init__.py backend/materias/management/commands/__init__.py
```

- [ ] **Step 2: Escribir el comando**

CSV esperado con columnas exactas `Carrera,Clave,Materia,Nivel,Plan` (`Nivel` puede venir vacío = optativa).

```python
# backend/materias/management/commands/cargar_materias.py
import csv

from django.core.management.base import BaseCommand

from carreras.models import Carrera
from materias.models import Materia


class Command(BaseCommand):
    help = "Carga o actualiza el catálogo de materias desde un CSV (columnas: Carrera,Clave,Materia,Nivel,Plan)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        creadas = 0
        actualizadas = 0
        errores = 0

        with open(options["csv_path"], newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for numero_fila, fila in enumerate(lector, start=2):
                try:
                    carrera = Carrera.objects.resolve(fila["Carrera"])
                except Carrera.DoesNotExist as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                nivel_texto = fila["Nivel"].strip()
                _, creada = Materia.objects.update_or_create(
                    clave=fila["Clave"].strip(),
                    defaults={
                        "nombre": fila["Materia"].strip(),
                        "carrera": carrera,
                        "nivel": int(nivel_texto) if nivel_texto else None,
                        "plan": int(fila["Plan"].strip()),
                    },
                )
                if creada:
                    creadas += 1
                else:
                    actualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Materias: {creadas} creadas, {actualizadas} actualizadas, {errores} filas con error"
            )
        )
```

- [ ] **Step 3: Escribir los tests**

```python
# backend/materias/tests/test_cargar_materias.py
import csv
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from carreras.models import Area, Carrera
from materias.models import Materia


def escribir_csv(filas):
    archivo = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    escritor = csv.DictWriter(archivo, fieldnames=["Carrera", "Clave", "Materia", "Nivel", "Plan"])
    escritor.writeheader()
    escritor.writerows(filas)
    archivo.close()
    return archivo.name


class CargarMateriasTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        Carrera.objects.create(clave=101, nombre="Actuaría", area=area, alias=["ACT"])

    def test_crea_materias_nuevas(self):
        csv_path = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Administración Actuarial",
             "Nivel": "8", "Plan": "2006"},
            {"Carrera": "ACT", "Clave": "1817", "Materia": "Administración de Riesgos",
             "Nivel": "", "Plan": "2006"},
        ])

        call_command("cargar_materias", csv_path)

        self.assertEqual(Materia.objects.count(), 2)
        optativa = Materia.objects.get(clave="1817")
        self.assertIsNone(optativa.nivel)
        self.assertEqual(optativa.carrera.clave, 101)

    def test_correr_dos_veces_es_idempotente(self):
        csv_path = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Administración Actuarial",
             "Nivel": "8", "Plan": "2006"},
        ])

        call_command("cargar_materias", csv_path)
        call_command("cargar_materias", csv_path)

        self.assertEqual(Materia.objects.count(), 1)

    def test_actualiza_materia_existente(self):
        csv_path = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Nombre viejo",
             "Nivel": "8", "Plan": "2006"},
        ])
        call_command("cargar_materias", csv_path)

        csv_path_v2 = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Nombre corregido",
             "Nivel": "8", "Plan": "2006"},
        ])
        call_command("cargar_materias", csv_path_v2)

        materia = Materia.objects.get(clave="1801")
        self.assertEqual(materia.nombre, "Nombre corregido")
        self.assertEqual(Materia.objects.count(), 1)

    def test_fila_con_carrera_no_reconocida_no_crea_materia_ni_aborta(self):
        csv_path = escribir_csv([
            {"Carrera": "Carrera Inexistente", "Clave": "9999", "Materia": "No debe crearse",
             "Nivel": "1", "Plan": "2006"},
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Administración Actuarial",
             "Nivel": "8", "Plan": "2006"},
        ])

        call_command("cargar_materias", csv_path)

        self.assertFalse(Materia.objects.filter(clave="9999").exists())
        self.assertTrue(Materia.objects.filter(clave="1801").exists())
```

- [ ] **Step 4: Correr los tests**

```bash
cd backend
uv run python manage.py test materias.tests.test_cargar_materias -v 2
```

Expected: `OK` (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/materias/management backend/materias/tests/test_cargar_materias.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar comando cargar_materias

- agregar management command que hace upsert de Materia por clave desde un CSV
- resolver la carrera de cada fila por nombre o alias, reportando errores por fila sin abortar
- agregar tests de creación, actualización, idempotencia y fila con carrera no reconocida

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 7: Management command `cargar_oferta`

**Files:**
- Create: `backend/materias/management/commands/cargar_oferta.py`
- Test: `backend/materias/tests/test_cargar_oferta.py`

**Interfaces:**
- Consumes: `materias.models.Materia`, `materias.models.OfertaMateria` (Task 4).
- Produces: comando `python manage.py cargar_oferta <semestre> <csv_path>`.

- [ ] **Step 1: Escribir el comando**

CSV esperado con columnas `Clave,SeImparte` (`SeImparte` acepta `1`/`0`, `true`/`false`, `si`/`no`, case-insensitive).

```python
# backend/materias/management/commands/cargar_oferta.py
import csv

from django.core.management.base import BaseCommand

from materias.models import Materia, OfertaMateria

VALORES_VERDADEROS = {"1", "TRUE", "SI", "SÍ"}


class Command(BaseCommand):
    help = "Carga la oferta de materias de un semestre desde un CSV (columnas: Clave,SeImparte)"

    def add_arguments(self, parser):
        parser.add_argument("semestre")
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        semestre = options["semestre"]
        creadas = 0
        actualizadas = 0
        errores = 0

        with open(options["csv_path"], newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for numero_fila, fila in enumerate(lector, start=2):
                clave = fila["Clave"].strip()
                try:
                    materia = Materia.objects.get(clave=clave)
                except Materia.DoesNotExist:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: no existe una Materia con clave '{clave}'")
                    continue

                se_imparte = fila["SeImparte"].strip().upper() in VALORES_VERDADEROS
                _, creada = OfertaMateria.objects.update_or_create(
                    materia=materia,
                    semestre=semestre,
                    defaults={"se_imparte": se_imparte},
                )
                if creada:
                    creadas += 1
                else:
                    actualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Oferta {semestre}: {creadas} creadas, {actualizadas} actualizadas, {errores} filas con error"
            )
        )
```

- [ ] **Step 2: Escribir los tests**

```python
# backend/materias/tests/test_cargar_oferta.py
import csv
import tempfile

from django.core.management import call_command
from django.test import TestCase

from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria


def escribir_csv(filas):
    archivo = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    escritor = csv.DictWriter(archivo, fieldnames=["Clave", "SeImparte"])
    escritor.writeheader()
    escritor.writerows(filas)
    archivo.close()
    return archivo.name


class CargarOfertaTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        carrera = Carrera.objects.create(clave=101, nombre="Actuaría", area=area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Administración Actuarial", carrera=carrera,
            nivel=8, plan=2006,
        )

    def test_crea_oferta_nueva(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])

        call_command("cargar_oferta", "20271", csv_path)

        oferta = OfertaMateria.objects.get(materia=self.materia, semestre="20271")
        self.assertTrue(oferta.se_imparte)

    def test_correr_dos_veces_es_idempotente(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])

        call_command("cargar_oferta", "20271", csv_path)
        call_command("cargar_oferta", "20271", csv_path)

        self.assertEqual(
            OfertaMateria.objects.filter(materia=self.materia, semestre="20271").count(), 1
        )

    def test_actualiza_se_imparte_del_mismo_semestre(self):
        csv_path_v1 = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])
        call_command("cargar_oferta", "20271", csv_path_v1)

        csv_path_v2 = escribir_csv([{"Clave": "1801", "SeImparte": "0"}])
        call_command("cargar_oferta", "20271", csv_path_v2)

        oferta = OfertaMateria.objects.get(materia=self.materia, semestre="20271")
        self.assertFalse(oferta.se_imparte)

    def test_semestres_distintos_no_se_pisan(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])
        call_command("cargar_oferta", "20271", csv_path)
        call_command("cargar_oferta", "20272", csv_path)

        self.assertEqual(OfertaMateria.objects.filter(materia=self.materia).count(), 2)

    def test_fila_con_clave_no_reconocida_no_crea_oferta_ni_aborta(self):
        csv_path = escribir_csv([
            {"Clave": "9999", "SeImparte": "1"},
            {"Clave": "1801", "SeImparte": "1"},
        ])

        call_command("cargar_oferta", "20271", csv_path)

        self.assertEqual(OfertaMateria.objects.filter(materia=self.materia).count(), 1)
```

- [ ] **Step 3: Correr los tests**

```bash
cd backend
uv run python manage.py test materias.tests.test_cargar_oferta -v 2
```

Expected: `OK` (5 tests).

- [ ] **Step 4: Commit**

```bash
git add backend/materias/management/commands/cargar_oferta.py backend/materias/tests/test_cargar_oferta.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar comando cargar_oferta

- agregar management command que hace upsert de OfertaMateria por (materia, semestre) desde un CSV
- agregar tests de creación, idempotencia, actualización, semestres separados y clave no reconocida

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 8: Verificación final

**Files:** ninguno nuevo — solo verificación de extremo a extremo.

- [ ] **Step 1: Migrar desde cero en una BD limpia**

```bash
cd backend
docker compose -f ../docker-compose.dev.yml down -v postgres
docker compose -f ../docker-compose.dev.yml up -d postgres
uv run python manage.py migrate
```

Expected: todas las migraciones de `accounts`, `carreras` y `materias` aplican sin error, incluida la data migration `0002_seed_areas_carreras`.

- [ ] **Step 2: Correr la suite completa**

```bash
cd backend
uv run python manage.py test -v 2
```

Expected: `OK` — incluye los tests preexistentes de `accounts` más los de `carreras` (10) y `materias` (13).

- [ ] **Step 3: Confirmar que el seed quedó en la BD de dev**

```bash
cd backend
uv run python manage.py shell -c "from carreras.models import Carrera; print(Carrera.objects.count())"
```

Expected: `9`.

- [ ] **Step 4: `manage.py check` sin advertencias**

```bash
cd backend
uv run python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

No requiere commit — es solo verificación de que las 7 tareas anteriores integran correctamente.
