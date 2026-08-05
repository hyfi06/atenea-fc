## Revisión retroactiva de vistas — Asesorías (asesor)

**Status:** Approved
**Date:** 2026-08-04 (iterada 2026-08-05)

### Context

Las pantallas del flujo de asesorías (vista de asesor) se construyeron en `dev-ux-ui` sin visualización ni aprobación previa — la falla de proceso que originó el plan de rediseño de `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md` (paso 3). Esta spec es esa visualización, hecha ahora, antes de decidir nada sobre reset de `dev-frontend` (paso 5).

Método: en vez de mockups aislados, se levantó la app real (`dev-ux-ui`, backend Django + frontend Vite contra Postgres/Redis locales), se sembró un asesor de demo con datos en los tres estados relevantes (agendada, realizada con notas, inasistencia, cancelada), y se navegó cada pantalla/diálogo con Playwright — capturas reales, no reconstrucciones. Sobre esa base se iteró el diseño de los ajustes encontrados, usando `ui-ux-pro-max` para fundamentar las decisiones de los puntos 3-5 (convención de diálogos, arquitectura de información, patrón de acción restringida por tiempo).

Esta spec es autocontenida: no depende de los artefactos visuales (`Artifact`) generados durante la sesión de diseño para ser implementable — cada decisión de código está descrita en prosa/tablas abajo.

### Decisión por pantalla

| Pantalla | Veredicto | Cambia respecto a lo ya construido |
|---|---|---|
| Sesiones del asesor (Próximas/Historial) | Aprobada con ajustes | Botón "← Home", subtabs de semestre en Historial |
| Detalle de asesoría | Aprobada con ajustes | Cancelar pasa a outline; formato con ícono; notas confirmadas inline |
| Disponibilidad del asesor | Aprobada con ajustes — **rediseño de fondo** | Se separa en dos pantallas: "Mis materias" y "Mi horario" (grilla → tabs por día) |
| Diálogos (bloque activo, nuevo bloque, agregar materia) | Aprobada | Se codifica una convención de botones nueva (ver más abajo), aplica retroactivamente a estos también |
| Componentes compartidos (Boton, InsigniaEstado, Retroalimentacion, Skeleton) | Aprobada | Sin cambios |
| Home (fuera del flujo de asesorías, pero afectada) | Nueva — tarjeta condicional | Primera tarjeta condicional a rol en `services.ts` |

---

### 1. Ícono de Asesorías Académicas

Nuevo ícono para `ServiceIcons.tsx`, mismo lenguaje visual del set existente (`viewBox="0 0 48 48"`, `stroke="currentColor"`, `strokeWidth={2.5}`, cierres redondeados):

```tsx
export function IconAsesoriasAcademicas({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <circle cx="10" cy="12" r="4.5" />
      <path d="M4 34 C4 25 7 21 11 21 C13 21 14.5 21.6 16 23" />
      <line x1="16" y1="23" x2="27" y2="15" />
      <rect x="23" y="8" width="21" height="16" rx="2" />
      <line x1="33" y1="24" x2="33" y2="30" />
      <line x1="27" y1="30" x2="39" y2="30" />
      <line x1="27" y1="14" x2="40" y2="14" />
      <line x1="27" y1="19" x2="35" y2="19" />
    </IconBase>
  )
}
```

Lee como "profesor con puntero (batuta) señalando un pizarrón con patas y contenido" — combina dos de las tres referencias dadas (batuta, pizarrón). Se descartó la referencia de "acompañamiento" como composición aparte porque `IconTutorias` ya usa exactamente esa idea (dos personas) para el servicio de Tutorías; repetirla habría confundido ambos íconos en la grilla de Home. Las dos líneas horizontales del pizarrón reusan la misma convención de "texto" que ya usa `IconIdiomas`.

### 2. Home — tarjeta condicional a rol

- La tarjeta "Asesorías Académicas" se agrega a `services.ts`/`Home.tsx` **condicionada a que el usuario tenga `PerfilAsesorAcademico` o `PerfilAlumno`** (no ambos).
- **Sin resaltado visual**: usa el mismo rol de color rotativo que cualquier otra tarjeta del grid (ej. `tertiary-container`), sin borde ni sombra especial — no debe sugerir un significado ("nuevo", "urgente") que podría confundirse con otro estado más adelante.
- **Sin perfil → la tarjeta no se renderiza** (se filtra del arreglo antes de mapear, como cualquier otro item condicional); la grilla de 3 columnas reacomoda el resto — no queda una celda vacía ni un placeholder en blanco.
- **Decisión sobre deuda técnica 0010:** mostrar esta tarjeta exige saber el rol del usuario. Hoy `useEsAsesor()` (`frontend/src/auth/rol.ts`) ya resuelve esto con un sondeo (`GET /api/asesorias/registros/`, 200 vs 403) — exactamente el patrón que la propia [deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md) advierte que "no escala a más de un rol sin agregar una llamada de sondeo por cada rol". Condicionar a "asesor o alumno" exigiría un segundo sondeo gemelo (`useEsAlumno()`). **Se decide no construir ese segundo parche: la deuda técnica 0010 se resuelve como parte del paso 4** (plan de backend), exponiendo perfil/rol en una sola llamada (`/api/auth/user/` o el endpoint que ese plan defina). Home espera a esa resolución en vez de duplicar el workaround.

---

### 3. Disponibilidad del asesor → "Mis materias" + "Mi horario"

**Cambio de fondo:** en vez de una sola pantalla con grilla de 7×28 celdas (el diseño original revisado, que mostraba solo ~3 de 7 columnas en un viewport de 390px sin ninguna pista de scroll — hallazgo de la primera pasada de esta revisión), se separa en dos pantallas:

- Materias se gestiona una vez por semestre (1-5 ítems); horario se consulta/edita constantemente. Cada pantalla responde una sola pregunta ("¿qué imparto?" vs. "¿cuándo estoy libre?") sin competir por espacio ni necesitar un separador entre secciones.

#### Mis materias

- Lista de filas (no chips) — cada fila: nombre de la materia truncado a **una línea con ellipsis** + atributo `title` con el nombre completo (para hover en desktop; en móvil el nombre completo debe quedar accesible al tocar la fila, p. ej. abriendo el detalle o expandiendo) + botón de quitar (ícono de basura, **36-44px de área de toque**, no un "×" diminuto sobre un chip — un chip con "×" no alcanza el tamaño mínimo de toque de 44×44px).
- "+ Agregar" (arriba, abre el `DialogoAgregarMateria` ya existente, sin cambios).
- Quitar una materia abre un diálogo de confirmación de 2 acciones (ver convención de diálogos abajo): "Ya no aparecerás como asesor de esta materia en búsquedas de alumnos. Las asesorías ya agendadas no se cancelan."

#### Mi horario

- **Tabs por día** (Lun–Dom) en vez de la grilla de 7 columnas — cada tab muestra una lista vertical de los slots de 30 min de ese día (07:00–20:30), sin scroll horizontal ni columnas cortadas. Mismo patrón de pestañas que ya usa `SesionesAsesor` (Próximas/Historial).
- **Línea de instrucción**, fija arriba de los tabs: *"Cada celda es un horario disponible: toca para activarlo o editarlo. Para cambiar de día, usa las pestañas. Los cambios se autoguardan."*
- **Leyenda de color y formato**, debajo de la instrucción: chip "Activo" (rol `primary-container`), chip "Inactivo" (rol `surface-variant`), ícono de monitor + "Virtual", ícono de pin + "Presencial" (mismos SVG que en Detalle, ver punto 5 — es el mismo concepto, debe ser el mismo ícono).
- **Grilla/lista limpia**: cada fila de slot activo muestra hora + el ícono de formato (monitor o pin) **sin el texto "Virtual"/"Presencial" repetido** (la leyenda ya lo explica una vez) + el salón si es presencial, **sin prefijo ("Presencial —") ni guion** — solo el nombre del salón directo después del ícono. Si es virtual, solo el ícono (no hay "salón" que mostrar ahí).

#### Desactivar un horario con sesiones futuras

Al tocar un bloque activo y elegir desactivar, si el backend confirma que existen `Asesoria` agendadas a futuro en ese horario, se muestra un modal de 3 acciones (ver convención abajo):
1. "Solo dejar de recibir nuevas" (reversible, arriba)
2. "Cancelar esas sesiones y desactivar" (destructiva, outline, en medio)
3. "Volver" (texto plano, sin fondo, al final)

### Convención de diálogos (nueva — aplica a toda la app, no solo a Disponibilidad)

Esta sección corrige una inconsistencia real encontrada entre `DialogoCancelar`/`DialogoAgregarMateria` (2 acciones) y los diálogos nuevos de este rediseño (3 acciones) — y un bug real de layout detectado en el propio proceso de diseño.

- **2 acciones → fila horizontal.** Izquierda = acción segura/salir (Cancelar, Volver); derecha = acción de confirmación (mantiene su estilo semántico — `peligro`/relleno si es destructiva, `primario` si no). Es lo que `DialogoCancelar` y `DialogoAgregarMateria` ya hacen bien; queda codificado como regla explícita para que los diálogos nuevos (quitar materia, etc.) no la rompan.
- **3+ acciones → columna, ancho completo, orden fijo:** arriba la opción reversible/segura, en medio la consecuente (siempre **outline, nunca relleno** — no debe verse como "la fácil"/la más prominente), y "Volver"/"Cancelar" al final como texto plano sin fondo. La opción más destructiva nunca va arriba ni con el estilo visualmente más fuerte.
- **Fix de overflow:** cualquier botón con `flex: 1` dentro de un diálogo necesita `min-width: 0` (y `white-space: normal` para permitir 2 líneas) — sin esto, un botón no se encoge por debajo del ancho de su propio texto y el par de botones se desborda cuando el contenido del modal es largo (bug real reproducido durante el diseño: el modal de "quitar materia" con un nombre de materia largo desbordaba sin `min-width:0`).

### Truncamiento de nombres de materia

Probado contra los dos extremos reales del catálogo: *"Aplicación de las Ciencias de la Tierra en la Vigilancia de Ensayos Nucleares"* (74 caracteres) y *"Física"* (6 caracteres).

- **Chips/filas de lista** (contenedor de ancho fijo): 1 línea, `text-overflow: ellipsis`, `overflow: hidden`, `white-space: nowrap`, con el nombre completo en `title`.
- **Encabezados** (título de tarjeta/pantalla de detalle): **nunca truncar a 1 línea** — `-webkit-line-clamp: 2` (2 líneas), porque es el nombre de la materia, la información principal de la pantalla, no una etiqueta secundaria. El badge de estado que lo acompaña debe llevar `flex: none` para no comprimirse cuando el título ocupa 2 líneas.

### Backend nuevo requerido para "Mis materias"/"Mi horario" (pendiente para el paso 4)

| Endpoint propuesto | Para qué |
|---|---|
| `GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/` | Antes de mostrar el modal de advertencia al desactivar: cuenta + lista mínima de `Asesoria` agendadas a futuro sobre esa `Disponibilidad`. |
| Acción de "cancelar todas y desactivar" en el backend (transacción) | Cancela cada `Asesoria` futura (reusa `Asesoria.cancelar()` ya existente) + pone `activa=False`, en una sola llamada — no un loop de N requests desde el frontend. |
| `POST /api/asesorias/registros/{id}/materias/quitar/ {materia_id}` (o `DELETE .../materias/{materia_id}/`) + `RegistroAsesor.quitar_materia()` | Botón de quitar materia en "Mis materias" — hoy `RegistroAsesorSerializer.materias` es `read_only` y solo existe el `agregar_materia()` simétrico. |

Ninguno de estos tres existe hoy en `backend/asesorias/`. No se implementan en este paso — quedan como requisito de entrada del plan de backend del paso 4.

---

### 4. Sesiones del asesor (Próximas/Historial)

- **"← Home"** en el encabezado, simétrico al patrón "← Volver a Asesorías" que ya usa el detalle — hoy esta pantalla es un callejón sin salida salvo el botón atrás del navegador.
- El link de texto "Disponibilidad" se reemplaza por **dos botones** ("Mis materias" / "Mi horario"), consecuencia directa de la separación del punto 3.
- **Historial con subtabs de semestre** (ej. 2026-2 / 2026-1 / 2025-2…) en vez de cargar todo el historial de una vez. **Requiere un query param nuevo en el backend:** `GET /api/asesorias/asesorias/?semestre=20262`, filtrando por `disponibilidad__registro__semestre`; el tab por default carga el semestre en curso. Esto conecta con la [deuda técnica 0006](../../technical-debt/0006-sin-paginacion-listados.md) (sin paginación) — el filtro cubre el caso de uso más común (ver historial reciente), no la reemplaza; vale la pena anotarlo en la propia 0006 cuando se implemente. También pendiente para el paso 4.

---

### 5. Detalle de asesoría

- **Restricción de horario para marcar asistencia: oculto + mensaje, no deshabilitado.** Esto **confirma** el comportamiento ya escrito en `DetalleAsesoria.tsx`/`sesionYaOcurrio()` — no se cambia. Razón (vía `ui-ux-pro-max`): la semántica de "disabled" de Material (opacidad reducida + cursor) está pensada para condiciones que el usuario puede resolver ahora mismo (un formulario incompleto); aquí no hay nada que resolver, solo esperar, y sin hover en móvil un botón deshabilitado necesitaría el mismo texto explicativo de todos modos — ocultar + explicar evita controles "fantasma" que invitan a tocarlos en vano. El mensaje debe incluir la hora exacta ("Podrás registrar asistencia después de las 16:30"), no un genérico "espera un momento".
- **Notas de la sesión: inline, no modal.** También confirma el comportamiento ya escrito — justo debajo de "El alumno asistió.", en el mismo panel donde ya vive "Notas de sesiones anteriores con este alumno". Un modal sería una interrupción extra justo después de confirmar asistencia sin necesidad.
- **"Cancelar asesoría" pasa de relleno a outline** (mismo `variante="peligro"` de `Boton`, sin fill — borde y texto en tono de error, fondo transparente). Sigue leyéndose como destructiva por color, pero ya no compite visualmente con marcar asistencia, que es la acción más frecuente del asesor en esta pantalla. **Cambio de código:** variante nueva del componente compartido `Boton` (ej. `peligro-outline`) o clase puntual en `DetalleAsesoria.tsx` — se decide en el plan de implementación.
- **Formato con ícono al frente:** la fila `<dt>Formato</dt><dd>` deja de mostrar "Liga de la sesión" como texto plano; pasa a ícono de monitor + enlace **"Entrar"** (virtual) o ícono de pin + el nombre del salón (presencial) — mismos dos SVG que la leyenda de "Mi horario" (punto 3): es el mismo concepto en ambas pantallas, debe ser el mismo ícono.
- **Encabezado con nombre de materia largo:** `line-clamp: 2` (ver "Truncamiento" en el punto 3) — probado con el ejemplo de 74 caracteres sin romper el layout ni la posición del badge de estado.

Íconos de referencia (mismos en punto 3 y punto 5):

```tsx
// Pin (presencial)
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
  <circle cx="12" cy="10" r="3" />
  <path d="M12 21c-4-4.5-7-8-7-11a7 7 0 0 1 14 0c0 3-3 6.5-7 11Z" />
</svg>

// Monitor (virtual)
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
  <rect x="3" y="4" width="18" height="12" rx="2" />
  <path d="M8 20h8" />
  <path d="M12 16v4" />
</svg>
```

---

### Out of scope

- Resolver la deuda técnica 0010 en sí (se decide *que* se resuelve en el paso 4, no se resuelve aquí).
- Implementar los tres endpoints de backend nuevos listados arriba (paso 4).
- El filtro por semestre del historial (paso 4, backend) y el consumo de ese filtro en el frontend (paso 9).
- Formalizar la convención de diálogos como documento aparte en `docs/development/` (candidato natural para el paso 7, marco de trabajo de componentes) — aquí queda documentada y aplicada, no todavía como guía independiente.
- Migrar `DialogoCancelar`/`DialogoAgregarMateria`/dialogs existentes al patrón `min-width:0` — se hace junto con el resto de la implementación en el paso 9, no es parte de esta spec.

### Self-review

- Sin placeholders/TBD: cada decisión (íconos, copy exacto de la instrucción, orden de botones, truncamiento) tiene un valor concreto, confirmado explícitamente por el usuario en el proceso de revisión.
- Sin contradicciones: el veredicto de Disponibilidad ("Aprobada con ajustes") se actualizó a reflejar el rediseño de fondo (split de pantallas) en vez de dejar el veredicto original de la primera pasada sin actualizar.
- Alcance cohesivo: cubre solo las pantallas ya construidas del flujo de asesorías (asesor) + la tarjeta nueva de Home que las expone — no se mezcla con la vista de alumno (Fase 2, fuera de alcance) ni con el sistema de componentes general (paso 6).
- Deuda técnica: no se genera deuda nueva. La 0010 y la 0006 ya existían; esta spec decide explícitamente cuándo se resuelven (0010: paso 4) o qué las cubre parcialmente (0006: el filtro de semestre), no las ignora en silencio.
- Autocontenida: cada decisión visual está descrita en prosa/código, no depende de que el artefacto HTML de la sesión de diseño siga disponible para una implementación futura en otra sesión.
