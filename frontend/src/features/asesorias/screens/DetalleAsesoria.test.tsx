import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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
    <MemoryRouter initialEntries={[`/asesorias/${asesoria.id}`]}>
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

  it('el alumno no crashea cuando el backend omite notas (payload real, no notas: "")', () => {
    const asesoria = crearAsesoria()
    delete (asesoria as Partial<Asesoria>).notas
    montar(asesoria, false)
    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })
})

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
