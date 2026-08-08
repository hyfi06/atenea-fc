import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoAgregarMateria } from './DialogoAgregarMateria'
import * as catalogo from '../../catalogo/api'
import type { Materia } from '../../../api/types'

function crearMateria(overrides: Partial<Materia>): Materia {
  return {
    id: 1, clave: '0001', nombre: 'Cálculo I', carrera: 1, nivel: null,
    plan: 1, habilitada_asesorias: true, ...overrides,
  }
}

function montar(materias: Materia[]) {
  vi.spyOn(catalogo, 'useMaterias').mockReturnValue({
    data: materias,
  } as ReturnType<typeof catalogo.useMaterias>)
  const onConfirmar = vi.fn()
  render(
    <DialogoAgregarMateria abierto cargando={false} error={null} onConfirmar={onConfirmar} onCerrar={vi.fn()} />,
  )
  return onConfirmar
}

describe('DialogoAgregarMateria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('oculta las materias no habilitadas para asesorías', () => {
    montar([
      crearMateria({ id: 1, nombre: 'Cálculo I' }),
      crearMateria({ id: 2, nombre: 'Álgebra', habilitada_asesorias: false }),
    ])

    expect(screen.getByRole('button', { name: 'Cálculo I' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Álgebra' })).not.toBeInTheDocument()
  })

  it('filtra por la búsqueda sin distinguir mayúsculas', () => {
    montar([crearMateria({ id: 1, nombre: 'Cálculo I' }), crearMateria({ id: 2, nombre: 'Física' })])

    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'fís' } })

    expect(screen.getByRole('button', { name: 'Física' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cálculo I' })).not.toBeInTheDocument()
  })

  it('mantiene Agregar deshabilitado hasta que hay una materia seleccionada', () => {
    const onConfirmar = montar([crearMateria({ id: 7, nombre: 'Física' })])

    expect(screen.getByRole('button', { name: 'Agregar' })).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Física' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }))

    expect(onConfirmar).toHaveBeenCalledWith(7)
  })
})
