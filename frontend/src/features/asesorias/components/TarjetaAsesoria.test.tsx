import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TarjetaAsesoria } from './TarjetaAsesoria'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

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

  it('para el alumno muestra el nombre del asesor y no navega', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.getByText(/Ana Asesora/)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('para el asesor muestra el nombre del alumno en un botón', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(true)
    render(<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.getByText(/Beto Alumno/)).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('nunca renderiza las notas', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(<TarjetaAsesoria asesoria={crearAsesoria({ notas: 'texto privado' })} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.queryByText(/texto privado/)).not.toBeInTheDocument()
  })
})
