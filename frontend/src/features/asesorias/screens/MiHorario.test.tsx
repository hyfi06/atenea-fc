import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MiHorario } from './MiHorario'
import * as api from '../api'
import * as rol from '../../../auth/rol'
import type { Disponibilidad, RegistroAsesor } from '../../../api/types'

const REGISTRO: RegistroAsesor = { id: 3, semestre: '20262', materias: [1] }

const BLOQUE_LUNES: Disponibilidad = {
  id: 11,
  registro: 3,
  dia_semana: 0,
  hora_inicio: '09:00:00',
  formato: 'presencial',
  ubicacion: 'Salón O-221',
  liga_virtual: '',
  activa: true,
}

function montar({
  disponibilidades = [BLOQUE_LUNES],
  totalSesionesFuturas = 0,
  asesorActivo = true,
}: { disponibilidades?: Disponibilidad[]; totalSesionesFuturas?: number; asesorActivo?: boolean } = {}) {
  vi.spyOn(rol, 'useAsesorActivo').mockReturnValue(asesorActivo)
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: REGISTRO, cargando: false })
  vi.spyOn(api, 'useMisDisponibilidades').mockReturnValue({
    data: disponibilidades,
    isPending: false,
  } as ReturnType<typeof api.useMisDisponibilidades>)
  vi.spyOn(api, 'useSesionesFuturas').mockReturnValue({
    data: { total: totalSesionesFuturas, sesiones: [] },
    isPending: false,
  } as ReturnType<typeof api.useSesionesFuturas>)

  const desactivar = vi.fn()
  const actualizar = vi.fn()
  vi.spyOn(api, 'useDesactivarDisponibilidad').mockReturnValue({
    mutate: desactivar,
    isPending: false,
  } as unknown as ReturnType<typeof api.useDesactivarDisponibilidad>)
  vi.spyOn(api, 'useActualizarDisponibilidad').mockReturnValue({
    mutate: actualizar,
    isPending: false,
  } as unknown as ReturnType<typeof api.useActualizarDisponibilidad>)
  vi.spyOn(api, 'useCrearDisponibilidad').mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof api.useCrearDisponibilidad>)
  vi.spyOn(api, 'useEliminarDisponibilidad').mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof api.useEliminarDisponibilidad>)

  render(
    <MemoryRouter>
      <MiHorario />
    </MemoryRouter>,
  )
  return { desactivar, actualizar }
}

describe('MiHorario', () => {
  beforeEach(() => {
    // Lunes, para que la pestaña por default sea la del bloque de prueba.
    vi.setSystemTime(new Date('2026-08-03T10:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('muestra una pestaña por día y la instrucción fija arriba', () => {
    montar()

    expect(screen.getAllByRole('tab')).toHaveLength(7)
    expect(
      screen.getByText(
        'Cada celda es un horario disponible: toca para activarlo o editarlo. Para cambiar de día, usa las pestañas. Los cambios se autoguardan.',
      ),
    ).toBeInTheDocument()
  })

  it('lista los 28 slots del día seleccionado, sin scroll horizontal', () => {
    montar()

    expect(screen.getAllByRole('button', { name: /^Horario/ })).toHaveLength(28)
  })

  it('un slot activo presencial muestra el salón sin prefijo ni texto de formato repetido', () => {
    montar()

    const slot = screen.getByRole('button', { name: /^Horario 09:00/ })
    expect(within(slot).getByText('Salón O-221')).toBeInTheDocument()
    expect(within(slot).queryByText(/Presencial —/)).not.toBeInTheDocument()
    expect(within(slot).getByText('Activo')).toBeInTheDocument()
  })

  it('desactivar un bloque sin sesiones futuras no pide confirmación extra', () => {
    const { desactivar } = montar({ totalSesionesFuturas: 0 })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }))

    expect(desactivar).toHaveBeenCalledWith(
      { id: 11, cancelarSesiones: false },
      expect.anything(),
    )
  })

  it('con sesiones futuras muestra el modal de 3 acciones antes de desactivar', () => {
    const { desactivar } = montar({ totalSesionesFuturas: 2 })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }))

    expect(desactivar).not.toHaveBeenCalled()
    expect(screen.getByText('Hay 2 sesiones agendadas en este horario.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar esas sesiones y desactivar' }))

    expect(desactivar).toHaveBeenCalledWith({ id: 11, cancelarSesiones: true }, expect.anything())
  })

  it('tocar un bloque inactivo lo reactiva directo, sin diálogo', () => {
    const { actualizar } = montar({ disponibilidades: [{ ...BLOQUE_LUNES, activa: false }] })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))

    expect(actualizar).toHaveBeenCalledWith({ id: 11, activa: true }, expect.anything())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('tocar un slot vacío abre el diálogo de bloque nuevo', () => {
    montar({ disponibilidades: [] })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))

    expect(screen.getByRole('dialog', { name: /Nuevo bloque — Lunes 09:00/ })).toBeInTheDocument()
  })

  function montarSoloLectura(disponibilidades: Disponibilidad[]) {
    vi.spyOn(rol, 'useAsesorActivo').mockReturnValue(true)
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(api, 'useMisDisponibilidades').mockReturnValue({
      data: [], isPending: false,
    } as ReturnType<typeof api.useMisDisponibilidades>)
    vi.spyOn(api, 'useSesionesFuturas').mockReturnValue({
      data: { total: 0, sesiones: [] }, isPending: false,
    } as ReturnType<typeof api.useSesionesFuturas>)
    vi.spyOn(api, 'useDesactivarDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useDesactivarDisponibilidad>)
    vi.spyOn(api, 'useActualizarDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useActualizarDisponibilidad>)
    vi.spyOn(api, 'useCrearDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useCrearDisponibilidad>)
    vi.spyOn(api, 'useEliminarDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useEliminarDisponibilidad>)

    render(
      <MemoryRouter>
        <MiHorario soloLectura disponibilidades={disponibilidades} />
      </MemoryRouter>,
    )
  }

  it('en solo lectura pinta los bloques recibidos y conserva los 7 días', () => {
    montarSoloLectura([BLOQUE_LUNES])

    expect(screen.getAllByRole('tab')).toHaveLength(7)
    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })

  it('en solo lectura las celdas no son interactivas ni abren diálogos', () => {
    montarSoloLectura([BLOQUE_LUNES])

    expect(screen.queryAllByRole('button', { name: /^Horario/ })).toHaveLength(0)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('en solo lectura no muestra chips de estado Activo/Inactivo', () => {
    montarSoloLectura([BLOQUE_LUNES])

    expect(screen.queryByText('Inactivo')).not.toBeInTheDocument()
    expect(screen.queryByText('Activo')).not.toBeInTheDocument()
  })

  it('en solo lectura un bloque presencial activo conserva su ubicación', () => {
    montarSoloLectura([BLOQUE_LUNES])

    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })

  it('en solo lectura un día sin disponibilidad activa muestra el texto vacío', () => {
    montarSoloLectura([])

    expect(screen.getByText('Sin disponibilidad este día')).toBeInTheDocument()
  })

  it('en solo lectura oculta las disponibilidades inactivas', () => {
    montarSoloLectura([{ ...BLOQUE_LUNES, activa: false }])

    expect(screen.queryByText('Salón O-221')).not.toBeInTheDocument()
    expect(screen.getByText('Sin disponibilidad este día')).toBeInTheDocument()
  })

  it('el asesor pendiente de aprobación ve el aviso en vez de la rejilla', () => {
    montar({ asesorActivo: false })
    expect(screen.getByText(/pendiente de que la SAE confirme tu nombramiento/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Mi horario' })).toBeInTheDocument()
  })
})
