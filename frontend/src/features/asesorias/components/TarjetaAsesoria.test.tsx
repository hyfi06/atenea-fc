import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { TarjetaAsesoria } from './TarjetaAsesoria'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

/** Ruta de destino de mentira: verifica a la vez que la navegación ocurrió y
 *  qué llegó en el router state. */
function EspiaDeEstado() {
  const { state } = useLocation() as { state: { asesoria?: Asesoria; nombreMateria?: string } | null }
  return (
    <div>
      <p>detalle SAE</p>
      <p data-testid="materia-en-estado">{state?.nombreMateria ?? ''}</p>
      <p data-testid="notas-en-estado">{state?.asesoria?.notas ?? ''}</p>
    </div>
  )
}

function crearAsesoria(overrides: Partial<Asesoria> = {}): Asesoria {
  return {
    id: 1, alumno: 10, alumno_nombre: 'Beto Alumno', asesor_nombre: 'Ana Asesora',
    disponibilidad: 1, materia: 1, carrera: 1, fecha: '2026-08-03', hora_inicio: '10:00:00',
    formato: 'virtual', ubicacion: '', liga_virtual: '', estado: 'agendada', asistio: null,
    notas: '', creado_en: '2026-08-01T10:00:00Z', ...overrides,
  }
}

describe('TarjetaAsesoria', () => {
  afterEach(() => vi.restoreAllMocks())

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

  it('para el asesor muestra el nombre del alumno en un botón', () => {
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(true)
    render(<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.getByText(/Beto Alumno/)).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('nunca renderiza las notas', () => {
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(<TarjetaAsesoria asesoria={crearAsesoria({ notas: 'texto privado' })} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.queryByText(/texto privado/)).not.toBeInTheDocument()
  })

  it('en modo admin muestra ambos nombres y tampoco las notas', () => {
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <TarjetaAsesoria
        asesoria={crearAsesoria({ notas: 'el alumno llegó tarde' })}
        nombreMateria="Cálculo I"
        indice={0}
        admin
      />,
      { wrapper: MemoryRouter },
    )
    expect(screen.getByText(/Beto Alumno · Ana Asesora/)).toBeInTheDocument()
    expect(screen.queryByText(/el alumno llegó tarde/)).not.toBeInTheDocument()
  })

  it('en modo admin es interactiva aunque quien mire no sea asesor', () => {
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} admin />,
      { wrapper: MemoryRouter },
    )
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('en modo admin navega al detalle SAE y no al del asesor', () => {
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(true)
    render(
      <MemoryRouter initialEntries={['/sae/asesorias']}>
        <Routes>
          <Route
            path="/sae/asesorias"
            element={
              <TarjetaAsesoria
                asesoria={crearAsesoria({ notas: 'trae dudas' })}
                nombreMateria="Cálculo I"
                indice={0}
                admin
              />
            }
          />
          <Route path="/sae/asesorias/1" element={<EspiaDeEstado />} />
          <Route path="/asesorias/1" element={<p>detalle del asesor</p>} />
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('detalle SAE')).toBeInTheDocument()
  })

  it('en modo admin lleva la sesión y la materia en el router state', () => {
    vi.spyOn(rol, 'useEsAlumno').mockReturnValue(false)
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <MemoryRouter initialEntries={['/sae/asesorias']}>
        <Routes>
          <Route
            path="/sae/asesorias"
            element={
              <TarjetaAsesoria
                asesoria={crearAsesoria({ notas: 'trae dudas' })}
                nombreMateria="Cálculo I"
                indice={0}
                admin
              />
            }
          />
          <Route path="/sae/asesorias/1" element={<EspiaDeEstado />} />
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByTestId('materia-en-estado')).toHaveTextContent('Cálculo I')
    expect(screen.getByTestId('notas-en-estado')).toHaveTextContent('trae dudas')
  })
})
