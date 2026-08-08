import { describe, it, expect } from 'vitest'
import { ApiError } from './client'
import { primerMensajeDeError } from './errores'

describe('primerMensajeDeError', () => {
  it('toma el primer elemento cuando detail es una lista', () => {
    const error = new ApiError(400, { detail: ['Ya tienes un bloque en ese horario.', 'Otro.'] })
    expect(primerMensajeDeError(error)).toBe('Ya tienes un bloque en ese horario.')
  })

  it('acepta detail como cadena', () => {
    expect(primerMensajeDeError(new ApiError(403, { detail: 'No autorizado.' }))).toBe('No autorizado.')
  })

  it('cae a un mensaje genérico con un cuerpo desconocido', () => {
    expect(primerMensajeDeError(new ApiError(500, null))).toBe('Ocurrió un error inesperado.')
  })

  it('cae a un mensaje genérico con algo que no es un ApiError', () => {
    expect(primerMensajeDeError(new Error('boom'))).toBe('Ocurrió un error inesperado.')
  })
})
