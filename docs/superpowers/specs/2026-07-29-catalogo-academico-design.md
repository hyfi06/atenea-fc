## Catálogo académico (Area, Carrera, Materia, OfertaMateria)

**Status:** Approved
**Date:** 2026-07-29

### Context

Primer servicio funcional de producción de Atenea: **Asesorías Académicas** (Programa Institucional de Tutorías, independiente de Tutorías). Antes de diseñar Asesorías, hace falta el catálogo académico del que depende — carreras, áreas y materias de la Facultad de Ciencias — porque:

- Un académico registrado como asesor elige un área de adscripción fija y un subconjunto de materias.
- Un alumno agenda eligiendo su carrera activa.
- Las materias se ofrecen o no cada semestre, y ese histórico debe conservarse (sirve también a futuros servicios como movilidad entrante).

Este catálogo se diseña como infraestructura reusable, desacoplada de la lógica de negocio de Asesorías Académicas (que tendrá su propia spec y ADR posteriores).

Contexto de dominio (aportado por el usuario, capturado aquí porque no es derivable del código):

- 9 carreras en la Facultad de Ciencias, 7 con nuevo ingreso y 2 sin nuevo ingreso (Ciencias de la Tierra, Manejo Sustentable de Zonas Costeras).
- Las carreras se agrupan en 3 áreas para fines de Asesorías: Matemáticas (Actuaría, Ciencias de la Computación, Matemáticas, Matemáticas Aplicadas), Física (Física, Física Biomédica, Ciencias de la Tierra), Biología (Biología, Manejo Sustentable de Zonas Costeras) — esta agrupación por área es más simple que la adscripción departamental real de los académicos (4 departamentos de Biología, por ejemplo), y existe solo para simplificar el registro de asesores.
- Una Materia se comparte en la práctica entre varias carreras/departamentos, pero la Facultad la responsabiliza administrativamente a una sola carrera — de ahí que `Materia.carrera` sea FK simple, no M2M.
- El sistema legado en Google Apps Script (`models.gs`, adjuntado por el usuario) ya modela `Carrera` con una clave oficial (`id`, ej. 101, 201) y referencias a los sistemas SIASS, SIASS-YPP (2025+) y DGECI — esos IDs externos son necesarios para trámites interinstitucionales y se preservan en Atenea.

### Decisions captured

1. **Dos apps Django**: `carreras` (Area, Carrera) y `materias` (Materia, OfertaMateria) — elegido sobre una sola app `catalogo` combinada; separa el ciclo de vida de las carreras (casi estático) del de materias (catálogo grande, se recarga por semestre).
2. **`Carrera.alias`** como `ArrayField(CharField)` de Postgres — no un modelo `CarreraAlias` aparte; son ~2-3 variantes fijas por carrera usadas solo para matching de imports, no se consultan como filas independientes.
3. **`Carrera.clave`** (el `id` de `models.gs`, ej. 101) es un campo de negocio requerido, `unique=True`, distinto de la PK autogenerada de Django — es la clave oficial usada en trámites entre sistemas.
4. **`Materia.clave`** es la llave natural: única globalmente, no compuesta con carrera ni plan (confirmado explícitamente por el usuario, corrige una propuesta anterior de llave compuesta).
5. **`OfertaMateria`** historiza la oferta por semestre vía `unique_together(materia, semestre)` + carga idempotente (`update_or_create`) — nunca se borran ni sobrescriben filas de semestres ya cerrados; una corrección dentro del semestre en curso sí actualiza esa fila.
6. **`Materia.habilitada_asesorias`** es el único flag de servicio agregado ahora (YAGNI) — flags de futuros servicios (ej. movilidad entrante) se agregan como campos propios cuando ese servicio exista, no se preconstruye un sistema genérico.
7. **Carga de datos**: `Area`/`Carrera` vía data migration (datos fijos, ~9 filas, sembrados desde `models.gs`); `Materia`/`OfertaMateria` vía management commands (`cargar_materias`, `cargar_oferta`) que leen CSV y hacen upsert idempotente por clave natural.
8. **Django admin**: los 4 modelos se registran en `admin.py` de su app respectiva (list_display/search_fields por clave/nombre) para correcciones puntuales sin repasar el CSV completo.

### Data model

```python
# backend/carreras/models.py

class Area(models.Model):
    nombre = models.CharField(max_length=50, unique=True)


class Carrera(models.Model):
    clave = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=150, unique=True)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="carreras")
    alias = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    acepta_nuevo_ingreso = models.BooleanField(default=True)
    siass_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    siassypp_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    dgeci_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
```

```python
# backend/materias/models.py

class Materia(models.Model):
    clave = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    carrera = models.ForeignKey("carreras.Carrera", on_delete=models.PROTECT, related_name="materias")
    nivel = models.PositiveSmallIntegerField(null=True, blank=True)  # null = optativa
    plan = models.PositiveIntegerField()
    habilitada_asesorias = models.BooleanField(default=False)


class OfertaMateria(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT, related_name="ofertas")
    semestre = models.CharField(max_length=5)  # formato AAAAN, ej. "20271"
    se_imparte = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["materia", "semestre"], name="unique_oferta_materia_semestre")
        ]
```

### Data flow

- **Seed inicial** (`carreras`): data migration con las 3 áreas y las 9 carreras (clave, nombre, area, alias, acepta_nuevo_ingreso, IDs externos) tomadas de `CAREERS()` en `models.gs`.
- **Carga por semestre** (`materias`): `python manage.py cargar_materias <csv>` — upsert por `clave` de las columnas Carrera/Clave/Materia/Nivel/Plan. `python manage.py cargar_oferta <semestre> <csv>` — upsert por `(materia, semestre)` marcando `se_imparte`.
- **Consumo futuro** (Asesorías Académicas, spec aparte): filtra `Materia` por `habilitada_asesorias=True` intersectado con `OfertaMateria` del semestre activo con `se_imparte=True`, y por el área del asesor vía `materia.carrera.area`.

### Error handling

- `clave` duplicada (Carrera o Materia) → `IntegrityError` de la constraint `unique`, capturado en el management command y reportado por fila sin abortar el resto del archivo.
- Fila de CSV con `carrera` que no matchea ninguna `Carrera.alias`/`nombre` → error reportado por fila, no crea la `Materia`, no aborta el comando completo.
- `OfertaMateria` para un semestre ya cerrado no tiene mecanismo de "reapertura" en esta spec — si hace falta corregir un semestre pasado, es una operación manual vía Django admin, no vía el comando de carga masiva.

### Testing

- `carreras/tests/`: unicidad de `clave`/`nombre`/IDs externos; matching de alias.
- `materias/tests/`: unicidad de `clave`; constraint `(materia, semestre)` de `OfertaMateria`; idempotencia de `cargar_materias`/`cargar_oferta` (correr el mismo CSV dos veces no duplica ni falla).

### Out of scope

- El servicio de Asesorías Académicas en sí (`PerfilAsesorAcademico`, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) — spec y ADR independientes, construidos sobre este catálogo.
- UI de carga de materias/oferta — por ahora es CLI (management command) + Django admin para correcciones puntuales.
- Cambios a `accounts.User` (split de `apellido1`/`apellido2`) — relacionado pero independiente, no es parte de este catálogo.
- Validación de "límite de materias fuera de plan" — confirmado por el usuario que no aplica a Asesorías, pertenece a otro sistema.

### Self-review

- Sin placeholders/TBD — cada decisión tiene un valor concreto.
- Alcance cohesivo: un solo catálogo (2 apps estrechamente relacionadas), no se mezcla con Asesorías Académicas.
- Sin contradicciones entre esta spec y la ADR 0015 asociada.
