# Carga del catálogo académico (materias y oferta)

La app `materias` incluye dos management commands para cargar/actualizar datos desde CSV: `cargar_materias` (catálogo de materias) y `cargar_oferta` (oferta por semestre). Ambos son idempotentes (`update_or_create`) — correr el mismo CSV dos veces no duplica registros — y procesan el archivo fila por fila: una fila con error se reporta y se salta, no aborta el resto de la carga.

## `cargar_materias`

Carga o actualiza el catálogo de `Materia`, resolviendo cada fila contra una `Carrera` ya existente.

```
uv run manage.py cargar_materias ruta/al/archivo.csv
```

En el flujo con Docker Compose:

```
docker compose -f docker-compose.dev.yml exec backend python manage.py cargar_materias ruta/al/archivo.csv
```

### Formato del CSV

Columnas requeridas (encabezado exacto): `Carrera,Clave,Materia,Nivel,Plan`.

| Columna | Descripción |
|---|---|
| `Carrera` | Nombre o alias de la carrera. Se resuelve con `Carrera.objects.resolve`, que normaliza (sin acentos, mayúsculas) y compara contra `nombre` y `alias` de cada `Carrera`. |
| `Clave` | Clave única de la materia (`Materia.clave`). Determina si la fila crea o actualiza un registro. |
| `Materia` | Nombre de la materia. |
| `Nivel` | Entero (semestre/nivel dentro del plan). Puede ir vacío — se guarda como `NULL` (ej. materias optativas). |
| `Plan` | Año del plan de estudios, entero. |

Ejemplo:

```csv
Carrera,Clave,Materia,Nivel,Plan
Actuaría,1801,Administración Actuarial,8,2006
Actuaría,1817,Administración de Riesgos,,2006
```

### Comportamiento

- Requiere que la `Carrera` ya exista (por nombre o alias); si no se reconoce, la fila se cuenta como error y se reporta en stderr, sin crear la `Materia`.
- Si `Clave` ya existe, actualiza `nombre`, `carrera`, `nivel` y `plan` del registro existente.
- Al terminar, imprime un resumen (`Materias: N creadas, M actualizadas, E filas con error`).
- Si hubo errores en alguna fila, el comando termina con `CommandError` (código de salida distinto de cero) aunque las filas válidas ya se hayan guardado — útil para detectarlo en scripts/CI.
- Un CSV con columnas faltantes en el encabezado, o una ruta de archivo inexistente, abortan antes de procesar cualquier fila.

## `cargar_oferta`

Carga o actualiza si una `Materia` se imparte (`OfertaMateria`) en un semestre dado.

```
uv run manage.py cargar_oferta <semestre> ruta/al/archivo.csv
```

Ejemplo:

```
uv run manage.py cargar_oferta 20271 oferta-2027-1.csv
```

### Argumentos

- `semestre` — formato `AAAAN` (año de 4 dígitos + `1` o `2`, ej. `20271`). Un formato inválido aborta el comando antes de leer el CSV.
- `csv_path` — ruta al archivo CSV.

### Formato del CSV

Columnas requeridas (encabezado exacto): `Clave,SeImparte`.

| Columna | Descripción |
|---|---|
| `Clave` | Clave de una `Materia` ya cargada (ver `cargar_materias`). Si no existe, la fila se cuenta como error. |
| `SeImparte` | Valor booleano en texto. Verdadero: `1`, `TRUE`, `SI`. Falso: `0`, `FALSE`, `NO`. Sin distinguir mayúsculas/acentos (se normaliza igual que `Carrera.objects.resolve`). Cualquier otro valor es un error. |

Ejemplo:

```csv
Clave,SeImparte
1801,1
1817,NO
```

### Comportamiento

- Requiere que la `Materia` (`Clave`) ya exista; si no, la fila se cuenta como error y se reporta en stderr.
- La combinación `(materia, semestre)` es única: correr el mismo semestre de nuevo actualiza `se_imparte` en vez de duplicar.
- Semestres distintos para la misma materia no se pisan entre sí.
- Al terminar, imprime un resumen (`Oferta <semestre>: N creadas, M actualizadas, E filas con error`).
- Igual que `cargar_materias`: si hubo errores de fila, termina con `CommandError` aunque las filas válidas ya se hayan guardado; encabezado inválido o archivo inexistente abortan antes de procesar filas.
