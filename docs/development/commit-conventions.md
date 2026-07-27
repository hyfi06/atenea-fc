# Convención de mensajes de commit

## Formato

```
[type][scope] resumen

- descripción de cambio 1
- descripción de cambio 2

Signed-off-by: Nombre Apellido <email>
```

- **`[type]`** (obligatorio) — uno de los tipos definidos abajo, entre corchetes.
- **`[scope]`** (opcional) — parte del monorepo afectada: `backend`, `frontend`, `docs`, `infra`, u otro nombre de módulo/servicio de la SAE conforme se integren. Se omite si el cambio no aplica a un área específica.
- **resumen** — una línea, en imperativo, describiendo el cambio.
- **lista de cambios** — uno o más bullets con el detalle de qué cambió. Si el commit es verdaderamente atómico, puede ser un solo bullet.
- **Signed-off-by** — generado con `git commit -s`, certifica autoría del cambio (DCO).

## Tipos

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad para el usuario final (no para el build/tooling). |
| `fix` | Corrección de un bug para el usuario final (no un fix al build/tooling). |
| `docs` | Cambios de documentación. |
| `style` | Formato, punto y comas faltantes, etc.; sin cambio de código de producción. |
| `refactor` | Refactor de código de producción, ej. renombrar una variable. |
| `test` | Agregar pruebas faltantes o refactorizar pruebas; sin cambio de código de producción. |
| `chore` | Tareas de mantenimiento (build scripts, dependencias, etc.); sin cambio de código de producción. |

## Atomicidad

Cada commit debe representar el cambio más pequeño y coherente posible: un commit, una razón de cambio. Evitar mezclar tipos distintos (ej. un `refactor` junto con un `feat`) en el mismo commit — si un cambio necesita ambos, son dos commits.

## Ejemplos

```
[feat][backend] agregar endpoint de login con Google OAuth

- agregar vista DRF para intercambio de código OAuth por JWT
- registrar ruta en urls.py

Signed-off-by: User <user@test.com>
```

```
[docs] documentar convención de mensajes de commit

- agregar docs/development/commit-conventions.md
- agregar ADR 0007

Signed-off-by: User <user@test.com>
```
