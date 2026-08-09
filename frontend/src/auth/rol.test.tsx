import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider } from './AuthContext'
import { useEsAlumno, useEsAsesor } from './rol'
import * as client from '../api/client'
import { usuarioDePrueba } from '../test/factories'
import type { AuthUser } from '../api/types'

function Sonda() {
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  return <div data-testid="rol">{`asesor=${esAsesor} alumno=${esAlumno}`}</div>
}

function montarCon(usuario: AuthUser) {
  vi.spyOn(client, 'apiGet').mockResolvedValue(usuario)
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
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
          carrera: 5,
          carrera_nombre: 'Actuaría',
          generacion: 2023,
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
      <AuthProvider>
        <Sonda />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true'))
    expect(apiGet).toHaveBeenCalledTimes(1)
    expect(apiGet).toHaveBeenCalledWith('/api/auth/user/')
  })
})
