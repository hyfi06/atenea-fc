# Fixes de staging — 2026-08-19

## Contexto

Revisión manual de staging encontró 5 bugs: uno de permisos (asesor pendiente
de aprobación puede escribir materias/disponibilidad), dos de UX en el flujo
de sesión del asesor (notas sin estado editable/read-only, sin navegación de
regreso), uno de datos (nombre de alumno no se muestra), uno de navegación
(el alumno no puede ver el detalle de su propia asesoría agendada) y uno de
logout (la flecha de regreso del navegador queda apuntando a una pantalla
protegida obsoleta).

B3 y B4 comparten causa y se resuelven con el mismo cambio: extender
`DetalleAsesoria.tsx` para servir también al rol alumno, siguiendo la
decisión de arquitectura ya tomada en este proyecto de tener una vista
unificada por rol en vez de pantallas duplicadas (ver `/asesorias`,
que ya hace esto para la lista).

Todas las rutas de archivo son relativas a `backend/` o `frontend/` según se
indique.

---

## B1 — Asesor pendiente de aprobación puede registrar materias y disponibilidad

**Causa raíz:** `PerfilAsesorAcademico.activo` (`asesorias/models.py:16-34`)
ya distingue asesor aprobado de pendiente — y ya se usa como filtro en las
3 vistas de búsqueda de cara al alumno (`BuscarDisponibilidadView`,
`OfertaView`, `AsesoresDeMateriaView`) — pero nunca se comprueba en escritura.
`RegistroAsesorViewSet` y `DisponibilidadViewSet` (`asesorias/views.py:31-100`)
solo exigen `EsAsesorAcademico` (existe el perfil) y `EsDuenoDelRegistro`
(es el dueño), no `activo`. En el frontend, `useEsAsesor()`
(`auth/rol.ts:12-16`) ignora `activo` a propósito (documentado inline: sigue
el mismo criterio que la permission class), así que ninguna pantalla bloquea
el acceso; el copy de `SolicitudAsesor.tsx:34-36` incluso invita
explícitamente a "cargar tus materias y tu horario" mientras está pendiente.

**Decisión:** bloqueo total — backend rechaza la escritura (defensa en
profundidad) y el frontend oculta las pantallas y da feedback claro en su
lugar, en vez de dejarlas navegables en modo lectura.

### Backend

`backend/asesorias/permissions.py` — nueva permission class, mismo patrón
que las existentes:

```python
class EsAsesorAprobado(BasePermission):
    message = "Tu perfil de asesor está pendiente de revisión de la SAE."

    def has_permission(self, request, view):
        perfil = getattr(request.user, "perfil_asesor_academico", None)
        return perfil is not None and perfil.activo
```

`backend/asesorias/views.py` — agregar `EsAsesorAprobado` a las dos
viewsets (aplica a todas sus acciones, incluida lectura: un asesor pendiente
no tiene nada que listar todavía):

```python
class RegistroAsesorViewSet(ModelViewSet):
    serializer_class = RegistroAsesorSerializer
    permission_classes = [EsAsesorAcademico, EsAsesorAprobado, EsDuenoDelRegistro]
    ...

class DisponibilidadViewSet(ModelViewSet):
    serializer_class = DisponibilidadSerializer
    permission_classes = [EsAsesorAcademico, EsAsesorAprobado, EsDuenoDelRegistro]
    ...
```

Importar `EsAsesorAprobado` en el `from .permissions import (...)` de
`views.py:19-21`.

### Frontend

El dato ya viaja al cliente: `GET /api/auth/user/` expone
`perfil_asesor_academico.activo` (`accounts/serializers.py:151-159`,
ya tipado en `frontend/src/api/types.ts:27-33`). No hace falta tocar el
backend de auth, solo empezar a usarlo.

`frontend/src/auth/rol.ts` — nuevo hook, junto a `useEsAsesor`:

```ts
/** Distinto de useEsAsesor: existe el perfil pero la SAE aún no lo aprueba.
 *  Mientras tanto no puede registrar materias ni disponibilidad (bug de
 *  staging 2026-08-19: antes sí podía). */
export function useAsesorActivo(): boolean {
  return useAuth().user?.perfil_asesor_academico?.activo ?? false
}
```

`frontend/src/features/asesorias/components/AsesorPendiente.tsx` — nuevo
componente, mismo patrón que `SinRegistroAsesor.tsx`:

```tsx
import { useNavigate } from 'react-router-dom'

/** Pantalla de "tu perfil de asesor está pendiente de revisión de la SAE".
 *  Reemplaza Mis materias / Mi horario mientras `activo` sea false. */
export function AsesorPendiente({ titulo }: { titulo: string }) {
  const navigate = useNavigate()
  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>
      <p className="text-sm text-on-surface-variant">
        Tu perfil de asesor está pendiente de que la SAE confirme tu
        nombramiento. Podrás registrar materias y disponibilidad en cuanto
        quede aprobado.
      </p>
    </main>
  )
}
```

`frontend/src/features/asesorias/screens/MisMaterias.tsx` — agregar el
chequeo ANTES del de `!registro` (línea 55-57), mismo criterio en
`MiHorario.tsx:127-129`:

```tsx
import { useAsesorActivo } from '../../../auth/rol'
import { AsesorPendiente } from '../components/AsesorPendiente'
...
  const asesorActivo = useAsesorActivo()
...
  if (!soloLectura && !asesorActivo) {
    return <AsesorPendiente titulo="Mis materias" /* o "Mi horario" */ />
  }

  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }
```

`soloLectura` (modo consulta SAE) no se toca — la SAE sí puede ver el
detalle de cualquier asesor sin que su estado de aprobación se lo impida.

`frontend/src/features/asesorias/screens/Asesorias.tsx:42-60` — ocultar los
botones "Mis materias"/"Mi horario" mientras esté pendiente y mostrar aviso
inline (refuerza el feedback también en la pantalla de entrada, no solo al
navegar directo a la URL):

```tsx
const asesorActivo = useAsesorActivo()
...
{esAsesor && (
  asesorActivo ? (
    <>
      {/* botones "Mis materias" / "Mi horario" existentes, sin cambios */}
    </>
  ) : (
    <p className="w-full text-sm text-on-surface-variant">
      Tu perfil de asesor está pendiente de revisión de la SAE.
    </p>
  )
)}
```

`frontend/src/features/asesorias/screens/SolicitudAsesor.tsx:34-36` —
corregir el copy engañoso:

```tsx
<p className="text-sm text-on-surface-variant">
  Tu perfil de asesor quedó pendiente de que la SAE confirme que tu
  nombramiento está vigente. En cuanto quede aprobado podrás cargar tus
  materias y tu horario.
</p>
```

**Criterio de aceptación:**
- Backend: test en `backend/asesorias/tests/` que haga `POST` a
  `/api/asesorias/registros/` y a `.../disponibilidades/` autenticado como
  asesor con `activo=False`, y assert `403`. Regresión: mismo POST con
  `activo=True` sigue en `201`.
- Frontend: navegar directo a `/asesorias/materias` o `/asesorias/horario`
  como asesor pendiente muestra `AsesorPendiente`, no el formulario. En
  `/asesorias`, los botones "Mis materias"/"Mi horario" no aparecen y sí el
  aviso de pendiente.

---

## B2 — Notas de asesoría: sin estado editable/read-only ni navegación tras guardar

**Componente:** `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`,
función `SeccionAcciones` (líneas 105-249).

**Causa raíz:** el `<textarea>` de notas (líneas 130-138) es siempre
editable cuando `puedeGuardarNotas(asesoria)` es verdadero — no hay
distinción visual entre "puedo escribir" y "esto ya se guardó". El único
feedback al guardar es un toast (`mostrar('Notas guardadas')`,
línea 149) que no cambia el estado del campo. Ni "Guardar notas" ni
"No asistió" navegan a ningún lado: el usuario se queda en el mismo detalle
(la lista se invalida vía `queryClient`, pero no hay redirect).

**Fix — toggle editar/lectura:**

```tsx
function SeccionAcciones({ asesoria }: { asesoria: Asesoria }) {
  const navigate = useNavigate()
  const { mensaje, saliendo, mostrar } = useRetroalimentacion()
  const cancelar = useCancelarAsesoria()
  const marcarAsistencia = useMarcarAsistencia()
  const guardarNotas = useGuardarNotas()
  const [dialogoCancelarAbierto, setDialogoCancelarAbierto] = useState(false)
  const [notas, setNotas] = useState(asesoria.notas)
  const [editandoNotas, setEditandoNotas] = useState(asesoria.notas.trim() === '')
  const [error, setError] = useState<string | null>(null)
  ...
```

Dentro del bloque `asesoria.estado === 'realizada'` (líneas 126-165),
reemplazar el `<textarea>` + botón siempre-editable por:

```tsx
{puedeGuardarNotas(asesoria) ? (
  editandoNotas ? (
    <>
      <textarea
        value={notas}
        onChange={(e) => setNotas(e.target.value)}
        rows={4}
        placeholder="Notas de la sesión…"
        className="rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
      />
      <Boton
        type="button"
        disabled={notas === asesoria.notas}
        cargando={guardarNotas.isPending}
        onClick={() =>
          guardarNotas.mutate(
            { id: asesoria.id, texto: notas },
            {
              onSuccess: () => navigate('/asesorias', { state: { historialDestacarId: asesoria.id } }),
              onError: (err) => setError(primerMensajeDeError(err)),
            },
          )
        }
        className="w-fit px-6"
      >
        Guardar notas
      </Boton>
      {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}
    </>
  ) : (
    <>
      <p className="text-sm text-on-surface">{asesoria.notas}</p>
      <Boton
        type="button"
        variante="secundario"
        onClick={() => setEditandoNotas(true)}
        className="w-fit px-6"
      >
        Editar nota
      </Boton>
    </>
  )
) : null}
```

`editandoNotas` arranca en `true` solo cuando no hay nota previa (primera
vez que se registra la sesión) — así el asesor no ve una vista de "no hay
nada" con un botón adicional para poder escribir por primera vez. Sin botón
de "cancelar edición": salir con "← Volver a Asesorías" ya cumple ese rol y
no agrega un control nuevo que nadie pidió.

**Fix — navegar a historial en "No asistió" y al guardar nota:**

"Guardar notas" ya queda resuelto arriba (`onSuccess` navega). Para
"No asistió" (línea ~199-210):

```tsx
onSuccess: () => navigate('/asesorias', { state: { historialDestacarId: asesoria.id } }),
```

"Asistió" (línea ~180-193) **no cambia**: sigue mostrando el toast y
quedándose en la pantalla, porque revela la caja de notas para que el
asesor las escriba de inmediato — navegar ahí cortaría ese flujo.
"Cancelar asesoría" tampoco cambia (fuera de alcance de este bug).

**Fix — destino: pestaña Historial con foco, reutilizando la infraestructura
que ya existe para "Próximas" tras agendar:**

`frontend/src/features/asesorias/screens/Asesorias.tsx` ya resalta la
tarjeta recién agendada en la pestaña "Próximas" vía `location.state` +
`destacarId` (líneas 20-33, 87-95). Hay que extender el mismo mecanismo a
"Historial", que hoy pasa `destacarId={null}` fijo (línea 135) y usa
`Tabs defaultValue="proximas"` no controlado (línea 81):

```tsx
const [tabActiva, setTabActiva] = useState<'proximas' | 'historial'>('proximas')
const [nuevaAsesoriaId, setNuevaAsesoriaId] = useState<number | null>(null)
const [historialDestacarId, setHistorialDestacarId] = useState<number | null>(null)

useEffect(() => {
  const state = location.state as
    | { nuevaAsesoriaId?: number; historialDestacarId?: number }
    | null
  if (state?.nuevaAsesoriaId != null) {
    setNuevaAsesoriaId(state.nuevaAsesoriaId)
    navigate(location.pathname, { replace: true, state: null })
  } else if (state?.historialDestacarId != null) {
    setHistorialDestacarId(state.historialDestacarId)
    setTabActiva('historial')
    navigate(location.pathname, { replace: true, state: null })
  }
}, [location, navigate])
```

```tsx
<Tabs value={tabActiva} onValueChange={(v) => setTabActiva(v as 'proximas' | 'historial')}>
  ...
  <TabsContent value="historial">
    <Historial nombreMateria={nombreMateria} destacarId={historialDestacarId} />
  </TabsContent>
</Tabs>
```

`Historial` y `ListaAsesorias` reciben y propagan `destacarId` (hoy
`Historial` no tiene esa prop y `ListaAsesorias` recibe `null` fijo en la
línea 135):

```tsx
function Historial({
  nombreMateria,
  destacarId,
}: {
  nombreMateria: (id: number) => string
  destacarId: number | null
}) {
  ...
  <ListaAsesorias
    asesorias={historial(asesorias)}
    cargando={cargandoLista}
    nombreMateria={nombreMateria}
    destacarId={destacarId}
    vacio="Sin sesiones en este semestre."
  />
```

`TarjetaAsesoria` ya sabe hacer scroll+focus+pulso con `destacar` (líneas
62-67, 79 de `components/TarjetaAsesoria.tsx`) — no requiere cambios.

**Nota/riesgo aceptado:** `Historial` selecciona por default el semestre más
reciente (`semestres[0]`, el endpoint ya los ordena de más reciente a más
antiguo — `views.py`, acción `semestres`). Una sesión recién modificada
siempre cae en el semestre vigente, así que el default ya la muestra sin
lógica adicional de selección de semestre.

**Criterio de aceptación:** con una asesoría `realizada` sin notas, "Editar
nota" no aparece (arranca en modo edición); tras "Guardar notas" se navega a
`/asesorias`, la pestaña "Historial" queda activa y la tarjeta modificada
tiene foco + scroll + pulso. Revisitar el detalle después muestra la nota en
modo lectura con botón "Editar nota". Marcar "No asistió" también navega y
enfoca igual. Marcar "Asistió" NO navega — se queda en el detalle con la
caja de notas ahora visible.

---

## B3 — Detalle de asesoría muestra "Alumno #N" en vez del nombre

**Causa raíz:** el dato ya viaja en el payload — `AsesoriaSerializer` expone
`alumno_nombre`/`asesor_nombre` (`asesorias/serializers.py`,
consultados con `select_related` para evitar N+1,
`asesorias/views.py:246-248`) y el tipo `Asesoria` del frontend ya los tipa
(`api/types.ts:100-101`). Otros dos componentes ya los usan correctamente
(`TarjetaAsesoria.tsx:41,44`, `AdminDetalleAsesoria.tsx:74,76`). El bug es
un descuido puntual en un único archivo:
`DetalleAsesoria.tsx:61-62`, que hardcodea `Alumno #{asesoria.alumno}`
(el id crudo) en vez de usar el nombre ya disponible.

Se resuelve junto con B4 (mismo componente, mismo cambio de sección):

```tsx
<dt>{esAsesor ? 'Alumno' : 'Asesor'}</dt>
<dd>{esAsesor ? asesoria.alumno_nombre : asesoria.asesor_nombre}</dd>
```

(requiere `esAsesor` — se importa junto con el resto de cambios de B4, ver
abajo). Los fallbacks `Materia #${id}` / `Carrera #${id}` de las líneas 56 y
64 **no se tocan**: vienen de un catálogo aparte (`useMapaMaterias`/
`useMapaCarreras`) que legítimamente puede no tener la entrada cacheada — no
es el mismo caso que `alumno`, que siempre viaja resuelto en la asesoría.

**Criterio de aceptación:** el detalle de una asesoría (vista asesor y vista
alumno, una vez resuelto B4) muestra el nombre completo de la contraparte,
nunca un id crudo.

---

## B4 — El alumno no puede ver el detalle de su asesoría (ni el salón)

**Causa raíz:** `TarjetaAsesoria.tsx:49` calcula
`interactiva = admin || esAsesor` — un alumno puro nunca obtiene `onClick`,
así que su tarjeta se renderiza como `<div>` no interactivo
(líneas 92-98). Consistente con eso, `/asesorias/:id` en `App.tsx:85-91`
está envuelta en `RutaDeAsesor` (asesor-only): un alumno que llegara ahí por
otra vía sería redirigido a `/home`. El formato/ubicación/liga de la sesión
(`Asesoria.formato/ubicacion/liga_virtual`, ya en el serializer) solo se
renderiza en `DetalleAsesoria.tsx:69-78` (asesor) y `AdminDetalleAsesoria.tsx`
(SAE) — ninguna de las dos alcanzables por el alumno. Resultado: el alumno
no tiene forma de ver dónde ni cómo es su sesión agendada.

**Decisión (confirmada):** reutilizar `DetalleAsesoria.tsx` con render
condicional por rol, en vez de una pantalla `AlumnoDetalleAsesoria.tsx`
aparte — sigue la decisión de arquitectura previa del proyecto de unificar
vistas por rol en una sola ruta (la misma razón por la que `/asesorias` ya
sirve a asesor y alumno con un solo componente).

### Habilitar la ruta y la tarjeta

`frontend/src/App.tsx:85-91` — cambiar el guard de la ruta de detalle:

```tsx
<Route
  path="/asesorias/:id"
  element={
    <RutaDeAsesorias>
      <DetalleAsesoria />
    </RutaDeAsesorias>
  }
/>
```

`frontend/src/features/asesorias/components/TarjetaAsesoria.tsx` — agregar
`esAlumno` a la condición de interactividad:

```tsx
import { useEsAsesor, useEsAlumno } from '../../../auth/rol'
...
const esAsesor = useEsAsesor()
const esAlumno = useEsAlumno()
...
const interactiva = admin || esAsesor || esAlumno
```

### Adaptar `DetalleAsesoria.tsx` al rol alumno

El backend ya autoriza al alumno dueño a leer la asesoría
(`AsesoriaViewSet.get_queryset`, `asesorias/views.py:256-266`, incluye sus
propias sesiones) y a cancelarla (`get_permissions`, línea 237:
`EsAlumnoOAsesorAcademico` para la acción `cancelar`). `notas` ya viene
excluida del payload para el alumno (`to_representation`,
`serializers.py:202-216`, `data.pop("notas", None)` salvo dueño/SAE). Lo que
falta es que el frontend oculte los controles que son exclusivos del asesor
(marcar asistencia, notas) y ajuste el texto para no leerse en tercera
persona cuando quien mira es el propio alumno:

```tsx
import { useEsAsesor } from '../../../auth/rol'
...
export function DetalleAsesoria() {
  const esAsesor = useEsAsesor()
  ...
  const previas = esAsesor ? sesionesPreviasConNotas(asesorias, asesoria.alumno, asesoria.id) : []
  ...
  {esAsesor && previas.length > 0 && (
    <section>
      <h2 className="mb-2 text-sm font-medium text-on-surface">Notas de sesiones anteriores con este alumno</h2>
      {/* ...lista existente... */}
    </section>
  )}
```

En `SeccionAcciones`, llamar `useEsAsesor()` directamente al inicio de la
función (es un hook, no requiere pasarlo por props desde `DetalleAsesoria`)
y condicionar:

- Bloque `estado === 'realizada'` (línea 126-165): el párrafo de asistencia
  usa wording neutral en vez de en tercera persona fija:
  `{asesoria.asistio ? 'Asistió a la sesión.' : 'No asistió a la sesión.'}`
  (funciona igual de bien leído por el asesor o por el alumno, sin tocar
  gramática por rol). El bloque de notas (editar/guardar, ver B2) se envuelve
  en `{esAsesor && (...)}`.
- Bloque no-`realizada`/no-`cancelada` (línea 167-221): la pregunta "¿El
  alumno asistió...?" + botones Asistió/No asistió se envuelven en
  `{esAsesor && yaOcurrio && (...)}`. El botón "Cancelar asesoría" **no** se
  envuelve — el backend ya permite cancelar tanto a alumno como a asesor
  dueños, así que se mantiene visible para ambos.

**Criterio de aceptación:** un alumno con una asesoría agendada puede tocar
su tarjeta en `/asesorias`, llega a `/asesorias/:id`, ve materia, nombre del
asesor (B3), fecha/hora, formato/ubicación o liga virtual, y puede cancelar.
No ve botones de marcar asistencia ni caja de notas. Un asesor que visita el
detalle de otro asesor (URL ajena) sigue recibiendo el 404 actual (sin
cambios en ese camino).

---

## B5 — Logout: la flecha de regreso del navegador queda apuntando a una pantalla protegida obsoleta

**Causa raíz:** `MenuUsuario.tsx:65-72` ya navega a `/` (Landing, pública) —
no a `/login` como se sospechaba — pero sin `replace: true`. La pantalla
protegida desde la que se hizo logout queda en el historial del navegador;
al presionar la flecha de regreso, el navegador intenta volver a esa
entrada, cuyo guard (`RutaConSesion`/`RutaDeAsesorias`/etc. en
`RutaProtegida.tsx`) redirige a `/login` por sesión inexistente — de ahí la
sensación de que "la flecha no hace nada" o "regresa al login". Relacionado:
`AuthContext.tsx`'s `logout()` (líneas 66-75) nunca limpia la caché de
`react-query` (`main.tsx:8-11` crea un único `QueryClient` de módulo); las
queries de asesorías/materias no están namespaced por usuario, así que en un
navegador compartido el siguiente login podría mostrar por un instante datos
cacheados del usuario anterior.

**Fix — navegación:** `frontend/src/components/MenuUsuario.tsx:65-72`:

```tsx
async function cerrarSesion() {
  setCerrando(true)
  await logout()
  navigate('/', { replace: true })
}
```

**Fix — limpiar caché de react-query:** `frontend/src/auth/AuthContext.tsx`
— usar `useQueryClient()` (el `QueryClientProvider` en `main.tsx:15-19` ya
envuelve a `AuthProvider`, así que el hook está disponible) y llamarlo desde
`logout()`:

```tsx
import { useQueryClient } from '@tanstack/react-query'
...
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  ...
  async function logout() {
    try {
      await apiPost('/api/auth/logout/', {})
    } catch {
      // el logout limpia el lado del cliente igual aunque el request falle
    }
    limpiarSesion()
    queryClient.clear()
    setUser(null)
    setStatus('unauthenticated')
  }
```

**Criterio de aceptación:** cerrar sesión desde `/home`, presionar el botón
de regreso del navegador — permanece en Landing (o llega directo a
`/login` sin pasar por una pantalla protegida a medio cargar). Con dos
usuarios distintos en el mismo navegador (logout de A, login de B), ninguna
pantalla de B muestra brevemente datos de A. Test: extender
`frontend/src/auth/AuthContext.test.tsx` (si existe una suite ahí; si no,
crear un caso mínimo) que haga login, popule una query, llame `logout()` y
assert `queryClient.getQueryData(...)` regresa `undefined`.

---

## Fuera de alcance (explícito)

No tocar en este trabajo: motivo de cancelación no expuesto en el
serializer (deuda técnica 0010, mencionada inline en `DetalleAsesoria.tsx`),
límite de 2hrs antes de asesoría, cierre automático de sesiones vencidas,
paginación de materias, flujo de recuperación de contraseña — todo eso ya
tiene sus propios specs de sprint (`2026-08-19-asesorias-limites-cierre-
propagacion-design.md`, `2026-08-19-catalogo-materias-scroll-infinito-
design.md`, `2026-08-19-auth-reset-blacklist-csrf-design.md`). Tampoco se
toca el botón "Cancelar asesoría" ni el flujo de agendado nuevo — ninguno de
los 5 bugs los involucra.

**Hallazgo posterior (revisión final de implementación):** B3/B4 asumen
que `useEsAsesor()` identifica correctamente el rol de quien mira una
asesoría. Para un usuario con doble rol (alumno y asesor, caso ya
contemplado por el backend — deuda 0011, resuelta) abriendo una sesión
donde participa como alumno, esto etiqueta mal la pantalla y puede
intentar leer `notas`, que el serializer oculta para quien no es el
asesor dueño. No alcanzable en el despliegue actual (ningún usuario real
tiene hoy doble rol simultáneo) — documentado como deuda técnica
[0022](../../technical-debt/0022-deteccion-de-rol-por-usuario-no-por-sesion.md)
en vez de resolverse dentro de este sprint.
