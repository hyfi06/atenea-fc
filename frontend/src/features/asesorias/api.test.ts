import { describe, it, expect } from 'vitest'
import { rutaAdminAsesorias, rutaBuscarAsesores } from './api'

describe('rutaAdminAsesorias', () => {
  it('sin filtros pide el listado por defecto (próximas agendadas)', () => {
    expect(rutaAdminAsesorias()).toBe('/api/asesorias/admin/asesorias/')
  })

  it('traduce el filtro de asesor a ?asesor=', () => {
    expect(rutaAdminAsesorias({ asesor: 7 })).toBe('/api/asesorias/admin/asesorias/?asesor=7')
  })

  it('traduce el filtro de alumno a ?alumno=', () => {
    expect(rutaAdminAsesorias({ alumno: 15 })).toBe('/api/asesorias/admin/asesorias/?alumno=15')
  })

  it('traduce el semestre a ?semestre=', () => {
    expect(rutaAdminAsesorias({ semestre: '20262' })).toBe('/api/asesorias/admin/asesorias/?semestre=20262')
  })

  it('traduce el estado a ?estado=', () => {
    expect(rutaAdminAsesorias({ estado: 'cancelada' })).toBe('/api/asesorias/admin/asesorias/?estado=cancelada')
  })

  it('combina filtros y omite los nulos', () => {
    expect(rutaAdminAsesorias({ asesor: 7, alumno: null, semestre: '20261' })).toBe(
      '/api/asesorias/admin/asesorias/?asesor=7&semestre=20261',
    )
  })
})

describe('rutaBuscarAsesores', () => {
  it('manda el término en ?buscar=', () => {
    expect(rutaBuscarAsesores('ana')).toBe('/api/asesorias/admin/asesores/?buscar=ana')
  })

  it('escapa los caracteres del término', () => {
    expect(rutaBuscarAsesores('ana lópez')).toBe(
      '/api/asesorias/admin/asesores/?buscar=ana%20l%C3%B3pez',
    )
  })
})
