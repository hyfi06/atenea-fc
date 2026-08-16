import { describe, it, expect } from 'vitest'
import { semestreActual, claveSlot, proximas, historial, sesionesPreviasConNotas, sesionYaOcurrio, puedeGuardarNotas, horasDelDia, slotsDelDia, diaSemanaHoy, agruparPorDia } from './logica'
import type { Disponibilidad, Asesoria, SlotDisponibilidad, AsesoriaAdmin } from '../../api/types'

describe('semestreActual', () => {
  // Convención UNAM: el semestre AAAA-1 arranca en agosto del año anterior.
  // Agosto 2026 ya es el semestre 2027-1; marzo 2027 es el 2027-2.
  it('julio a diciembre pertenece al semestre 1 del año siguiente', () => {
    expect(semestreActual(new Date('2026-08-01T12:00:00'))).toBe('20271')
    expect(semestreActual(new Date('2026-12-31T12:00:00'))).toBe('20271')
  })

  it('enero a junio pertenece al semestre 2 del año en curso', () => {
    expect(semestreActual(new Date('2027-01-15T12:00:00'))).toBe('20272')
    expect(semestreActual(new Date('2027-06-30T12:00:00'))).toBe('20272')
  })
})

describe('claveSlot', () => {
  it('combina día y hora en una clave estable', () => {
    expect(claveSlot(0, '09:00:00')).toBe('0-09:00:00')
  })
})

function crearAsesoria(overrides: Partial<Asesoria>): Asesoria {
  return {
    id: 1,
    alumno: 10,
    disponibilidad: 1,
    materia: 1,
    carrera: 1,
    fecha: '2026-08-03',
    hora_inicio: '10:00:00',
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: 'https://meet.example/x',
    estado: 'agendada',
    asistio: null,
    notas: '',
    creado_en: '2026-08-01T10:00:00Z',
    ...overrides,
  }
}

describe('proximas', () => {
  it('incluye solo agendadas, ordenadas por fecha ascendente', () => {
    const a = crearAsesoria({ id: 1, fecha: '2026-08-10', estado: 'agendada' })
    const b = crearAsesoria({ id: 2, fecha: '2026-08-03', estado: 'agendada' })
    const c = crearAsesoria({ id: 3, fecha: '2026-08-01', estado: 'realizada' })
    expect(proximas([a, b, c]).map((x) => x.id)).toEqual([2, 1])
  })
})

describe('historial', () => {
  it('incluye realizadas y canceladas, ordenadas por fecha descendente', () => {
    const a = crearAsesoria({ id: 1, fecha: '2026-07-01', estado: 'realizada' })
    const b = crearAsesoria({ id: 2, fecha: '2026-07-15', estado: 'cancelada' })
    const c = crearAsesoria({ id: 3, fecha: '2026-08-01', estado: 'agendada' })
    expect(historial([a, b, c]).map((x) => x.id)).toEqual([2, 1])
  })
})

describe('sesionesPreviasConNotas', () => {
  it('filtra por mismo alumno, excluye la actual, solo realizadas con notas', () => {
    const actual = crearAsesoria({ id: 1, alumno: 10, estado: 'agendada' })
    const previaConNotas = crearAsesoria({ id: 2, alumno: 10, estado: 'realizada', notas: 'Le costó factorizar', fecha: '2026-07-01' })
    const previaSinNotas = crearAsesoria({ id: 3, alumno: 10, estado: 'realizada', notas: '', fecha: '2026-07-08' })
    const otroAlumno = crearAsesoria({ id: 4, alumno: 99, estado: 'realizada', notas: 'otra cosa', fecha: '2026-07-10' })
    const resultado = sesionesPreviasConNotas([actual, previaConNotas, previaSinNotas, otroAlumno], 10, 1)
    expect(resultado.map((x) => x.id)).toEqual([2])
  })
})

describe('sesionYaOcurrio', () => {
  it('es true si la fecha+hora de inicio ya pasó', () => {
    const asesoria = { fecha: '2026-08-01', hora_inicio: '10:00:00' }
    expect(sesionYaOcurrio(asesoria, new Date('2026-08-01T11:00:00'))).toBe(true)
    expect(sesionYaOcurrio(asesoria, new Date('2026-08-01T09:00:00'))).toBe(false)
  })
})

describe('puedeGuardarNotas', () => {
  it('solo es true si la sesión está realizada y hubo asistencia', () => {
    expect(puedeGuardarNotas({ estado: 'realizada', asistio: true })).toBe(true)
    expect(puedeGuardarNotas({ estado: 'realizada', asistio: false })).toBe(false)
    expect(puedeGuardarNotas({ estado: 'agendada', asistio: null })).toBe(false)
  })
})

describe('horasDelDia', () => {
  it('produce los 28 slots de media hora de 07:00 a 20:30', () => {
    const horas = horasDelDia()
    expect(horas).toHaveLength(28)
    expect(horas[0]).toBe('07:00:00')
    expect(horas[1]).toBe('07:30:00')
    expect(horas.at(-1)).toBe('20:30:00')
  })
})

describe('slotsDelDia', () => {
  const base: Disponibilidad = {
    id: 1,
    registro: 1,
    dia_semana: 0,
    hora_inicio: '09:00:00',
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: 'https://meet.example/x',
    activa: true,
  }

  it('devuelve un slot por cada media hora del día', () => {
    expect(slotsDelDia(0, [])).toHaveLength(28)
  })

  it('marca activo el slot con una disponibilidad activa de ese día', () => {
    const slots = slotsDelDia(0, [base])
    const slot = slots.find((s) => s.hora === '09:00:00')

    expect(slot?.activo).toBe(true)
    expect(slot?.disponibilidad).toEqual(base)
  })

  it('un bloque inactivo se reporta como no activo pero conserva su disponibilidad', () => {
    const slots = slotsDelDia(0, [{ ...base, activa: false }])
    const slot = slots.find((s) => s.hora === '09:00:00')

    expect(slot?.activo).toBe(false)
    expect(slot?.disponibilidad?.id).toBe(1)
  })

  it('ignora las disponibilidades de otros días', () => {
    const slots = slotsDelDia(1, [base])

    expect(slots.every((s) => s.disponibilidad === null)).toBe(true)
  })
})

describe('diaSemanaHoy', () => {
  it('traduce el domingo de JavaScript (0) al índice 6 del proyecto', () => {
    expect(diaSemanaHoy(new Date('2026-08-02T10:00:00'))).toBe(6)
  })

  it('traduce el lunes al índice 0', () => {
    expect(diaSemanaHoy(new Date('2026-08-03T10:00:00'))).toBe(0)
  })
})

function slot(overrides: Partial<SlotDisponibilidad>): SlotDisponibilidad {
  return {
    registro_id: 7, asesor_nombre: 'Ana', disponibilidad_id: 1,
    fecha: '2026-08-10', hora_inicio: '10:00:00', hora_fin: '10:30:00',
    formato: 'virtual', ubicacion: '', liga_virtual: 'https://x', ...overrides,
  }
}

describe('agruparPorDia', () => {
  it('agrupa slots por fecha', () => {
    const dias = agruparPorDia([
      slot({ disponibilidad_id: 1, fecha: '2026-08-10' }),
      slot({ disponibilidad_id: 2, fecha: '2026-08-10', hora_inicio: '11:00:00' }),
      slot({ disponibilidad_id: 3, fecha: '2026-08-11' }),
    ])
    expect(dias.map((d) => d.fecha)).toEqual(['2026-08-10', '2026-08-11'])
    expect(dias[0].slots).toHaveLength(2)
    expect(dias[1].slots).toHaveLength(1)
  })

  it('ordena los días por fecha ascendente', () => {
    const dias = agruparPorDia([
      slot({ fecha: '2026-08-12' }),
      slot({ fecha: '2026-08-10' }),
    ])
    expect(dias.map((d) => d.fecha)).toEqual(['2026-08-10', '2026-08-12'])
  })

  it('ordena los slots de cada día por hora_inicio', () => {
    const [dia] = agruparPorDia([
      slot({ disponibilidad_id: 1, hora_inicio: '12:00:00' }),
      slot({ disponibilidad_id: 2, hora_inicio: '09:00:00' }),
    ])
    expect(dia.slots.map((s) => s.hora_inicio)).toEqual(['09:00:00', '12:00:00'])
  })

  it('devuelve lista vacía sin slots', () => {
    expect(agruparPorDia([])).toEqual([])
  })
})

function crearAsesoriaAdmin(overrides: Partial<AsesoriaAdmin> = {}): AsesoriaAdmin {
  return {
    id: 1,
    estado: 'agendada',
    fecha: '2026-08-03',
    hora_inicio: '10:00:00',
    materia: 1,
    carrera: 1,
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: '',
    alumno_nombre: 'Beto Alumno',
    asesor_nombre: 'Ana Asesora',
    asistio: null,
    notas: '',
    ...overrides,
  }
}

describe('proximas / historial sobre la forma admin', () => {
  it('acepta AsesoriaAdmin y separa agendadas de no agendadas', () => {
    const lista = [
      crearAsesoriaAdmin({ id: 1, estado: 'realizada', fecha: '2026-07-01' }),
      crearAsesoriaAdmin({ id: 2, estado: 'agendada', fecha: '2026-08-20' }),
      crearAsesoriaAdmin({ id: 3, estado: 'cancelada', fecha: '2026-07-15' }),
    ]

    expect(proximas(lista).map((a) => a.id)).toEqual([2])
    expect(historial(lista).map((a) => a.id)).toEqual([3, 1])
  })

  it('conserva los campos exclusivos de la forma admin', () => {
    const [primera] = proximas([crearAsesoriaAdmin({ notas: 'llegó tarde' })])
    expect(primera.notas).toBe('llegó tarde')
    expect(primera.asesor_nombre).toBe('Ana Asesora')
  })
})
