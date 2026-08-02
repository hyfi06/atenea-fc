import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SesionesAsesor } from './SesionesAsesor'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { Asesoria } from '../../../api/types'

function crearAsesoria(overrides: Partial<Asesoria>): Asesoria {
  return {
    id: 1, alumno: 10, disponibilidad: 1, materia: 1, carrera: 1,
    fecha: '2026-08-03', hora_inicio: '10:00:00', formato: 'virtual',
    ubicacion: '', liga_virtual: '', estado: 'agendada', asistio: null,
    notas: '', creado_en: '2026-08-01T10:00:00Z', ...overrides,
  }
}

function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('SesionesAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('la tab Próximas muestra solo agendadas por default', () => {
    vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
      data: [
        crearAsesoria({ id: 1, estado: 'agendada' }),
        crearAsesoria({ id: 2, estado: 'realizada' }),
      ],
      isPending: false,
    } as ReturnType<typeof api.useMisAsesorias>)
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]))

    render(<SesionesAsesor />, { wrapper: envolver })

    expect(screen.getAllByText('Cálculo I')).toHaveLength(1)
  })
})
