import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoBloqueActivo } from './DialogoBloqueActivo'
import type { Disponibilidad } from '../../../api/types'

const BLOQUE: Disponibilidad = {
  id: 1,
  registro: 1,
  dia_semana: 0,
  hora_inicio: '09:00:00',
  formato: 'virtual',
  ubicacion: '',
  liga_virtual: 'https://meet.example/x',
  activa: true,
}

function montar() {
  const onDesactivar = vi.fn()
  const onEliminar = vi.fn()
  const onCerrar = vi.fn()
  render(
    <DialogoBloqueActivo
      abierto
      disponibilidad={BLOQUE}
      cargando={false}
      onDesactivar={onDesactivar}
      onEliminar={onEliminar}
      onCerrar={onCerrar}
    />,
  )
  return { onDesactivar, onEliminar, onCerrar }
}

describe('DialogoBloqueActivo', () => {
  it('presenta las 3 acciones en el orden de la convención', () => {
    montar()

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'Desactivar',
      'Eliminar',
      'Volver',
    ])
  })

  it('la acción destructiva va en contorno, no rellena', () => {
    montar()

    expect(screen.getByRole('button', { name: 'Eliminar' })).toHaveClass('bg-transparent')
  })

  it('cada botón dispara su callback', () => {
    const { onDesactivar, onEliminar, onCerrar } = montar()

    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Volver' }))

    expect(onDesactivar).toHaveBeenCalledTimes(1)
    expect(onEliminar).toHaveBeenCalledTimes(1)
    expect(onCerrar).toHaveBeenCalledTimes(1)
  })

  it('no renderiza nada sin disponibilidad', () => {
    render(
      <DialogoBloqueActivo
        abierto
        disponibilidad={null}
        cargando={false}
        onDesactivar={vi.fn()}
        onEliminar={vi.fn()}
        onCerrar={vi.fn()}
      />,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
