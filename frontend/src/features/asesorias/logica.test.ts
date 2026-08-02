import { describe, it, expect } from 'vitest'
import { semestreActual, claveSlot, mapaDisponibilidades, proximas, historial, sesionesPreviasConNotas, sesionYaOcurrio, puedeGuardarNotas } from './logica'
import type { Disponibilidad, Asesoria } from '../../api/types'

describe('semestreActual', () => {
  it('devuelve año+1 para meses de enero a junio', () => {
    expect(semestreActual(new Date('2026-03-15'))).toBe('20261')
  })

  it('devuelve año+2 para meses de julio a diciembre', () => {
    expect(semestreActual(new Date('2026-08-01'))).toBe('20262')
  })
})

describe('claveSlot', () => {
  it('combina día y hora en una clave estable', () => {
    expect(claveSlot(0, '09:00:00')).toBe('0-09:00:00')
  })
})

describe('mapaDisponibilidades', () => {
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

  it('indexa solo las disponibilidades activas por día+hora', () => {
    const mapa = mapaDisponibilidades([base, { ...base, id: 2, activa: false, dia_semana: 1 }])
    expect(mapa.size).toBe(1)
    expect(mapa.get('0-09:00:00')).toEqual(base)
    expect(mapa.get('1-09:00:00')).toBeUndefined()
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
