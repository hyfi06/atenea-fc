# Guía de usuario — Académico — 2026-08-25

## Contexto

Atenea no tiene ninguna guía de usuario todavía. Se decidió crear una,
empezando por el flujo del académico (el rol con más pasos: convertirse en
asesor, mantener materias y horario, y atender asesorías), con ejemplos
visuales en formato de celular para que un académico sin experiencia previa
en la app pueda seguirla sin ayuda.

La guía debe ser **pública** (accesible sin sesión, para poder compartirse
por link antes de que alguien tenga cuenta) y **servida por la propia app
web**, no ser solo un documento del repo. Debe además ser barata de mantener
para subagentes que la vayan a leer/escribir a futuro: archivos pequeños y
autocontenidos, sin dependencias cruzadas que obliguen a abrir más de un
archivo para editar una sección.

Mapa del flujo de académico, confirmado leyendo el código (`frontend/src`):

1. **Convertirse en asesor** — Home (tile "Asesorías", visible a
   `esAlumno || esAcademico`) → pantalla Asesorías (banner
   "Registrarme como asesor" para académico sin perfil de asesor) →
   formulario de solicitud (elegir área → "Solicitud enviada") → mientras
   la SAE confirma el nombramiento, banner de pendiente en Asesorías o
   pantalla `AsesorPendiente` al intentar Mis materias/Mi horario → una vez
   activo, si no hay registro del semestre, pantalla `SinRegistroAsesor`
   ("Registrar semestre {semestre}", solo si la ventana de registro está
   abierta).
2. **Mis materias** — lista de materias del semestre, botón "+ Agregar"
   (`DialogoAgregarMateria`), quitar con confirmación
   (`DialogoQuitarMateria`).
3. **Mi horario** — rejilla semanal por pestañas (Lun–Sáb), tocar una celda
   vacía crea un bloque (`DialogoNuevoBloque`: virtual o presencial), tocar
   un bloque activo lo desactiva/elimina (`DialogoBloqueActivo`), con aviso
   si tiene sesiones futuras agendadas (`DialogoDesactivarConSesiones`).
4. **Atender asesorías** — pantalla Asesorías con tabs Próximas/Historial
   (`TarjetaAsesoria`) → detalle de una asesoría
   (`DetalleAsesoria`/`SeccionAcciones`): marcar asistencia (Asistió/No
   asistió, habilitado tras la hora de la sesión), agregar/editar notas de
   sesión una vez realizada, cancelar con motivo (`DialogoCancelar`).

## Decisión

### Dónde vive y cómo se sirve

La guía se sirve como archivos estáticos desde `frontend/public/docs/`.
Vite copia `public/` sin procesar a `dist/`, y `frontend/nginx.conf` ya
resuelve archivos reales antes del fallback de la SPA
(`try_files $uri $uri/ /index.html;`), así que no se necesita build step,
proxy nuevo ni cambio de CSP (la CSP actual ya permite `style-src
'unsafe-inline'`; la guía no usa JS ni recursos externos, así que no toca
`script-src`). Queda en `/docs/` y `/docs/academico/...` tanto en prod como
en `pnpm dev`.

```
frontend/public/docs/
  index.html                    # portal: hoy una sola tarjeta → Académico
  academico/
    index.html                  # portada de la guía, con link a cada sección
    01-registro-asesor.html
    02-mis-materias.html
    03-mi-horario.html
    04-tus-asesorias.html
```

`index.html` (el portal, no el de `academico/`) es el destino estable desde
la app — cuando se agregue la guía de otro rol, se agrega su tarjeta ahí sin
tocar el link que vive en `Home.tsx`.

### Sistema visual

- Cada archivo `.html` es autocontenido: su propio `<style>` inline, sin
  hoja de estilos ni script externos, sin build. Se acepta duplicar el
  marco del teléfono y los tokens de color entre archivos — el objetivo es
  que abrir un solo archivo baste para entenderlo y editarlo completo.
- Marco de iPhone en CSS puro: ~390×844px (iPhone 14/15 lógico), esquinas
  redondeadas, dynamic island, barra de estado mínima (hora + iconos
  genéricos). Cada pantalla mockeada va dentro de un marco.
- Paleta: los mismos tokens M3 oscuros de `frontend/src/index.css`
  (`--color-primary`, `--color-primary-container`, `--color-secondary*`,
  `--color-tertiary*`, `--color-error*`, `--color-background`,
  `--color-surface*`, `--color-outline*`) copiados como variables CSS en
  cada archivo — la app no tiene tema claro, así que no hace falta
  soportar ambos.
- Tipografía: pila de sistema (`-apple-system, BlinkMacSystemFont,
  "Segoe UI", Roboto, sans-serif`) para que se vea nativo de iPhone.
- El logo de Atenea se reproduce con el mismo SVG de
  `frontend/src/components/Logo.tsx` (inline, `stroke="currentColor"`).
- **Sin URLs reales**: como la guía es pública, ningún mockup ni texto
  muestra rutas reales de la SPA (`/asesorias/materias`, `/asesorias/soy-asesor`,
  etc.). Las pantallas se identifican solo por su nombre visible en la UI
  ("Mis materias", "Mi horario"), nunca por su ruta.
- Cada "paso" dentro de una sección = un marco de teléfono con la pantalla
  reproducida + una nota al lado o debajo con el número de paso y qué
  tocar. Una sección puede tener varios pasos en secuencia (p. ej. la
  sección 1 encadena Home → Asesorías → formulario → confirmación →
  pendiente → registrar semestre).

### Header y navegación de la guía

Cada página de la guía (portal, portada de académico, y las 4 secciones)
lleva, como chrome propio de la página — no dentro de los mockups de
teléfono —, un header con el logo + "Atenea" (mismo lenguaje visual que el
header real de `Home.tsx`), envuelto en un único `<a href="/">`. No hay
ícono de hamburguesa aparte: `Landing.tsx` ya hace
`<Navigate to="/home" replace />` cuando `status === 'authenticated'`, así
que un solo link a `/` resuelve los dos casos (visitante sin sesión ve la
landing; usuario logeado rebota a su Home) sin necesitar JavaScript para
detectar sesión.

Además, cada página lleva navegación propia de la guía (independiente del
header de la app): las 4 secciones tienen un "← Volver" a
`academico/index.html`, y `academico/index.html` tiene un "← Volver" a
`/docs/`.

### Tarjeta en Home

`frontend/src/screens/Home.tsx` gana un tile más en el arreglo `tiles`:
"Guía de uso", visible para **todos** los roles (sin condición de rol —
la guía es pública y hoy es la única, a diferencia de los demás tiles que
sí filtran por rol porque son servicios reales). Usa
`containerClassName: 'bg-tertiary-container text-on-tertiary-container'`
para distinguirse visualmente de los tiles de servicio. A diferencia de
los demás tiles (que navegan con `useNavigate()` porque son rutas de
React Router), este es un `<a href="/docs/">` de navegación completa de
página, porque `/docs/` es un árbol estático fuera del router de la SPA —
usar `navigate()` lo mandaría a `NoEncontrado`. Esto requiere distinguir en
el render qué tiles son internos (`<button onClick={...}>`) y cuáles son
externos (`<a href={...}>`); se agrega un campo `externo?: boolean` a la
config de cada tile.

### Documento de mantenimiento

`docs/development/guia-de-usuario.md` (junto a `api-frontend.md` y
`contribuir-componentes.md`) documenta, para quien mantenga la guía a
futuro (humano o subagente):

- El snippet base del marco de iPhone, listo para copiar/pegar.
- La tabla de tokens de color M3 oscuros y su origen (`frontend/src/index.css`),
  con la nota de que si la paleta de la app cambia, hay que sincronizar
  aquí a mano.
- El mapa de archivos actual y la convención de nombres
  (`NN-nombre-seccion.html`).
- Cómo agregar un paso/pantalla nueva a una sección existente.
- Cómo agregar una sección nueva o un rol nuevo (nuevo directorio bajo
  `frontend/public/docs/`, más su tarjeta en `frontend/public/docs/index.html`).
- El recordatorio de no usar rutas reales de la SPA en ningún texto ni
  mockup.

## Consecuencias

- La guía queda pública sin autenticación — cualquiera con el link la ve.
  Aceptado explícitamente: es contenido de ayuda, no información sensible,
  y permite compartirla antes de que alguien tenga cuenta.
- Los mockups son ilustraciones hechas a mano, no capturas reales — pueden
  desincronizarse visualmente de la app si esta cambia y nadie actualiza la
  guía. Mitigado por `docs/development/guia-de-usuario.md`, que deja el
  proceso de actualización documentado y barato.
- Duplicar el marco de teléfono y la paleta en cada archivo es deuda
  intencional a favor de que cada archivo se entienda solo — no amerita
  ítem de deuda técnica porque es la decisión de diseño en sí, no un atajo
  sobre ella.

## Alternativas consideradas

- **Screenshots reales vía Playwright** en vez de mockups a mano: más
  fieles, pero exigen stack corriendo, usuario de prueba sembrado con rol
  de asesor, y volver a correr el script de captura cada vez que la UI
  cambie. Se descartó por ahora a favor de mockups sin dependencias de
  infraestructura; podría revisitarse más adelante.
- **`docs/user-guides/` en el repo, sin servir por la app**: era la
  ubicación inicial propuesta, pero no resuelve el requisito real de que la
  guía sea accesible para usuarios finales, no solo para quien lee el
  repo.
- **CSS/JS compartido entre archivos de la guía** (una sola hoja de estilos
  importada por todas las secciones): reduce duplicación, pero acopla los
  archivos entre sí — un subagente editando una sección tendría que leer
  también el archivo compartido para no romper a las demás. Descartado a
  favor de archivos autocontenidos, priorizando el costo de mantenimiento
  sobre el de líneas duplicadas.
- **Detectar sesión con un script inline** para mostrar/ocultar el ícono de
  "volver a la app" según haya sesión real: rompe el diseño "sin JS" y
  acopla la guía al mecanismo de auth interno de la SPA. Descartado a favor
  de un solo link a `/`, que ya resuelve ambos casos vía el redirect
  existente en `Landing.tsx`.
