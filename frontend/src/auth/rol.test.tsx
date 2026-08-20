import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider } from './AuthContext'
import { useEsAlumno, useEsAsesor, useEsMiembroSAE, useEsAcademico, useAsesorActivo } from './rol'
import * as client from '../api/client'
import { usuarioDePrueba, usuarioSAE } from '../test/factories'
import type { AuthUser } from '../api/types'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function Proveedores({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

function Sonda() {
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  return <div data-testid="rol">{`asesor=${esAsesor} alumno=${esAlumno}`}</div>
}

function montarCon(usuario: AuthUser) {
  vi.spyOn(client, 'apiGet').mockResolvedValue(usuario)
  render(
    <Proveedores>
      <Sonda />
    </Proveedores>,
  )
}

describe('hooks de rol', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reconoce al asesor académico por el rol que viene del contexto', async () => {
    montarCon(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: true },
      }),
    )

    await waitFor(() => {
      expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true alumno=false')
    })
  })

  it('reconoce al alumno', async () => {
    montarCon(
      usuarioDePrueba({
        roles: ['alumno'],
        perfil_alumno: {
          id: 4,
          numero_cuenta: '312345678',
          historial: [{ carrera: 5, carrera_nombre: 'Actuaría', generacion: 2023 }],
        },
      }),
    )

    await waitFor(() => {
      expect(screen.getByTestId('rol')).toHaveTextContent('asesor=false alumno=true')
    })
  })

  it('un asesor con el perfil inactivo sigue contando como asesor', async () => {
    // Mismo criterio que la permission class EsAsesorAcademico del backend,
    // que solo comprueba que el perfil exista. Divergir haría que la UI
    // escondiera una pantalla a la que el backend sí da acceso.
    montarCon(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: false },
      }),
    )

    await waitFor(() => {
      expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true')
    })
  })

  it('no consulta ningún endpoint de asesorías para averiguar el rol', async () => {
    const apiGet = vi
      .spyOn(client, 'apiGet')
      .mockResolvedValue(usuarioDePrueba({ roles: ['asesor_academico'] }))

    render(
      <Proveedores>
        <Sonda />
      </Proveedores>,
    )

    await waitFor(() => expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true'))
    expect(apiGet).toHaveBeenCalledTimes(1)
    expect(apiGet).toHaveBeenCalledWith('/api/auth/user/')
  })
})

function SondaSAE() {
  const esSAE = useEsMiembroSAE()
  return <div data-testid="sae">{`sae=${esSAE}`}</div>
}

describe('useEsMiembroSAE', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reconoce al miembro de la SAE por el rol del contexto', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioSAE())
    render(
      <Proveedores>
        <SondaSAE />
      </Proveedores>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('sae')).toHaveTextContent('sae=true')
    })
  })

  it('no reconoce como SAE a quien no tiene el rol', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    render(
      <Proveedores>
        <SondaSAE />
      </Proveedores>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('sae')).toHaveTextContent('sae=false')
    })
  })
})

function SondaAcademico() {
  const esAcademico = useEsAcademico()
  return <div data-testid="academico">{`academico=${esAcademico}`}</div>
}

describe('useEsAcademico', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reconoce al académico sin perfil de asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico'],
        perfil_academico: { id: 7, numero_trabajador: '70001' },
      }),
    )
    render(
      <Proveedores>
        <SondaAcademico />
      </Proveedores>,
    )
    await waitFor(() => expect(screen.getByTestId('academico')).toHaveTextContent('academico=true'))
  })

  it('no reconoce como académico a un alumno', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    render(
      <Proveedores>
        <SondaAcademico />
      </Proveedores>,
    )
    await waitFor(() => expect(screen.getByTestId('academico')).toHaveTextContent('academico=false'))
  })
})

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
      <Proveedores>
        <SondaAsesorActivo />
      </Proveedores>,
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
      <Proveedores>
        <SondaAsesorActivo />
      </Proveedores>,
    )
    await waitFor(() => expect(screen.getByTestId('activo')).toHaveTextContent('activo=false'))
  })

  it('es false para quien no tiene perfil de asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    render(
      <Proveedores>
        <SondaAsesorActivo />
      </Proveedores>,
    )
    await waitFor(() => expect(screen.getByTestId('activo')).toHaveTextContent('activo=false'))
  })
})
