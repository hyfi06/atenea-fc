# Fixes de staging (B1–B5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir los 5 bugs de la revisión manual de staging del 2026-08-19 (permisos de asesor pendiente, notas de sesión, nombre de alumno, detalle de asesoría para el alumno, logout).

**Architecture:** Backend: una permission class nueva en `asesorias/permissions.py` aplicada a 2 viewsets. Frontend: un hook de rol nuevo (`useAsesorActivo`), un componente de estado nuevo (`AsesorPendiente`), y render condicional por rol en `DetalleAsesoria.tsx`/`TarjetaAsesoria.tsx` en vez de pantallas duplicadas.

**Tech Stack:** Django 6 + DRF (tests con `APITestCase`, runner de Django), React 19 + TypeScript + Vite + Tailwind v4 + Radix/shadcn, Vitest + Testing Library, TanStack Query v5, React Router v7.

**Spec:** `docs/superpowers/specs/2026-08-19-fixes-staging-design.md`

## ⚠ Requiere mockup

Ninguna pieza. `AsesorPendiente.tsx` es variante de `SinRegistroAsesor.tsx`; el toggle editar/lectura y el aviso inline de "pendiente" no introducen patrones de interacción nuevos.

## Global Constraints

- **Tests backend:** desde `backend/`, `uv run manage.py test <ruta> -v 2`. Requiere Postgres y Redis: `docker compose -f docker-compose.dev.yml up -d postgres redis` desde la raíz.
- **Tests frontend:** desde `frontend/`, test puntual `npx vitest run <ruta>`; suite `npm test`; build `npm run build`; lint `npm run lint`.
- **Color:** solo tokens M3 existentes (`bg-secondary-container`, `text-on-secondary-container`, `text-on-surface-variant`, …). Nunca un hex literal.
- **Motion:** solo clases ya definidas en `frontend/src/index.css` (`entrada-lista`, `pulso-exito`, `presionable`, `fila-interactiva`, `foco-visible`). No se agregan `@keyframes` nuevos en este plan.
- **Foco:** todo control interactivo nuevo lleva `foco-visible` (o hereda el `focus-visible:outline-*` de `components/ui/Boton.tsx`).
- **Commits:** formato `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>`.

---

### Task 1: Backend — `EsAsesorAprobado` bloquea la escritura del asesor pendiente (B1)

**Files:**
- Modify: `backend/asesorias/permissions.py` (agregar clase al final)
- Modify: `backend/asesorias/views.py:19-21` (import), `:31-33` y `:67-69` (`permission_classes`)
- Test: `backend/asesorias/tests/test_api_asesor_pendiente.py` (crear)

**Interfaces:**
- Consumes: nada.
- Produces: `asesorias.permissions.EsAsesorAprobado` — `BasePermission` con `has_permission(self, request, view) -> bool`, `message: str`.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/asesorias/tests/test_api_asesor_pendiente.py`:

```python
import datetime

from academico.models import PeriodoAcademico
from academico.servicios import semestre_vigente
from accounts.models import PerfilAcademico, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area
from rest_framework.test import APITestCase


class AsesorPendienteApiTests(APITestCase):
    def setUp(self):
        self.semestre = semestre_vigente()
        PeriodoAcademico.objects.create(
            semestre=self.semestre,
            fecha_inicio=datetime.date(2000, 1, 1),
            fecha_fin=datetime.date(2099, 12, 31),
            registro_asesores_inicio=datetime.date(2000, 1, 1),
            registro_asesores_fin=datetime.date(2099, 12, 31),
        )
        self.area = Area.objects.create(nombre="Area pendiente")

        self.pendiente_user = User.objects.create_user(
            email="pendiente@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.pendiente_user, numero_trabajador="90001")
        self.pendiente = PerfilAsesorAcademico.objects.create(
            user=self.pendiente_user, area=self.area, activo=False)
        self.registro_pendiente = RegistroAsesor.objects.create(
            asesor=self.pendiente, semestre=self.semestre)

        self.aprobado_user = User.objects.create_user(
            email="aprobado@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.aprobado_user, numero_trabajador="90002")
        self.aprobado = PerfilAsesorAcademico.objects.create(
            user=self.aprobado_user, area=self.area, activo=True)

    def test_pendiente_no_puede_crear_registro(self):
        self.client.force_authenticate(user=self.pendiente_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 403)

    def test_pendiente_no_puede_listar_registros(self):
        self.client.force_authenticate(user=self.pendiente_user)
        response = self.client.get("/api/asesorias/registros/")
        self.assertEqual(response.status_code, 403)

    def test_pendiente_no_puede_crear_disponibilidad(self):
        self.client.force_authenticate(user=self.pendiente_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro_pendiente.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 403)

    def test_aprobado_sigue_creando_registro(self):
        self.client.force_authenticate(user=self.aprobado_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 201)

    def test_aprobado_sigue_creando_disponibilidad(self):
        registro = RegistroAsesor.objects.create(asesor=self.aprobado, semestre=self.semestre)
        self.client.force_authenticate(user=self.aprobado_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Disponibilidad.objects.filter(id=response.data["id"]).exists())
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run manage.py test asesorias.tests.test_api_asesor_pendiente -v 2`
Expected: FAIL — los 3 tests de `pendiente` esperan 403 y reciben 201/200.

- [ ] **Step 3: Agregar la permission class**

Al final de `backend/asesorias/permissions.py`:

```python
class EsAsesorAprobado(BasePermission):
    message = "Tu perfil de asesor está pendiente de revisión de la SAE."

    def has_permission(self, request, view):
        perfil = getattr(request.user, "perfil_asesor_academico", None)
        return perfil is not None and perfil.activo
```

- [ ] **Step 4: Aplicarla a las dos viewsets**

En `backend/asesorias/views.py`, reemplazar el bloque de import (líneas 19-21):

```python
from .permissions import (
    EsAcademico, EsAlumno, EsAlumnoOAsesorAcademico, EsAlumnoOMiembroSAE, EsAsesorAcademico, EsAsesorAprobado, EsMiembroSAE, EsDuenoDelRegistro, EsDuenoDeLaAsesoria,
)
```

En `RegistroAsesorViewSet`, reemplazar:

```python
    permission_classes = [EsAsesorAcademico, EsDuenoDelRegistro]
```

por:

```python
    permission_classes = [EsAsesorAcademico, EsAsesorAprobado, EsDuenoDelRegistro]
```

En `DisponibilidadViewSet`, reemplazar:

```python
    permission_classes = [EsAsesorAcademico, EsDuenoDelRegistro]
```

por:

```python
    permission_classes = [EsAsesorAcademico, EsAsesorAprobado, EsDuenoDelRegistro]
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `uv run manage.py test asesorias.tests.test_api_asesor_pendiente -v 2`
Expected: PASS (5 tests)

- [ ] **Step 6: Correr la suite de `asesorias` para descartar regresiones**

Run: `uv run manage.py test asesorias -v 2`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/asesorias/permissions.py backend/asesorias/views.py backend/asesorias/tests/test_api_asesor_pendiente.py
git commit -m "$(cat <<'EOF'
[fix][backend] rechazar escritura de materias y disponibilidad al asesor pendiente

- nueva permission class EsAsesorAprobado (perfil existe y activo=True)
- aplicada a RegistroAsesorViewSet y DisponibilidadViewSet, todas sus acciones
- tests de 403 para asesor pendiente y regresión de 201 para asesor aprobado

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 2: Hook `useAsesorActivo` (B1)

**Files:**
- Modify: `frontend/src/auth/rol.ts` (agregar hook después de `useEsAsesor`)
- Test: `frontend/src/auth/rol.test.tsx` (agregar describe al final)

**Interfaces:**
- Consumes: `useAuth()` de `frontend/src/auth/AuthContext.tsx`; el campo `AuthUser.perfil_asesor_academico.activo` ya tipado en `frontend/src/api/types.ts:27-34`.
- Produces: `useAsesorActivo(): boolean` exportado desde `frontend/src/auth/rol.ts`. Lo consumen las Tasks 4 y 5.

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `frontend/src/auth/rol.test.tsx`:

```tsx
function SondaAsesorActivo() {
  const activo = useAsesorActivo()
  return <div data-testid="activo">{`activo=${activo}`}</div>
}

describe('useAsesorActivo', () => {
  afterEach(() => vi.restoreAllMocks())

  it('es true cuando la SAE ya aprobó el perfil', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: true },
      }),
    )
    render(
      <AuthProvider>
        <SondaAsesorActivo />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('activo')).toHaveTextContent('activo=true'))
  })

  it('es false mientras el perfil está pendiente, aunque useEsAsesor sea true', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: false },
      }),
    )
    render(
      <AuthProvider>
        <SondaAsesorActivo />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('activo')).toHaveTextContent('activo=false'))
  })

  it('es false para quien no tiene perfil de asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    render(
      <AuthProvider>
        <SondaAsesorActivo />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('activo')).toHaveTextContent('activo=false'))
  })
})
```

Y en la línea 4 del mismo archivo, reemplazar el import:

```tsx
import { useEsAlumno, useEsAsesor, useEsMiembroSAE, useEsAcademico, useAsesorActivo } from './rol'
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run (desde `frontend/`): `npx vitest run src/auth/rol.test.tsx`
Expected: FAIL — `useAsesorActivo is not a function` / error de import.

- [ ] **Step 3: Implementar el hook**

En `frontend/src/auth/rol.ts`, inmediatamente después de la función `useEsAsesor`:

```ts
/** Distinto de useEsAsesor: existe el perfil pero la SAE aún no lo aprueba.
 *  Mientras tanto no puede registrar materias ni disponibilidad (bug de
 *  staging 2026-08-19: antes sí podía). */
export function useAsesorActivo(): boolean {
  return useAuth().user?.perfil_asesor_academico?.activo ?? false
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/auth/rol.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/auth/rol.ts frontend/src/auth/rol.test.tsx
git commit -m "$(cat <<'EOF'
[feat][frontend] agregar hook useAsesorActivo para distinguir asesor aprobado de pendiente

- lee perfil_asesor_academico.activo, que ya viaja en GET /api/auth/user/
- useEsAsesor no cambia: sigue el criterio de EsAsesorAcademico (perfil existe)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 3: Componente `AsesorPendiente` (B1)

**Files:**
- Create: `frontend/src/features/asesorias/components/AsesorPendiente.tsx`
- Test: `frontend/src/features/asesorias/components/AsesorPendiente.test.tsx` (crear)

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `AsesorPendiente({ titulo }: { titulo: string })` exportado desde `frontend/src/features/asesorias/components/AsesorPendiente.tsx`. Lo consume la Task 4.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/features/asesorias/components/AsesorPendiente.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AsesorPendiente } from './AsesorPendiente'

function montar(titulo = 'Mis materias') {
  render(
    <MemoryRouter initialEntries={['/asesorias/materias']}>
      <Routes>
        <Route path="/asesorias/materias" element={<AsesorPendiente titulo={titulo} />} />
        <Route path="/asesorias" element={<p>lista de asesorías</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AsesorPendiente', () => {
  it('anuncia el título de la pantalla desde la que se llegó', () => {
    montar('Mi horario')
    expect(screen.getByRole('heading', { name: 'Mi horario' })).toBeInTheDocument()
  })

  it('explica que la SAE aún no confirma el nombramiento', () => {
    montar()
    expect(screen.getByText(/pendiente de que la SAE confirme tu nombramiento/i)).toBeInTheDocument()
  })

  it('ofrece volver a Asesorías', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Volver a Asesorías' }))
    expect(screen.getByText('lista de asesorías')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/components/AsesorPendiente.test.tsx`
Expected: FAIL — no existe `./AsesorPendiente`.

- [ ] **Step 3: Implementar el componente**

Crear `frontend/src/features/asesorias/components/AsesorPendiente.tsx`:

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
      <p role="status" className="entrada-lista max-w-prose rounded-lg bg-secondary-container px-3 py-2 text-sm text-on-secondary-container">
        Tu perfil de asesor está pendiente de que la SAE confirme tu
        nombramiento. Podrás registrar materias y disponibilidad en cuanto
        quede aprobado.
      </p>
    </main>
  )
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/components/AsesorPendiente.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/components/AsesorPendiente.tsx frontend/src/features/asesorias/components/AsesorPendiente.test.tsx
git commit -m "$(cat <<'EOF'
[feat][frontend] agregar pantalla AsesorPendiente para el asesor sin aprobar

- mismo patrón que SinRegistroAsesor: volver + título + explicación
- aviso con el par secondary-container/on-secondary-container y role="status"

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 4: Guard de `Mis materias` y `Mi horario` (B1)

**Files:**
- Modify: `frontend/src/features/asesorias/screens/MisMaterias.tsx` (imports + guard antes de la línea 55)
- Modify: `frontend/src/features/asesorias/screens/MiHorario.tsx` (imports + guard antes de la línea 127)
- Test: `frontend/src/features/asesorias/screens/MisMaterias.test.tsx` (modificar `montar` + test nuevo)
- Test: `frontend/src/features/asesorias/screens/MiHorario.test.tsx` (modificar `montar` + test nuevo)

**Interfaces:**
- Consumes: `useAsesorActivo()` (Task 2), `AsesorPendiente` (Task 3).
- Produces: nada para tasks posteriores.
- **Depende de:** Tasks 2 y 3.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/features/asesorias/screens/MisMaterias.test.tsx`, agregar el import tras la línea 7:

```tsx
import * as rol from '../../../auth/rol'
```

Reemplazar la firma y la primera línea de `montar`:

```tsx
function montar({ asesorActivo = true }: { asesorActivo?: boolean } = {}) {
  vi.spyOn(rol, 'useAsesorActivo').mockReturnValue(asesorActivo)
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: REGISTRO, cargando: false })
```

Agregar dentro del `describe('MisMaterias', ...)`:

```tsx
  it('el asesor pendiente de aprobación ve el aviso en vez del formulario', () => {
    montar({ asesorActivo: false })
    expect(screen.getByText(/pendiente de que la SAE confirme tu nombramiento/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: NOMBRE_LARGO })).not.toBeInTheDocument()
  })
```

En `frontend/src/features/asesorias/screens/MiHorario.test.tsx`, agregar el import tras la línea 6:

```tsx
import * as rol from '../../../auth/rol'
```

Reemplazar la firma y la primera línea de `montar`:

```tsx
function montar({
  disponibilidades = [BLOQUE_LUNES],
  totalSesionesFuturas = 0,
  asesorActivo = true,
}: { disponibilidades?: Disponibilidad[]; totalSesionesFuturas?: number; asesorActivo?: boolean } = {}) {
  vi.spyOn(rol, 'useAsesorActivo').mockReturnValue(asesorActivo)
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: REGISTRO, cargando: false })
```

Agregar dentro del `describe` principal de `MiHorario`:

```tsx
  it('el asesor pendiente de aprobación ve el aviso en vez de la rejilla', () => {
    montar({ asesorActivo: false })
    expect(screen.getByText(/pendiente de que la SAE confirme tu nombramiento/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Mi horario' })).toBeInTheDocument()
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/features/asesorias/screens/MisMaterias.test.tsx src/features/asesorias/screens/MiHorario.test.tsx`
Expected: FAIL — `useAsesorActivo` no se usa en las pantallas, así que el aviso nunca aparece.

- [ ] **Step 3: Agregar el guard en `MisMaterias.tsx`**

Agregar los imports (tras `import { primerMensajeDeError } from '../../../api/errores'`):

```tsx
import { useAsesorActivo } from '../../../auth/rol'
```

y junto a los demás imports de `../components/`:

```tsx
import { AsesorPendiente } from '../components/AsesorPendiente'
```

Dentro de `MisMaterias`, tras `const navigate = useNavigate()`:

```tsx
  const asesorActivo = useAsesorActivo()
```

Reemplazar el bloque:

```tsx
  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }
```

por:

```tsx
  if (!soloLectura && !asesorActivo) {
    return <AsesorPendiente titulo="Mis materias" />
  }

  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }
```

- [ ] **Step 4: Agregar el guard en `MiHorario.tsx`**

Agregar los imports (tras `import { primerMensajeDeError } from '../../../api/errores'`):

```tsx
import { useAsesorActivo } from '../../../auth/rol'
```

y junto a los demás imports de `../components/`:

```tsx
import { AsesorPendiente } from '../components/AsesorPendiente'
```

Dentro de `MiHorario`, tras `const navigate = useNavigate()`:

```tsx
  const asesorActivo = useAsesorActivo()
```

Reemplazar el bloque:

```tsx
  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mi horario" />
  }
```

por:

```tsx
  if (!soloLectura && !asesorActivo) {
    return <AsesorPendiente titulo="Mi horario" />
  }

  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mi horario" />
  }
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/screens/MisMaterias.test.tsx src/features/asesorias/screens/MiHorario.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/MisMaterias.tsx frontend/src/features/asesorias/screens/MiHorario.tsx frontend/src/features/asesorias/screens/MisMaterias.test.tsx frontend/src/features/asesorias/screens/MiHorario.test.tsx
git commit -m "$(cat <<'EOF'
[fix][frontend] mostrar AsesorPendiente en Mis materias y Mi horario mientras la SAE no aprueba

- el chequeo va antes del de "sin registro": sin aprobación no hay nada que registrar
- el modo consulta de la SAE (soloLectura) no se ve afectado

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 5: `Asesorias.tsx` — aviso de pendiente y destacado en Historial; copy de `SolicitudAsesor` (B1 + B2)

**Files:**
- Modify: `frontend/src/features/asesorias/screens/Asesorias.tsx` (imports, estado, `useEffect`, bloque de botones, `Tabs`, `Historial`)
- Modify: `frontend/src/features/asesorias/screens/SolicitudAsesor.tsx:34-37` (copy)
- Test: `frontend/src/features/asesorias/screens/Asesorias.test.tsx` (modificar `montar` + tests nuevos)

**Interfaces:**
- Consumes: `useAsesorActivo()` (Task 2).
- Produces: `Asesorias` consume `location.state.historialDestacarId?: number` — la Task 8 navega con exactamente ese nombre de clave. `Historial` pasa a recibir `destacarId: number | null`.
- **Depende de:** Task 2. La Task 8 depende de esta.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/features/asesorias/screens/Asesorias.test.tsx`, reemplazar `envolver` y `montar` por:

```tsx
function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[{ pathname: '/asesorias', state: estadoInicial }]}>
        <Routes>
          <Route path="/asesorias" element={children} />
          <Route path="/home" element={<p>pantalla home</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

let estadoInicial: unknown = null

function montar({
  esAsesor,
  esAlumno,
  asesorActivo = true,
  state = null,
  historial = [],
}: {
  esAsesor: boolean
  esAlumno: boolean
  asesorActivo?: boolean
  state?: unknown
  historial?: Asesoria[]
}) {
  estadoInicial = state
  // jsdom no implementa scrollIntoView y `destacar` lo invoca.
  Element.prototype.scrollIntoView = vi.fn()
  vi.spyOn(rol, 'useEsAsesor').mockReturnValue(esAsesor)
  vi.spyOn(rol, 'useEsAlumno').mockReturnValue(esAlumno)
  vi.spyOn(rol, 'useEsAcademico').mockReturnValue(false)
  vi.spyOn(rol, 'useAsesorActivo').mockReturnValue(asesorActivo)
  vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
    data: [crearAsesoria({ id: 1 })], isPending: false,
  } as ReturnType<typeof api.useMisAsesorias>)
  vi.spyOn(api, 'useSemestres').mockReturnValue({
    data: historial.length > 0 ? ['20262'] : [], isPending: false,
  } as ReturnType<typeof api.useSemestres>)
  vi.spyOn(api, 'useAsesoriasDeSemestre').mockReturnValue({
    data: historial, isPending: false,
  } as ReturnType<typeof api.useAsesoriasDeSemestre>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )
  render(<Asesorias />, { wrapper: envolver })
}
```

Agregar estos tests dentro del `describe('Asesorias (vista unificada)', ...)`:

```tsx
  it('el asesor pendiente no ve Mis materias / Mi horario sino el aviso de revisión', () => {
    montar({ esAsesor: true, esAlumno: false, asesorActivo: false })
    expect(screen.queryByRole('button', { name: 'Mis materias' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mi horario' })).not.toBeInTheDocument()
    expect(screen.getByText('Tu perfil de asesor está pendiente de revisión de la SAE.')).toBeInTheDocument()
  })

  it('al llegar con historialDestacarId abre la pestaña Historial', () => {
    montar({
      esAsesor: true,
      esAlumno: false,
      state: { historialDestacarId: 7 },
      historial: [crearAsesoria({ id: 7, estado: 'realizada', fecha: '2020-01-01' })],
    })
    expect(screen.getByRole('tab', { name: 'Historial' })).toHaveAttribute('aria-selected', 'true')
  })

  it('destaca en Historial la sesión que viene en el router state', () => {
    montar({
      esAsesor: true,
      esAlumno: false,
      state: { historialDestacarId: 7 },
      historial: [crearAsesoria({ id: 7, estado: 'realizada', fecha: '2020-01-01' })],
    })
    expect(screen.getByRole('button', { name: /Cálculo I/ })).toHaveClass('pulso-exito')
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx`
Expected: FAIL — `useAsesorActivo` no se usa, `Tabs` no es controlado y `Historial` pasa `destacarId={null}` fijo.

- [ ] **Step 3: Actualizar `Asesorias.tsx`**

Reemplazar la línea 9 (import de rol):

```tsx
import { useEsAsesor, useEsAlumno, useEsAcademico, useAsesorActivo } from '../../../auth/rol'
```

Reemplazar el bloque de estado + efecto (líneas 15-33) por:

```tsx
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  const esAcademico = useEsAcademico()
  const asesorActivo = useAsesorActivo()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()
  // `location.state` sobrevive a refresh/back-nav, así que el resaltado se
  // reactivaría sobre una asesoría vieja. Lo consumimos una vez: leemos el id
  // a estado local y limpiamos el state de navegación para que el pulso/scroll
  // dispare sólo tras el agendado real.
  const [tabActiva, setTabActiva] = useState<'proximas' | 'historial'>('proximas')
  const [nuevaAsesoriaId, setNuevaAsesoriaId] = useState<number | null>(null)
  const [historialDestacarId, setHistorialDestacarId] = useState<number | null>(null)
  const nombreMateria = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

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

Reemplazar el bloque `{esAsesor && (...)}` (líneas 43-60) por:

```tsx
        {esAsesor &&
          (asesorActivo ? (
            <>
              <button
                type="button"
                onClick={() => navigate('/asesorias/materias')}
                className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
              >
                Mis materias
              </button>
              <button
                type="button"
                onClick={() => navigate('/asesorias/horario')}
                className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
              >
                Mi horario
              </button>
            </>
          ) : (
            <p role="status" className="entrada-lista w-full rounded-lg bg-secondary-container px-3 py-2 text-sm text-on-secondary-container">
              Tu perfil de asesor está pendiente de revisión de la SAE.
            </p>
          ))}
```

Reemplazar la apertura de `Tabs` (línea 81):

```tsx
      <Tabs value={tabActiva} onValueChange={(v) => setTabActiva(v as 'proximas' | 'historial')}>
```

Reemplazar el `TabsContent` de historial (líneas 96-98):

```tsx
        <TabsContent value="historial">
          <Historial nombreMateria={nombreMateria} destacarId={historialDestacarId} />
        </TabsContent>
```

Reemplazar la firma de `Historial` (línea 104):

```tsx
function Historial({
  nombreMateria,
  destacarId,
}: {
  nombreMateria: (id: number) => string
  destacarId: number | null
}) {
```

Reemplazar el `destacarId={null}` de su `ListaAsesorias` (línea 135):

```tsx
        destacarId={destacarId}
```

- [ ] **Step 4: Corregir el copy de `SolicitudAsesor.tsx`**

Reemplazar el párrafo de la pantalla "Solicitud enviada" (líneas 34-37):

```tsx
        <p className="text-sm text-on-surface-variant">
          Tu perfil de asesor quedó pendiente de que la SAE confirme que tu
          nombramiento está vigente. En cuanto quede aprobado podrás cargar tus
          materias y tu horario.
        </p>
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx src/features/asesorias/screens/SolicitudAsesor.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/Asesorias.tsx frontend/src/features/asesorias/screens/Asesorias.test.tsx frontend/src/features/asesorias/screens/SolicitudAsesor.tsx
git commit -m "$(cat <<'EOF'
[fix][frontend] avisar del perfil pendiente en Asesorías y permitir destacar en Historial

- oculta Mis materias / Mi horario mientras la SAE no aprueba el perfil
- Tabs pasa a controlado: historialDestacarId del router state abre Historial
- Historial y ListaAsesorias propagan destacarId (scroll + foco + pulso)
- corrige el copy de SolicitudAsesor, que invitaba a cargar materias sin permiso

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 6: Tarjeta interactiva y ruta de detalle para el alumno (B4)

**Files:**
- Modify: `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx:5` (import), `:36-37` (hooks), `:49` (`interactiva`)
- Modify: `frontend/src/App.tsx:84-91` (guard de `/asesorias/:id`)
- Test: `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx` (mocks + tests)

**Interfaces:**
- Consumes: `useEsAlumno()` (ya existe en `frontend/src/auth/rol.ts`).
- Produces: `/asesorias/:id` accesible para alumno y asesor. La Task 7 asume esa ruta.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx`, reemplazar el test `'para el alumno muestra el nombre del asesor y no navega'` por:

```tsx
  it('para el alumno muestra el nombre del asesor y navega a su detalle', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(true)
    render(
      <MemoryRouter initialEntries={['/asesorias']}>
        <Routes>
          <Route
            path="/asesorias"
            element={<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />}
          />
          <Route path="/asesorias/1" element={<p>detalle de la asesoría</p>} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText(/Ana Asesora/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('detalle de la asesoría')).toBeInTheDocument()
  })

  it('quien no es alumno ni asesor ni admin recibe una tarjeta no interactiva', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    render(<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
```

Agregar `vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)` como primera línea del cuerpo de cada uno de los tests restantes del archivo (los que hoy solo mockean `useEsAsesor`): `'para el asesor muestra el nombre del alumno en un botón'`, `'nunca renderiza las notas'`, `'en modo admin muestra ambos nombres y tampoco las notas'`, `'en modo admin es interactiva aunque quien mire no sea asesor'`, `'en modo admin navega al detalle SAE y no al del asesor'` y `'en modo admin lleva la sesión y la materia en el router state'`.

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: FAIL — `useEsAlumno` no es llamado por el componente, así que el spy no aplica y el alumno no obtiene botón.

- [ ] **Step 3: Hacer interactiva la tarjeta del alumno**

En `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`, reemplazar la línea 5:

```tsx
import { useEsAsesor, useEsAlumno } from '../../../auth/rol'
```

Reemplazar la línea 36 (`const esAsesor = useEsAsesor()`) por:

```tsx
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
```

Reemplazar la línea 49:

```tsx
  const interactiva = admin || esAsesor || esAlumno
```

- [ ] **Step 4: Abrir la ruta de detalle al alumno**

En `frontend/src/App.tsx`, reemplazar el `Route` de `/asesorias/:id`:

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

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/components/TarjetaAsesoria.tsx frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx frontend/src/App.tsx
git commit -m "$(cat <<'EOF'
[fix][frontend] dar al alumno acceso al detalle de su asesoría

- TarjetaAsesoria es interactiva también para el alumno dueño
- /asesorias/:id pasa de RutaDeAsesor a RutaDeAsesorias

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 7: `DetalleAsesoria` — nombre de la contraparte y render por rol (B3 + B4)

**Files:**
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`
- Test: `frontend/src/features/asesorias/screens/DetalleAsesoria.test.tsx` (crear)

**Interfaces:**
- Consumes: `useEsAsesor()` de `frontend/src/auth/rol.ts`; ruta abierta al alumno (Task 6).
- Produces: `SeccionAcciones` con `const esAsesor = useEsAsesor()` ya declarado y el bloque `estado === 'realizada'` ya envuelto en `{esAsesor && puedeGuardarNotas(asesoria) ? … : null}` — la Task 8 reemplaza el interior de ese ternario.
- **Depende de:** Task 6. La Task 8 depende de esta.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/DetalleAsesoria.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { DetalleAsesoria } from './DetalleAsesoria'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

function crearAsesoria(overrides: Partial<Asesoria> = {}): Asesoria {
  return {
    id: 1, alumno: 10, alumno_nombre: 'Beto Alumno', asesor_nombre: 'Ana Asesora',
    disponibilidad: 1, materia: 1, carrera: 1, fecha: '2020-01-01', hora_inicio: '10:00:00',
    formato: 'presencial', ubicacion: 'Salón O-221', liga_virtual: '', estado: 'agendada',
    asistio: null, notas: '', creado_en: '2020-01-01T10:00:00Z', ...overrides,
  }
}

/** Ruta destino de mentira: revela a dónde navegó y con qué router state. */
function EspiaAsesorias() {
  const { state } = useLocation() as { state: { historialDestacarId?: number } | null }
  return <p data-testid="destino">{`asesorias:${state?.historialDestacarId ?? 'sin-id'}`}</p>
}

function montar(asesoria: Asesoria, esAsesor: boolean) {
  vi.spyOn(rol, 'useEsAsesor').mockReturnValue(esAsesor)
  vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
    data: [asesoria], isPending: false,
  } as ReturnType<typeof api.useMisAsesorias>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Actuaría' } as never]]),
  )
  const guardarNotas = vi.fn((_vars: unknown, opciones: { onSuccess?: () => void }) => opciones?.onSuccess?.())
  const marcarAsistencia = vi.fn((_vars: unknown, opciones: { onSuccess?: () => void }) => opciones?.onSuccess?.())
  vi.spyOn(api, 'useGuardarNotas').mockReturnValue({
    mutate: guardarNotas, isPending: false,
  } as unknown as ReturnType<typeof api.useGuardarNotas>)
  vi.spyOn(api, 'useMarcarAsistencia').mockReturnValue({
    mutate: marcarAsistencia, isPending: false,
  } as unknown as ReturnType<typeof api.useMarcarAsistencia>)
  vi.spyOn(api, 'useCancelarAsesoria').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useCancelarAsesoria>)

  render(
    <MemoryRouter initialEntries={['/asesorias/1']}>
      <Routes>
        <Route path="/asesorias/:id" element={<DetalleAsesoria />} />
        <Route path="/asesorias" element={<EspiaAsesorias />} />
      </Routes>
    </MemoryRouter>,
  )
  return { guardarNotas, marcarAsistencia }
}

describe('DetalleAsesoria por rol', () => {
  afterEach(() => vi.restoreAllMocks())

  it('el asesor ve el nombre del alumno, nunca su id', () => {
    montar(crearAsesoria(), true)
    expect(screen.getByText('Alumno')).toBeInTheDocument()
    expect(screen.getByText('Beto Alumno')).toBeInTheDocument()
    expect(screen.queryByText(/Alumno #10/)).not.toBeInTheDocument()
  })

  it('el alumno ve el nombre del asesor', () => {
    montar(crearAsesoria(), false)
    expect(screen.getByText('Asesor')).toBeInTheDocument()
    expect(screen.getByText('Ana Asesora')).toBeInTheDocument()
  })

  it('el alumno ve dónde es la sesión', () => {
    montar(crearAsesoria(), false)
    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })

  it('el alumno no ve los botones de marcar asistencia pero sí el de cancelar', () => {
    montar(crearAsesoria(), false)
    expect(screen.queryByRole('button', { name: 'Asistió' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'No asistió' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancelar asesoría' })).toBeInTheDocument()
  })

  it('el alumno no ve la caja de notas de una sesión realizada', () => {
    montar(crearAsesoria({ estado: 'realizada', asistio: true, notas: 'trajo dudas' }), false)
    expect(screen.queryByText('trajo dudas')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Guardar notas' })).not.toBeInTheDocument()
  })

  it('el texto de asistencia es neutral, legible por cualquiera de los dos roles', () => {
    montar(crearAsesoria({ estado: 'realizada', asistio: true }), false)
    expect(screen.getByText('Asistió a la sesión.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/DetalleAsesoria.test.tsx`
Expected: FAIL — el detalle renderiza `Alumno #10` y muestra los botones de asistencia al alumno.

- [ ] **Step 3: Adaptar `DetalleAsesoria.tsx` al rol**

Agregar el import tras la línea 11 (`import { primerMensajeDeError } …`):

```tsx
import { useEsAsesor } from '../../../auth/rol'
```

Dentro de `DetalleAsesoria`, tras `const navigate = useNavigate()`:

```tsx
  const esAsesor = useEsAsesor()
```

Reemplazar la línea 45:

```tsx
  const previas = esAsesor ? sesionesPreviasConNotas(asesorias, asesoria.alumno, asesoria.id) : []
```

Reemplazar el par `<dt>Alumno</dt> / <dd>Alumno #{asesoria.alumno}</dd>` (líneas 61-62):

```tsx
          <dt>{esAsesor ? 'Alumno' : 'Asesor'}</dt>
          <dd>{esAsesor ? asesoria.alumno_nombre : asesoria.asesor_nombre}</dd>
```

Reemplazar la `<section>` de notas previas completa (líneas 84-100) por:

```tsx
      {esAsesor && previas.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-medium text-on-surface">Notas de sesiones anteriores con este alumno</h2>
          <ul className="flex flex-col gap-2">
            {previas.map((previa, indice) => (
              <li key={previa.id} className="entrada-lista rounded-lg bg-surface-container-low p-3 text-sm" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
                <p className="mb-1 text-xs text-on-surface-variant">
                  {FORMATEADOR_FECHA.format(new Date(`${previa.fecha}T00:00:00`))}
                </p>
                <p className="text-on-surface">{previa.notas}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
```

- [ ] **Step 4: Condicionar `SeccionAcciones` por rol**

Dentro de `SeccionAcciones`, tras `const { mensaje, saliendo, mostrar } = useRetroalimentacion()`:

```tsx
  const esAsesor = useEsAsesor()
```

Reemplazar el bloque `if (asesoria.estado === 'realizada')` completo (líneas 126-165) por:

```tsx
  if (asesoria.estado === 'realizada') {
    return (
      <section className="flex flex-col gap-3 rounded-lg bg-surface-container-low p-4">
        <p className="text-sm text-on-surface">{asesoria.asistio ? 'Asistió a la sesión.' : 'No asistió a la sesión.'}</p>
        {esAsesor && puedeGuardarNotas(asesoria) ? (
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
                    onSuccess: () => {
                      setError(null)
                      mostrar('Notas guardadas')
                    },
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
        ) : null}
        <Retroalimentacion mensaje={mensaje} saliendo={saliendo} />
      </section>
    )
  }
```

Reemplazar el bloque `{yaOcurrio ? (…) : (…)}` completo (líneas 171-221) por:

```tsx
      {esAsesor &&
        (yaOcurrio ? (
          <div className="flex flex-col gap-2">
            <p className="text-sm text-on-surface">¿El alumno asistió a esta sesión?</p>
            <div className="flex gap-2">
              <Boton
                type="button"
                cargando={marcarAsistencia.isPending}
                onClick={() =>
                  marcarAsistencia.mutate(
                    { id: asesoria.id, asistio: true },
                    {
                      onSuccess: () => {
                        setError(null)
                        mostrar('Asistencia registrada')
                      },
                      onError: (err) => setError(primerMensajeDeError(err)),
                    },
                  )
                }
                className="flex-1"
              >
                Asistió
              </Boton>
              <Boton
                type="button"
                variante="secundario"
                cargando={marcarAsistencia.isPending}
                onClick={() =>
                  marcarAsistencia.mutate(
                    { id: asesoria.id, asistio: false },
                    {
                      onSuccess: () => {
                        setError(null)
                        mostrar('Asistencia registrada')
                      },
                      onError: (err) => setError(primerMensajeDeError(err)),
                    },
                  )
                }
                className="flex-1"
              >
                No asistió
              </Boton>
            </div>
            {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}
          </div>
        ) : (
          <p className="text-xs text-on-surface-variant">
            Podrás marcar asistencia después de las {FORMATEADOR_HORA.format(new Date(`${asesoria.fecha}T${asesoria.hora_inicio}`))}.
          </p>
        ))}
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/screens/DetalleAsesoria.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/DetalleAsesoria.tsx frontend/src/features/asesorias/screens/DetalleAsesoria.test.tsx
git commit -m "$(cat <<'EOF'
[fix][frontend] mostrar el nombre de la contraparte y adaptar el detalle al rol alumno

- usa alumno_nombre/asesor_nombre en vez de renderizar el id crudo del alumno
- oculta al alumno los controles de asistencia, las notas y las sesiones previas
- el texto de asistencia pasa a wording neutral, legible por ambos roles
- Cancelar asesoría queda visible para ambos: el backend ya lo autoriza

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 8: Toggle editar/lectura de notas y navegación al Historial (B2)

**Files:**
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx` (imports, estado de `SeccionAcciones`, bloque `realizada`, `onSuccess` de "No asistió")
- Test: `frontend/src/features/asesorias/screens/DetalleAsesoria.test.tsx` (agregar describe)

**Interfaces:**
- Consumes: `SeccionAcciones` tal como la deja la Task 7; `Asesorias` acepta `location.state.historialDestacarId` (Task 5); helpers `montar`, `crearAsesoria`, `EspiaAsesorias` del test creado en la Task 7.
- Produces: navegación `navigate('/asesorias', { state: { historialDestacarId: asesoria.id } })`.
- **Depende de:** Tasks 5 y 7.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `frontend/src/features/asesorias/screens/DetalleAsesoria.test.tsx`:

```tsx
describe('DetalleAsesoria: notas y navegación al historial', () => {
  afterEach(() => vi.restoreAllMocks())

  it('sin nota previa arranca en modo edición, sin botón de Editar nota', () => {
    montar(crearAsesoria({ estado: 'realizada', asistio: true, notas: '' }), true)
    expect(screen.getByRole('button', { name: 'Guardar notas' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Editar nota' })).not.toBeInTheDocument()
  })

  it('con nota previa arranca en modo lectura', () => {
    montar(crearAsesoria({ estado: 'realizada', asistio: true, notas: 'trajo dudas del examen' }), true)
    expect(screen.getByText('trajo dudas del examen')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Editar nota' })).toBeInTheDocument()
  })

  it('Editar nota revela el campo con el texto guardado', () => {
    montar(crearAsesoria({ estado: 'realizada', asistio: true, notas: 'trajo dudas del examen' }), true)
    fireEvent.click(screen.getByRole('button', { name: 'Editar nota' }))
    expect(screen.getByLabelText('Nota de la sesión')).toHaveValue('trajo dudas del examen')
  })

  it('al guardar la nota navega a Asesorías con el id a destacar en Historial', () => {
    const { guardarNotas } = montar(
      crearAsesoria({ id: 7, estado: 'realizada', asistio: true, notas: '' }), true,
    )
    fireEvent.change(screen.getByLabelText('Nota de la sesión'), { target: { value: 'repasamos límites' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar notas' }))
    expect(guardarNotas).toHaveBeenCalledWith({ id: 7, texto: 'repasamos límites' }, expect.anything())
    expect(screen.getByTestId('destino')).toHaveTextContent('asesorias:7')
  })

  it('marcar No asistió navega a Asesorías con el id a destacar en Historial', () => {
    montar(crearAsesoria({ id: 7 }), true)
    fireEvent.click(screen.getByRole('button', { name: 'No asistió' }))
    expect(screen.getByTestId('destino')).toHaveTextContent('asesorias:7')
  })

  it('marcar Asistió no navega: el asesor se queda para escribir la nota', () => {
    montar(crearAsesoria({ id: 7 }), true)
    fireEvent.click(screen.getByRole('button', { name: 'Asistió' }))
    expect(screen.queryByTestId('destino')).not.toBeInTheDocument()
  })
})
```

Reemplazar la línea 2 del archivo para importar `fireEvent`:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/features/asesorias/screens/DetalleAsesoria.test.tsx`
Expected: FAIL — no existe el botón "Editar nota", el textarea no tiene label y guardar no navega.

- [ ] **Step 3: Implementar el toggle y la navegación**

En `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`, reemplazar la línea 1:

```tsx
import { useId, useState } from 'react'
```

Reemplazar el bloque de hooks de `SeccionAcciones` (declaraciones de estado) por:

```tsx
function SeccionAcciones({ asesoria }: { asesoria: Asesoria }) {
  const navigate = useNavigate()
  const { mensaje, saliendo, mostrar } = useRetroalimentacion()
  const esAsesor = useEsAsesor()
  const cancelar = useCancelarAsesoria()
  const marcarAsistencia = useMarcarAsistencia()
  const guardarNotas = useGuardarNotas()
  const idNotas = useId()
  const [dialogoCancelarAbierto, setDialogoCancelarAbierto] = useState(false)
  const [notas, setNotas] = useState(asesoria.notas)
  const [editandoNotas, setEditandoNotas] = useState(asesoria.notas.trim() === '')
  const [error, setError] = useState<string | null>(null)
```

Reemplazar el ternario `{esAsesor && puedeGuardarNotas(asesoria) ? (…) : null}` completo por:

```tsx
        {esAsesor && puedeGuardarNotas(asesoria) ? (
          editandoNotas ? (
            <div className="entrada-lista flex flex-col gap-2">
              <label htmlFor={idNotas} className="text-xs font-medium text-on-surface-variant">
                Nota de la sesión
              </label>
              <textarea
                id={idNotas}
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
                rows={4}
                placeholder="Notas de la sesión…"
                className="foco-visible rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
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
            </div>
          ) : (
            <div className="entrada-lista flex flex-col gap-2">
              <p className="text-xs font-medium text-on-surface-variant">Nota de la sesión</p>
              <p className="max-w-prose whitespace-pre-wrap rounded-md bg-surface-container px-3 py-2 text-sm text-on-surface">
                {asesoria.notas}
              </p>
              <Boton
                type="button"
                variante="secundario"
                onClick={() => setEditandoNotas(true)}
                className="w-fit px-6"
              >
                Editar nota
              </Boton>
            </div>
          )
        ) : null}
```

Reemplazar el `onSuccess` del botón "No asistió" (el `marcarAsistencia.mutate` con `asistio: false`):

```tsx
                    {
                      onSuccess: () => navigate('/asesorias', { state: { historialDestacarId: asesoria.id } }),
                      onError: (err) => setError(primerMensajeDeError(err)),
                    },
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/screens/DetalleAsesoria.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/screens/DetalleAsesoria.tsx frontend/src/features/asesorias/screens/DetalleAsesoria.test.tsx
git commit -m "$(cat <<'EOF'
[fix][frontend] separar los estados de lectura y edición de la nota de sesión

- la nota guardada se muestra en lectura con botón Editar nota; sin nota previa
  el campo arranca abierto
- el textarea gana label asociado y foco visible
- guardar la nota y marcar No asistió navegan a Asesorías con el id a destacar
  en Historial; Asistió sigue sin navegar para no cortar el flujo de la nota

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

### Task 9: Logout — `replace: true` y limpieza de la caché de react-query (B5)

**Files:**
- Modify: `frontend/src/components/MenuUsuario.tsx:65-72`
- Modify: `frontend/src/auth/AuthContext.tsx` (import, `useQueryClient`, `logout`)
- Test: `frontend/src/components/MenuUsuario.test.tsx` (ruta espía + test)
- Test: `frontend/src/auth/AuthContext.test.tsx` (wrapper + test)
- Test: `frontend/src/auth/rol.test.tsx` (wrapper)
- Test: `frontend/src/auth/RutaProtegida.test.tsx` (wrapper)

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `AuthProvider` pasa a requerir un `QueryClientProvider` por encima (ya lo tiene en `frontend/src/main.tsx:15-19`); todo test que monte `AuthProvider` debe envolverlo.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/components/MenuUsuario.test.tsx`, agregar `useNavigationType` al import de react-router-dom (línea 3):

```tsx
import { MemoryRouter, Route, Routes, useNavigationType } from 'react-router-dom'
```

Agregar antes de `function montar(...)`:

```tsx
/** Revela si se llegó a la landing con push o con replace. */
function SondaLanding() {
  return (
    <>
      <p>pantalla landing</p>
      <p data-testid="tipo-navegacion">{useNavigationType()}</p>
    </>
  )
}
```

Reemplazar la línea 29 del archivo:

```tsx
        <Route path="/" element={<SondaLanding />} />
```

Agregar dentro del `describe('MenuUsuario', ...)`:

```tsx
  it('reemplaza la entrada del historial al cerrar sesión', async () => {
    montar()
    abrir()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByText('pantalla landing')).toBeInTheDocument()
    expect(screen.getByTestId('tipo-navegacion')).toHaveTextContent('REPLACE')
  })
```

En `frontend/src/auth/AuthContext.test.tsx`, reemplazar el import de la línea 4 y agregar el de react-query:

```tsx
import * as client from '../api/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
```

Agregar tras los imports:

```tsx
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function Proveedores({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
```

Reemplazar **todas** las ocurrencias de `<AuthProvider>` por `<Proveedores>` y de `</AuthProvider>` por `</Proveedores>` en el archivo.

Reemplazar `Sonda` por:

```tsx
function Sonda() {
  const { status, user, roles, loginWithPassword, loginWithGoogle, logout } = useAuth()
  return (
    <>
      <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
      <div data-testid="roles">{roles.join(',') || 'sin-roles'}</div>
      <button type="button" onClick={() => loginWithPassword('a@ciencias.unam.mx', 'x')}>
        Entrar con contraseña
      </button>
      <button type="button" onClick={() => loginWithGoogle()}>
        Entrar con Google
      </button>
      <button type="button" onClick={() => logout()}>
        Cerrar sesión
      </button>
    </>
  )
}
```

Agregar dentro del `describe('AuthProvider', ...)`:

```tsx
  it('logout vacía la caché de react-query, para no filtrar datos entre usuarios', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba())
    vi.spyOn(client, 'apiPost').mockResolvedValue({})
    queryClient.setQueryData(['asesorias'], [{ id: 1 }])

    montar()
    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('authenticated'))

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))

    await waitFor(() => expect(queryClient.getQueryData(['asesorias'])).toBeUndefined())
  })
```

En `frontend/src/auth/rol.test.tsx`, agregar tras los imports:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function Proveedores({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
```

Reemplazar **todas** las ocurrencias de `<AuthProvider>` por `<Proveedores>` y de `</AuthProvider>` por `</Proveedores>` en el archivo.

En `frontend/src/auth/RutaProtegida.test.tsx`, agregar tras los imports:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function Proveedores({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
```

Reemplazar **todas** las ocurrencias de `<AuthProvider>` por `<Proveedores>` y de `</AuthProvider>` por `</Proveedores>` en el archivo.

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx src/auth/AuthContext.test.tsx`
Expected: FAIL — `tipo-navegacion` contiene `PUSH` y `queryClient.getQueryData(['asesorias'])` sigue devolviendo el arreglo.

- [ ] **Step 3: Navegar con `replace` al cerrar sesión**

En `frontend/src/components/MenuUsuario.tsx`, reemplazar la última línea de `cerrarSesion`:

```tsx
    navigate('/', { replace: true })
```

- [ ] **Step 4: Limpiar la caché de react-query en `logout`**

En `frontend/src/auth/AuthContext.tsx`, agregar el import tras la línea 1:

```tsx
import { useQueryClient } from '@tanstack/react-query'
```

Dentro de `AuthProvider`, antes de `const [user, setUser] = useState<AuthUser | null>(null)`:

```tsx
  const queryClient = useQueryClient()
```

Reemplazar la función `logout` por:

```tsx
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

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx src/auth/AuthContext.test.tsx src/auth/rol.test.tsx src/auth/RutaProtegida.test.tsx`
Expected: PASS

- [ ] **Step 6: Correr la suite completa, el build y el lint**

Run (desde `frontend/`): `npm test && npm run build && npm run lint`
Expected: PASS en los tres.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/MenuUsuario.tsx frontend/src/components/MenuUsuario.test.tsx frontend/src/auth/AuthContext.tsx frontend/src/auth/AuthContext.test.tsx frontend/src/auth/rol.test.tsx frontend/src/auth/RutaProtegida.test.tsx
git commit -m "$(cat <<'EOF'
[fix][frontend] cerrar sesión sin dejar pantallas protegidas en el historial

- navigate('/', { replace: true }) al cerrar sesión
- logout() vacía el QueryClient para no mostrar datos del usuario anterior
- los tests que montan AuthProvider ahora lo envuelven en QueryClientProvider

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Self-Review

**1. Spec coverage**

| Requisito del spec | Task |
|---|---|
| B1 backend: `EsAsesorAprobado` + 2 viewsets + tests 403/201 | 1 |
| B1 frontend: `useAsesorActivo` | 2 |
| B1 frontend: `AsesorPendiente.tsx` | 3 |
| B1 frontend: guard en `MisMaterias` / `MiHorario` (sin tocar `soloLectura`) | 4 |
| B1 frontend: ocultar botones + aviso inline en `Asesorias.tsx` | 5 |
| B1 frontend: copy de `SolicitudAsesor.tsx` | 5 |
| B2: toggle editar/lectura, `editandoNotas` inicial | 8 |
| B2: navegar a Historial al guardar nota y al marcar No asistió; Asistió no navega | 8 |
| B2: `Tabs` controlado + `historialDestacarId` + `Historial`/`ListaAsesorias` con `destacarId` | 5 |
| B3: `alumno_nombre`/`asesor_nombre` en el detalle | 7 |
| B4: ruta `/asesorias/:id` bajo `RutaDeAsesorias` | 6 |
| B4: `TarjetaAsesoria` interactiva para el alumno | 6 |
| B4: `DetalleAsesoria` oculta asistencia/notas/previas al alumno, conserva Cancelar | 7 |
| B5: `navigate('/', { replace: true })` | 9 |
| B5: `queryClient.clear()` en `logout()` | 9 |

Sin huecos.

**2. Placeholder scan**

Sin "TBD", "similar a Task N" ni pasos de código sin bloque de código. Los bloques que la Task 7 y la Task 8 tocan en el mismo archivo están escritos completos en ambas tasks.

**3. Type consistency**

- `useAsesorActivo(): boolean` — declarado en Task 2, consumido con el mismo nombre en Tasks 4 y 5.
- `AsesorPendiente({ titulo }: { titulo: string })` — Task 3, invocado con `titulo` en Task 4.
- Clave del router state `historialDestacarId` — leída en Task 5, escrita en Task 8, y verificada por `EspiaAsesorias` en el test de la Task 7/8.
- `Historial({ nombreMateria, destacarId })` y `ListaAsesorias(..., destacarId: number | null)` — mismo nombre en ambos.
- `EsAsesorAprobado` — mismo nombre en `permissions.py`, en el import de `views.py` y en `permission_classes`.
- `esAsesor` se declara una sola vez por función (`DetalleAsesoria` y `SeccionAcciones` por separado; ambas son funciones distintas, no hay sombra).
- `Proveedores` — mismo nombre de wrapper en los tres archivos de test de la Task 9, cada uno con su propia definición local.
