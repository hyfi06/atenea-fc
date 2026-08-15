## Usuarios reales — Home por rol, historial académico multi-carrera, autoservicio de asesor

**Status:** Approved
**Date:** 2026-08-15

### Context

Atenea va a tener usuarios reales por primera vez. Esto expone tres huecos que hasta ahora eran aceptables porque no había datos ni usuarios reales detrás:

1. **Home (`frontend/src/screens/Home.tsx`) pinta 9 servicios mock** (`frontend/src/data/services.ts`: Orientación Vocacional, Tutorías, Becas, Idiomas, Servicio Social, Bolsa de Trabajo, Movilidad, Voluntariado, Prácticas) a **cualquier usuario, sin backend detrás** — el comentario del propio archivo ya avisa que es temporal, pendiente de ADR 0012. Además, Home solo tiene un tile condicionado por rol (`esMiembroSAE` → `/sae/asesorias`); **ni alumno ni académico tienen ninguna entrada a `/asesorias`**, aunque esas rutas y pantallas ya existen (`App.tsx`: `/asesorias`, `/asesorias/materias`, `/asesorias/horario`, guardadas por `RutaDeAsesorias`/`RutaDeAsesor`).
2. **`PerfilAlumno` (`backend/accounts/models.py`) asume una sola carrera y un solo correo por alumno.** La carga real de alumnos incluye casos con dos carreras simultáneas/segunda carrera bajo el mismo número de cuenta, y correos alternos conocidos por la SAE además del correo de login. Esto es exactamente la señal de revisión que ya anticipaba la [deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md).
3. **El alta de asesor es 100% manual** ([deuda 0002](../../technical-debt/0002-alta-perfil-asesor-solo-admin.md)) y **la oferta no está acotada a un semestre vigente real** ([deuda 0001](../../technical-debt/0001-sin-modelo-calendario-academico.md), [deuda 0012](../../technical-debt/0012-oferta-asesorias-sin-scope-de-semestre.md)). Para abrir producción al semestre 20271, los asesores necesitan poder registrarse ellos mismos, y el sistema necesita saber que 20271 es efectivamente el semestre vigente y que su ventana de registro está abierta.

**Estado actual del código (referencias verificadas):**
- `PerfilAlumno(user OneToOne, numero_cuenta único, carrera FK, generacion)` — `backend/accounts/models.py`.
- `PerfilAsesorAcademico(user OneToOne, area FK, activo)` y `RegistroAsesor(asesor FK, semestre CharField, materias M2M)` — `backend/asesorias/models.py`. `RegistroAsesor.agregar_materia` ya valida que la materia esté habilitada y ofertada ese semestre.
- Roles se derivan por existencia de perfil; `UserDetailsSerializer.get_roles` (`backend/accounts/serializers.py:109-124`) ya arma `roles` incluyendo `"academico"` (por `perfil_academico`), pero **ningún hook de frontend lo consume todavía** — `frontend/src/auth/rol.ts` solo expone `useEsAsesor` (`asesor_academico`), `useEsAlumno`, `useEsMiembroSAE`.
- `frontend/src/features/asesorias/logica.ts::semestreActual(hoy)` calcula la clave `AAAAN` con una heurística de fecha (corregida en `1533d53`, fix de "primer semestre del año próximo" durante el segundo semestre calendario) — es la única fuente de "semestre actual" hoy, y solo existe en frontend.
- Precedente de carga masiva: `backend/materias/management/commands/cargar_materias.py` — CSV, upsert por llave natural con `update_or_create`, reporta creadas/actualizadas/errores por fila sin abortar la carga completa.
- `Materia.habilitada_asesorias` y `OfertaMateria` (semestre, se_imparte) ya historizan oferta por semestre — no se tocan aquí.

**Prerrequisito de modelo:** migraciones para `HistoriaAcademica`, `PerfilAlumno.correos_alternos`, `PeriodoAcademico`, y los cambios de `PerfilAsesorAcademico`/`RegistroAsesor` que habilita el autoservicio. Se detallan en Decisions.

### Decisions captured

1. **`HistoriaAcademica` reemplaza `PerfilAlumno.carrera`/`generacion`.** Nuevo modelo `HistoriaAcademica(perfil_alumno FK a PerfilAlumno, carrera FK a Carrera, generacion)`, sin `unique_together` sobre `perfil_alumno` (un alumno puede tener más de una fila — carrera simultánea o segunda carrera bajo el mismo `numero_cuenta`). `PerfilAlumno.carrera` y `PerfilAlumno.generacion` se **eliminan** del modelo; deja de haber una "carrera activa" denormalizada. Resuelve la [deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md) — se marca como Resuelta al mergear. `Asesoria.carrera` sigue siendo un snapshot independiente (sin cambios, mismo patrón que hoy).
2. **Selección de carrera al agendar.** Cuando `HistoriaAcademica` tiene más de una fila para el alumno, `AgendarAsesoria` (frontend) debe pedir con qué carrera agenda esa sesión antes del `POST`. Con una sola fila, se usa esa sin preguntar. El backend no infiere: `Asesoria.carrera` sigue viniendo explícito en el payload (contrato ya existente, ADR 0021).
3. **`PerfilAlumno.correos_alternos`.** `ArrayField(EmailField, blank=True, default=list)`. Guarda correos conocidos por la SAE además del correo de login (`User.email`, que sigue siendo único y la única llave de autenticación — sin cambios a ADR 0003/0019). Visible **solo** en Django admin y en cualquier endpoint restringido a `perfil_sae`; el propio alumno nunca lo ve en su serializer de perfil. No se usa para resolver login.
4. **`cargar_alumnos` (management command, CSV).** Mismo patrón que `cargar_materias`: upsert por `numero_cuenta`, sin self-service ni endpoint — lo corre quien tenga acceso al servidor. Escribe a tres modelos por fila: `User` (correo principal / identidad), `PerfilAlumno` (`numero_cuenta`, agrega a `correos_alternos` sin duplicar), `HistoriaAcademica` (upsert por `(perfil_alumno, carrera)` — una fila nueva si la carrera no existía para ese alumno). Reporta creados/actualizados/errores por fila, no aborta la carga completa por una fila mala.
   **STOP en el plan de implementación:** antes de escribir el comando, definir con Héctor las columnas exactas del CSV real disponible y el mapeo columna → campo (qué va a `User`, qué a `PerfilAlumno`, qué a `HistoriaAcademica`).
5. **`PeriodoAcademico`.** Nuevo modelo: `semestre` (CharField `AAAAN`, único), `fecha_inicio`, `fecha_fin`, `registro_asesores_inicio`, `registro_asesores_fin`. Se gestiona desde Django admin (alta/edición manual por la SAE cada semestre), igual criterio que `PerfilSAE`/`PerfilAsesorAcademico` hoy. No modela subdivisiones internas (periodo de exámenes, etc.) — deja la [deuda 0001](../../technical-debt/0001-sin-modelo-calendario-academico.md) parcialmente resuelta (hay fechas reales de semestre y de ventana de registro de asesores; no hay más granularidad que esa).
6. **`semestreActual` se porta a backend y se expone vía API.** La función pura (misma heurística ya corregida en `logica.ts`) se reimplementa en Python (p. ej. `academico/servicios.py` o donde viva `PeriodoAcademico`). Nuevo endpoint de solo lectura `GET /api/academico/periodo-vigente/` devuelve el detalle (`{semestre, fecha_inicio, fecha_fin, registro_asesores_inicio, registro_asesores_fin, registro_asesores_abierto}`) del `PeriodoAcademico` cuya clave coincide con la heurística — 404 si no existe ese `PeriodoAcademico` todavía (la SAE no lo ha dado de alta). El frontend sigue calculando la clave con su propia copia de la función (para no depender de una llamada de red solo para mostrar la etiqueta "2027-1") y consulta este endpoint para el detalle/ventanas. Resuelve la [deuda 0012](../../technical-debt/0012-oferta-asesorias-sin-scope-de-semestre.md): `OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` acotan al semestre vigente derivado de aquí, no solo a `Disponibilidad.activa`.
7. **Autoservicio de `PerfilAsesorAcademico`.** Un usuario con `PerfilAcademico` sin `PerfilAsesorAcademico` puede solicitar ser asesor desde la app: elige `area`. Esto **cierra la deuda 0002** (deja de ser alta-solo-admin). La activación (`activo=True`) depende de confirmar que el académico está vigente consultando un **servicio externo** cuyo contrato aún no está definido.
   **STOP en el plan de implementación:** antes de construir esta pieza, definir con Héctor los datos de conexión y el contrato de ese servicio externo (endpoint, autenticación, forma de la respuesta). Hasta entonces, el modelo/endpoint de solicitud puede construirse dejando el punto de validación como una interfaz clara (p. ej. una función `validar_academico_activo(numero_trabajador) -> bool` con un stub), sin integrarlo de verdad.
8. **Autoservicio de `RegistroAsesor` del semestre vigente.** Un usuario con `PerfilAsesorAcademico` (recién creado o preexistente) puede crear su `RegistroAsesor` para el semestre vigente y cargar materias + disponibilidad desde la app — reusa `MisMaterias`/`MiHorario` (ya existen) más una pantalla de alta si no tiene registro todavía. Solo alcanzable mientras `PeriodoAcademico.registro_asesores_inicio <= hoy <= registro_asesores_fin` para el semestre vigente; fuera de esa ventana, la pantalla de registro no se ofrece (las pantallas de gestión de un registro ya existente — `MisMaterias`/`MiHorario` de semestres pasados — no se restringen por esto).
9. **`useEsAcademico()` en frontend.** Nuevo hook en `auth/rol.ts` (`roles.includes('academico')`), simétrico a los existentes. Sin esto, un académico sin `PerfilAsesorAcademico` todavía no tiene forma de saber que puede entrar a registrarse.
10. **Home deja de pintar los 9 mocks.** `Home.tsx` deja de importar/renderizar `services.ts`. Tiles reales, cada uno gateado por rol:
    - **Asesorías** (`/asesorias`) — visible si `useEsAlumno()` o `useEsAcademico()`. Es la entrada que hoy falta para ambos roles.
    - **Panel SAE** (`/sae/asesorias`) — visible si `useEsMiembroSAE()` (sin cambio de comportamiento, solo se mueve de "el único tile" a "uno más").
    - Si ningún tile aplica al usuario: leyenda "Aún no contamos con servicios para ti." en vez de una grilla vacía.
    `services.ts` y sus íconos (`IconOrientacionVocacional`, etc.) quedan sin consumidores — se decide en el plan si se borran o se documentan como deuda técnica para cuando esos servicios existan de verdad.

### Resources & endpoints

```
# Nuevo
GET  /api/academico/periodo-vigente/        # detalle del PeriodoAcademico vigente (404 si no existe aún)

# Nuevo (autoservicio de asesor — contrato exacto de activación depende del STOP de decisión 7)
POST /api/asesorias/asesores/solicitud/      # { area } -> crea PerfilAsesorAcademico (activo pendiente de validación externa)
POST /api/asesorias/registros/               # { semestre? } -> crea RegistroAsesor del semestre vigente para el asesor autenticado

# Modificados (acotar a semestre vigente, deuda 0012)
GET  /api/asesorias/oferta/
GET  /api/asesorias/oferta/{materia_id}/asesores/
GET  /api/asesorias/disponibilidad/buscar/

# Sin cambios de endpoint, cambia el modelo detrás
GET  /api/auth/user/                         # roles ya incluye "academico"; sin cambios de forma
```

Forma de respuesta nueva:

```
# GET /api/academico/periodo-vigente/
{ "semestre": "20271", "fecha_inicio": "2027-01-11", "fecha_fin": "2027-05-28",
  "registro_asesores_inicio": "2026-12-01", "registro_asesores_fin": "2027-01-18",
  "registro_asesores_abierto": true }
```

### Out of scope (esta iteración)

- Límites de uso en Asesorías ([deuda 0003](../../technical-debt/0003-sin-limites-uso-asesorias.md)), cierre automático de sesiones vencidas ([deuda 0004](../../technical-debt/0004-sin-cierre-automatico-recordatorios.md)), propagación de `Disponibilidad` editada a sesiones ya agendadas ([deuda 0005](../../technical-debt/0005-editar-disponibilidad-no-propaga.md)), paginación de listados ([deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md)), validación de materia-del-registro al agendar ([deuda 0013](../../technical-debt/0013-agendar-sin-validar-materia-del-registro.md)), curación no-manual de `habilitada_asesorias` ([deuda 0016](../../technical-debt/0016-habilitar-asesorias-manual-en-admin.md)).
- Alta self-service de `PerfilSAE` ([deuda 0014](../../technical-debt/0014-alta-perfil-sae-solo-admin.md)) — sigue admin-only, no se tocó.
- Subdivisiones del calendario académico más allá de fechas de semestre + ventana de registro de asesores (periodo de exámenes, vacaciones, etc.) — la deuda 0001 queda parcialmente resuelta, no cerrada.
- Catálogo real de los 9 servicios mock retirados de Home — se retiran, no se reemplazan por nada todavía.
- Contrato final del servicio externo de validación de académico activo — explícitamente diferido a un STOP dentro del plan de implementación.
