# Diseño de Spec — Flujo de Asesorías Académicas (Vista de Asesor)

**Fecha:** 2026-08-01
**Status:** En progreso (Fase 1)

---

## Contexto

### Por qué este plan

El backend de asesorías académicas está completo (ADR-0016 modelos, ADR-0017 API DRF) y probado end-to-end, incluida la implementación de cookies httpOnly en producción (ADR-0018, cerrado 2026-08-01). El frontend, en cambio, es un scaffold: `Login.tsx` navega directo a `/home` sin llamar a la API, `api/client.ts` solo tiene un `apiGet` sin manejo de auth, y no existe ni una sola pantalla, hook o componente relacionado con asesorías. Se decidió (ver Decisiones de alcance) construir primero el flujo de **asesor** — registro de disponibilidad semanal y gestión del ciclo de vida de sus sesiones — dejando búsqueda/booking de alumno y los tableros de solo-lectura de administración para fases posteriores, cada una con su propio spec y plan.

Como el flujo de asesor requiere sesión autenticada y no hay ninguna pantalla protegida hoy, este plan incluye como prerequisito construir el wiring real de autenticación (Google OAuth vía GIS, login por email/contraseña, cliente HTTP con `POST`/`PATCH`/`DELETE`, refresh silencioso, rutas protegidas) — decisión explícita del usuario en brainstorming, en vez de asumir que existe en otro plan.

---

## Decisiones de alcance

1. **Fase 1 (este plan, a detalle):** vista de asesor — registrar disponibilidad del semestre, ver asesorías (próximas/historial), detalle con notas de sesiones previas del mismo alumno, cancelar/marcar asistencia/notas.
2. **Fase 2 (fuera de este plan):** vista de alumno — buscar asesorías por materia, ver asesores/disponibilidad disponibles, agendar.
3. **Fase 3 (fuera de este plan):** vista de administración — lista de asesores por semestre (solo lectura de su disponibilidad y asesorías), lista de alumnos que han solicitado asesorías por semestre.

---

## Gaps de API descubiertos

Durante la exploración se confirmaron dos vacíos de contrato que **no se resuelven aquí** por decisión explícita del usuario ("backend aparte, documéntalo como deuda técnica"):

1. **`AsesoriaSerializer` solo expone IDs planos** (`alumno`, `materia`, `carrera`, `disponibilidad`), sin nombre. `materia`/`carrera` se resuelven en el frontend contra los catálogos de solo lectura ya existentes (`/api/materias/materias/`, `/api/carreras/carreras/`) — sin costo extra, ya se cargan para otros fines. **`alumno` no tiene ninguna vía de resolución**: no existe endpoint que exponga `PerfilAlumno.user.first_name` a un tercero (el asesor). La UI de este plan muestra `"Alumno #<id>"` como placeholder.
2. **`/api/auth/user/` no expone qué perfil (rol) tiene el usuario autenticado.** No hay forma de saber "este usuario es asesor" sin sondear un endpoint exclusivo de asesor y leer el código de estado. Este plan implementa ese sondeo como solución interina (Task 5).

Ambos comparten causa raíz (la API no expone información de perfil más allá de lo que el propio dueño del perfil puede ver de sí mismo vía `/api/auth/user/`). Se registra deuda técnica correspondiente (0010) **referenciada explícitamente en qué tareas dependen de él** para que sea buscable antes de que el costo del workaround se vuelva indispensable de resolver (cuando se construya la Fase 3, el sondeo por-rol no escala a "admin ve todos los roles").

Hay un tercer gap, más chico, encontrado al leer `backend/asesorias/serializers.py` directamente: `AsesoriaSerializer.Meta.fields` tampoco incluye `motivo_cancelacion` ni `cancelado_por`, aunque ambos existen en el modelo `Asesoria` y se llenan en `cancelar()`. A diferencia de los otros dos gaps, este no es "falta un endpoint de un tercero" — es simplemente que el serializer no expone dos campos del propio objeto que el asesor ya puede ver. Se documenta en el mismo ítem de deuda técnica (0010) y la UI diseña el panel de "cancelada" sin depender de `motivo_cancelacion`, ya que el campo nunca llega al frontend con el contrato actual.

---

## Decisiones de arquitectura

| Decisión | Elegida | Alternativa descartada | Por qué |
|---|---|---|---|
| Estado de servidor | TanStack Query | Hooks manuales (`useState`+`useEffect` por pantalla) | Da `isPending`/`isFetching`/`isError` gratis por request — exactamente lo que pide el usuario para animaciones de carga — y invalidación de caché declarativa tras cada mutación, sin repetir lógica en 6+ pantallas. |
| Animación | CSS puro (`@keyframes`, transiciones Tailwind) | Framer Motion / GSAP | Coherente con la filosofía "sin librería" ya fijada en ADR-0014; las animaciones pedidas son sutiles (skeleton, spinner de botón, pulso de éxito), no coreografía compleja — no justifica una dependencia nueva. |
| Diálogos/confirmaciones | Radix UI primitives (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`) | Modal propio a mano | Focus trap, `Escape`, ARIA ya resueltos — evitar implementar accesibilidad de teclado a mano en el diálogo de cancelación (acción destructiva) y el de notas. |
| Detección de rol tras login | Sondeo a `GET /api/asesorias/registros/` (200→asesor, 403→no) | Endpoint dedicado de perfil | El endpoint no existe (ver gap #2); sondear un endpoint ya exclusivo de asesor es la única vía sin tocar backend. Documentado como deuda técnica. |
| UI de disponibilidad semanal | Grilla visual (filas=hora, columnas=día, clic en celda) | Lista agrupada por día | Más intuitiva para planear un horario recurrente; mejor terreno para el feedback de acción pedido (pulso al crear, fade-out al eliminar). |
| Rango horario de la grilla | 07:00–21:00 en bloques de 30 min (28 filas) | Rango dinámico/configurable | El modelo `Disponibilidad` no impone límites de hora — este es un recorte de UI, no del backend. Documentado aquí para que quede explícito, no oculto en el código. |
| Estructura de carpetas | Nueva carpeta `features/asesorias/` (api/lógica/pantallas/componentes) junto al `screens/` plano existente | Seguir metiendo todo en `screens/` | El dominio de asesorías tiene 3 pantallas + hooks + componentes propios; `screens/` plano no escala para eso. `screens/` existente no se toca salvo `Login.tsx`. |

---

## Sistema de motion

No hay match en la base de datos del skill `ui-ux-pro-max` para "calendar/scheduling grid" — el patrón de grilla semanal se diseña con heurística UX general, no con un match de la base de datos. Sí hubo matches para timing de motion, que se traducen a CSS puro (se descartó GSAP, ver tabla de decisiones):

| Uso | Preset de referencia (GSAP) | Traducción a CSS |
|---|---|---|
| Skeleton de carga | shimmer, 1.4s `sine.inOut`, loop | `@keyframes shimmer` + `background-position`, 1.4s `ease-in-out infinite` |
| Entrada de items en lista | stagger subtle, 250-350ms `power1.out`, y=8px | `@keyframes entrada-lista`, 300ms `ease-out`, `translateY(8px)`, delay por item vía `style` |
| Botón en progreso | loader loop 800-1200ms | `.spinner`: borde girando, 600ms `linear infinite` (más rápido que un loader decorativo porque indica una acción puntual, no una espera larga) |
| Confirmación de éxito | success feedback | `@keyframes pulso-exito`: `scale(1→1.03→1)`, 400ms `ease-out`, una sola vez |
| Salida de items (cancelar/eliminar) | exit-faster-than-enter | reutiliza `entrada-lista` en reversa vía `animation-direction: reverse`, 200ms (más corto que la entrada) |

Regla aplicada: mostrar skeleton/spinner solo para operaciones que puedan superar ~300ms, nunca para clics instantáneos — evita el "flash" que el skill marca como anti-patrón.

---

## Pantallas y flujos

### Pantalla 1: Disponibilidad Semanal

**Ruta:** `/asesorias/disponibilidad`

**Flujo:**

1. Al montar, `useMisRegistros()`. Si no hay un registro para `semestreActual()`, mostrar una tarjeta "Registrar disponibilidad para el semestre {X}" con el semestre pre-llenado y editable (input de texto, patrón `AAAAN`) — no hay endpoint de calendario académico así que el semestre por defecto es una heurística de cliente que el asesor puede corregir antes de confirmar.
2. Con el registro creado: sección "Materias" (chips con el nombre resuelto vía `useMapaMaterias`, botón "+ agregar materia" que abre diálogo — lista filtrable de materias con `habilitada_asesorias=true`, error inline si el backend rechaza por "no se imparte este semestre").
3. Grilla semanal: 7 columnas (Lunes–Domingo) × 28 filas (07:00–20:30 en bloques de 30 min). Celda vacía → clic abre diálogo con día/hora ya fijados, pide `formato` + `ubicación`/`liga_virtual` según formato. Celda activa → clic abre un menú con "Desactivar" (PATCH `activa:false`) / "Eliminar" (DELETE).
4. Mientras `useMisDisponibilidades()` está `isPending`, la grilla completa se renderiza con `Skeleton` en vez de celdas.
5. Al crear un bloque, la celda nueva monta con `.entrada-lista` + `.pulso-exito`; al eliminar, la celda sale con `.salida-lista` antes de que TanStack Query refresque la lista (200ms, más corto que la entrada).

### Pantalla 2: Sesiones Asesor (Lista)

**Ruta:** `/asesorias`

**Flujo:**

1. Dos tabs: "Próximas" (filtra `estado === 'agendada'`, ordenado por fecha ascendente) y "Historial" (filtra `estado !== 'agendada'`, descendente).
2. Lista de tarjetas con:
   - Nombre de materia (resuelto vía `useMapaMaterias`)
   - Fecha formateada + hora + placeholder de alumno (`"Alumno #<id>"`)
   - Insignia de estado (`InsigniaEstado`)
3. Cada tarjeta entra con `.entrada-lista` + delay escalonado (max 10 items, 30ms cada uno).
4. Mientras carga: skeleton de 4 placeholders.
5. Si la lista está vacía: mensaje "No tienes asesorías próximas." / "Aún no hay historial."

**Acceso:** Botón "+ Disponibilidad" en la esquina superior derecha navega a `/asesorias/disponibilidad`.

### Pantalla 3: Detalle Asesoría

**Ruta:** `/asesorias/:id`

**Flujo:**

**Sección de información (solo lectura):**
- Materia + insignia de estado
- Lista de datos: alumno (placeholder por id), carrera, fecha, hora, formato (virtual → link; presencial → ubicación)

**Historial de notas:**
- Panel de notas de sesiones previas del mismo alumno, filtradas a realizadas con notas (función `sesionesPreviasConNotas`).
- Cada nota lista la fecha + el texto de la nota.

**Sección de acciones (varía por estado):**

- **Si `estado === 'agendada'`:**
  - Botón "Cancelar asesoría" → abre diálogo (motivo opcional) → `useCancelarAsesoria`.
  - Si `sesionYaOcurrio(asesoria, ahora)`: sección "Marcar asistencia" con dos botones "Asistió" / "No asistió" → `useMarcarAsistencia`. El backend rechaza marcar asistencia antes de la hora de inicio, por eso el gating también ocurre en el cliente.
  - Si no ha ocurrido: nota informativa con la hora en la que se habilita.

- **Si `estado === 'realizada'`:**
  - Insignia de asistencia (`Asistió` / `No asistió`).
  - Si `puedeGuardarNotas(asesoria)` (realizadas + hubo asistencia): textarea editable con las notas actuales, botón "Guardar notas" (deshabilitado si el texto no cambió) → `useGuardarNotas`.
  - Si no: leyenda "El alumno no asistió a esta sesión."

- **Si `estado === 'cancelada'`:**
  - Panel de solo lectura indicando que fue cancelada. (Nota: el motivo de cancelación no está disponible en la API — ver deuda técnica 0010.)
