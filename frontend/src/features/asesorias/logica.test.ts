import { describe, it, expect } from 'vitest'
import { semestreActual, claveSlot, mapaDisponibilidades } from './logica'
import type { Disponibilidad } from '../../api/types'

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
