# Fixes — 2026-08-24

## Contexto

Cinco correcciones puntuales reportadas sobre el frontend (una con parte de
backend): un bug de sesión
(logout termina en `/login` en vez de en la landing), una feature de
agendado (el alumno ve días/bloques ya fuera de la ventana de 2h), un bug de
estilo (botón "+ Agregar" de Mis materias no combina con sus vecinos), un
chore de calendario (domingo no debe listarse en Mi horario) y un bug de
compatibilidad de navegador (`<select>` casi ilegible en Chrome/Opera/Edge +
Linux Mint). Los cinco son correcciones dentro de decisiones ya vigentes —
ninguno amerita ADR ni deuda técnica nueva.

Todas las rutas de archivo son relativas a `backend/` o `frontend/` según se
indique.

---

## 1 — Logout termina en `/login` en vez de en la landing

**Causa raíz (confirmada con Network tab en dev, ver hilo de spec):**
`MenuUsuario.cerrarSesion()` (`frontend/src/components/MenuUsuario.tsx:65-72`)
hace:

```tsx
async function cerrarSesion() {
  setCerrando(true)
  await logout()                       // adentro: setStatus('unauthenticated')
  navigate('/', { replace: true })
}
```

`logout()` (`frontend/src/auth/AuthContext.tsx:68-83`) llama
`setStatus('unauthenticated')` antes de que `cerrarSesion` alcance a llamar
`navigate('/')`. Ambas actualizaciones — el estado local de `AuthContext` y
el estado interno del router — nacen de fuentes distintas dentro de la misma
continuación de microtask (tras el `await` a `apiPost`). El clic ocurre
estando montado en `/home`. Antes de que la navegación explícita a `/` surta
efecto, `RutaConSesion` (que sigue montado en `/home` en ese instante) ve
`status === 'unauthenticated'` y se adelanta, redirigiendo por su cuenta a
`/login` — la guarda de la ruta decide el destino final, no el
`navigate('/')` de `cerrarSesion`.

Confirmado con una captura real (Chrome, dev): una sola petición de red (sin
reload ni refetch de `/api/auth/user/`), aterrizaje instantáneo en `/login`
sin frame intermedio visible, reproducible siempre igual con un solo clic —
no es timing flaky, es un orden de commits determinista dado cómo React
18/19 procesa estas dos fuentes de actualización. `POST /api/auth/logout/`
responde `200 OK` limpio: el backend no está involucrado.

**Fix:** en vez de perseguir el orden exacto de esa carrera entre updates
(frágil), se lo vuelve inofensivo — las dos rutas de destino convergen.
`frontend/src/auth/RutaProtegida.tsx` — las 5 guardas (`RutaConSesion`,
`RutaDeAsesor`, `RutaDeAsesorias`, `RutaDeSAE`, `RutaDeAcademico`) redirigen
hoy a `/login` con `state={{from: location}}` cuando no hay sesión. Se
confirmó por grep repo-wide que **`location.state.from` nunca se lee en
ningún lado** — ninguna pantalla lo consume para volver a la página
original tras iniciar sesión, es dato muerto. Cambio: las 5 redirigen a `/`
en vez de `/login`, y se deja de pasar el `state` muerto:

```tsx
export function RutaConSesion({ children }: { children: ReactNode }) {
  const { status } = useAuth()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
```

(mismo cambio en las otras 4 guardas: quitar `useLocation`/`location` si
queda sin otro uso, y `Navigate to="/"` sin `state`.)

Con esto, sin importar cuál de las dos navegaciones "gane" la carrera,
ambas terminan en `/` — el bug deja de ser observable sin depender de
resolver el scheduling exacto. Es consistente con el principio ya
documentado en `2026-08-13-fixes-navegacion-sesion-frontend-design.md`
("la landing es la entrada canónica de la app").

**Testing:** `frontend/src/auth/RutaProtegida.test.tsx` tiene 4 asserts que
esperan `/login` como destino de las guardas sin sesión (líneas 34, 99, 159,
204 y sus casos asociados) — se actualizan a `/`. Revisar
`MenuUsuario.test.tsx` por si algún caso asume `/login` como consecuencia
indirecta del logout.

### Botón de regreso en Login (`frontend/src/screens/Login.tsx:55-64`)

Se quita el botón circular con ícono SVG (`onClick={() => navigate(-1)}`) —
depende del historial del navegador, lo cual es justo la fuente del segundo
síntoma reportado ("el botón de atrás de login sigue recorriendo el
historial"). Se reemplaza por el mismo patrón textual fijo que ya usan las
pantallas de Asesorías (`frontend/src/features/asesorias/screens/Asesorias.tsx:46-48`):

```tsx
<button
  type="button"
  onClick={() => navigate('/')}
  className="foco-visible w-fit min-h-11 text-sm text-primary"
>
  ← Inicio
</button>
```

Destino fijo `/` (landing), no `-1`: no depende de cómo se llegó a `/login`
(deep link, recarga directa, o efectivamente "atrás").

**Testing:** `frontend/src/screens/Login.test.tsx` — actualizar el caso que
verifica el botón de regreso (`aria-label="Volver"` deja de existir; nuevo
caso: click en "← Inicio" navega a `/`).

---

## 2 — El alumno ve días/bloques ya fuera de la ventana de 2h

**Causa raíz:** `BuscarDisponibilidadView.get()`
(`backend/asesorias/views.py:118-172`) arma los slots agendables recorriendo
cada fecha entre hoy y el fin de la ventana quincenal (`ventana_agendable()`),
pero no descarta las horas de hoy que ya pasaron o están a menos de 2h de
ahora — esa ventana sólo se valida al momento de agendar
(`Asesoria.clean()`, `backend/asesorias/models.py:236-244`), no al listar.
Un alumno hoy puede ver (y sólo al confirmar falla) un bloque de las 9am si
ya son las 11:50am.

**Fix:** aplicar el mismo predicado que ya usa `Asesoria.clean()` (línea
243: `timezone.now() > self.momento_inicio - VENTANA_MINIMA_ANTICIPACION`)
también al listar, para que lo que se ofrece como agendable sea siempre
agendable:

```python
# backend/asesorias/views.py
from .models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor, VENTANA_MINIMA_ANTICIPACION

class BuscarDisponibilidadView(APIView):
    ...
    def get(self, request):
        ...
        inicio, fin = ventana_agendable()
        ahora = timezone.now()
        ocupados = set(...)

        resultados = []
        fecha_cursor = inicio
        while fecha_cursor <= fin:
            dia_semana = fecha_cursor.weekday()
            for disp in disponibilidades:
                if disp.dia_semana != dia_semana:
                    continue
                if (disp.id, fecha_cursor) in ocupados:
                    continue
                momento_inicio = timezone.make_aware(
                    datetime.datetime.combine(fecha_cursor, disp.hora_inicio)
                )
                if ahora > momento_inicio - VENTANA_MINIMA_ANTICIPACION:
                    continue
                resultados.append({...})
            fecha_cursor += datetime.timedelta(days=1)
```

Un solo cambio resuelve "días y bloques": si un día se queda sin slots
elegibles, `agruparPorDia()` en el frontend
(`frontend/src/features/asesorias/logica.ts`) ya lo omite solo, sin tocar
nada del frontend.

**Testing:** `backend/asesorias/tests/` — caso nuevo en el test file de
`BuscarDisponibilidadView`: un bloque de hoy cuya `hora_inicio` cae dentro
de las próximas 2h (o ya pasó) no aparece en la respuesta; un bloque de hoy
más allá de las 2h sí aparece; un bloque de mañana (fuera del día actual)
no se ve afectado por la hora actual. Congelar el reloj con
`freezegun`/`time_machine` si el proyecto ya lo usa en tests similares de
ventana (revisar `asesorias/tests/test_models.py` por el patrón existente
para `VENTANA_MINIMA_ANTICIPACION`).

---

## 3 — Botón "+ Agregar" en Mis materias no combina con sus vecinos

**Causa raíz:** `frontend/src/features/asesorias/screens/MisMaterias.tsx:129-138`
es el único botón de acción de la pantalla sin `border`/`bg` — texto plano
`text-primary`. Los botones vecinos de acción secundaria (`Mis materias`,
`Mi horario` en `Asesorias.tsx:55-68`) usan píldora con borde.

**Fix:**

```tsx
<button
  type="button"
  onClick={() => {
    setErrorAgregar(null)
    setDialogoAgregarAbierto(true)
  }}
  className="foco-visible min-h-11 rounded-full border border-outline px-3 text-sm font-medium text-primary"
>
  + Agregar
</button>
```

Mismo patrón exacto que `Mis materias`/`Mi horario`: `border border-outline`,
`px-3` (no `px-2`), texto `text-primary`. Se conserva el texto `+ Agregar`.

**Testing:** ningún test actual depende de las clases exactas de este botón
(`MisMaterias.test.tsx` lo ubica por texto/rol); no requiere cambios de
test, sólo verificación visual.

---

## 4 — Ocultar domingo en Mi horario

**Diseño:** `frontend/src/features/asesorias/screens/MiHorario.tsx:27-28`:

```ts
const DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
```

Se recortan a 6 entradas (se quita `'Dom'`/`'Domingo'`, índice 6). El único
lugar donde se recorre el arreglo completo es el render de las pestañas
(`DIAS_CORTOS.map` en las líneas 208 y 215) — al tener 6 elementos en vez de
7, domingo deja de tener pestaña **tanto en modo edición del asesor como en
consulta de SAE** (mismo componente, mismo criterio, según se confirmó).
Puramente de frontend: no se toca `dia_semana` en el backend ni la
validación de `Disponibilidad` — si existiera algún bloque legado en
domingo, seguiría existiendo en datos pero no sería visible en esta
pantalla (aceptado explícitamente, no amerita regla de backend).

`celdaVacia.dia` (usado al crear un bloque nuevo, línea 116) sigue siendo un
índice 0-5 válido tras el recorte, ya que `tocarSlot` recibe `indice` del
mismo `DIAS_CORTOS.map` ya acotado — no requiere cambio adicional.

**Testing:** `MiHorario.test.tsx` — actualizar cualquier caso que cuente
pestañas esperando 7, o que interactúe con la pestaña "Dom"; caso nuevo:
domingo no aparece en la lista de pestañas (ni en modo edición ni en modo
`soloLectura`).

---

## 5 — `<select>` casi ilegible en Chrome/Opera/Edge + Linux Mint

**Diagnóstico:** no hay ninguna declaración de `color-scheme` en el CSS del
proyecto, y la app es de tema único (siempre oscuro —
`frontend/src/index.css:24-35` sólo define la paleta oscura, sin
`@media (prefers-color-scheme)` ni variante clara). Es la causa clásica de
este bug conocido de Chromium en Linux: sin `color-scheme` explícito, el
navegador pinta el texto de las `<option>` con la paleta de un modo (según
el tema GTK del SO) mientras el fondo del popup nativo se pinta con la del
otro — de ahí el texto pálido casi invisible sobre fondo claro que se ve en
la captura. Firefox y Safari no tienen ese comportamiento, por eso ahí se ve
bien.

**Fix (best-effort, según acordamos — sin garantía total de paridad entre
navegadores/temas del SO):** declarar `color-scheme: dark` explícito
—no `light dark`, porque la app nunca renderiza en claro, así que decirle al
navegador "esto es oscuro" es lo correcto y además da un popup nativo oscuro
consistente con el resto de la UI, en vez de un flash claro— y fijar
`background-color`/`color` explícitos en `select`/`option` con los tokens
ya existentes, como refuerzo (Chromium sí respeta esas dos propiedades en
`<option>`):

```css
/* frontend/src/index.css, dentro del bloque :root ya existente (línea 71-75) */
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
  color-scheme: dark;
}

select {
  color-scheme: dark;
  background-color: var(--color-surface-container);
  color: var(--color-on-surface);
}

select option {
  background-color: var(--color-surface-container);
  color: var(--color-on-surface);
}
```

No requiere tocar los componentes (`DialogoAgregarMateria.tsx:87-99`,
`AgendarAsesoria.tsx:177-189`): la regla es global sobre el elemento
`select`, y ambos ya son `<select>` nativos sin clases que la contradigan.

**Testing:** no hay test automatizado razonable para contraste visual de un
popup nativo del SO — verificación manual en Chrome/Linux Mint (el
ambiente de la captura original) tras el cambio; documentar en el commit
que es best-effort y que Chromium en Linux no da control total del popup
nativo.

---

## Fuera de alcance (explícito)

No se toca en este trabajo: el mecanismo interno exacto de scheduling de
React Router/React 18-19 que causa la carrera del ítem 1 (se lo vuelve
inofensivo, no se lo resuelve en su origen); ningún cambio a
`ACCESS_TOKEN_LIFETIME`/`REFRESH_TOKEN_LIFETIME` ni a la configuración de
cookies JWT (se descartó como causa tras confirmar que el bug es 100%
cliente); la ventana agendable en sí (`ventana_agendable()`, semana en
curso + siguiente) — el ítem 2 sólo agrega el filtro de 2h que ya existía
en la validación de escritura; ningún cambio a `Disponibilidad`/
`dia_semana` en el backend por el ítem 4; reemplazar los `<select>` nativos
por un componente de listbox propio (se descartó explícitamente a favor del
fix CSS best-effort).
