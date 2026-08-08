import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoDesactivarConSesiones } from './DialogoDesactivarConSesiones'

function montar(total: number) {
  const onSoloNuevas = vi.fn()
  const onCancelarYDesactivar = vi.fn()
  render(
    <DialogoDesactivarConSesiones
      abierto
      total={total}
      cargando={false}
      error={null}
      onSoloNuevas={onSoloNuevas}
      onCancelarYDesactivar={onCancelarYDesactivar}
      onCerrar={vi.fn()}
    />,
  )
  return { onSoloNuevas, onCancelarYDesactivar }
}

describe('DialogoDesactivarConSesiones', () => {
  it('ordena las 3 acciones como fija la convención del paso 3', () => {
    montar(2)

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'Solo dejar de recibir nuevas',
      'Cancelar esas sesiones y desactivar',
      'Volver',
    ])
  })

  it('la opción destructiva no va rellena', () => {
    montar(2)

    expect(screen.getByRole('button', { name: 'Cancelar esas sesiones y desactivar' })).toHaveClass(
      'bg-transparent',
    )
  })

  it('concuerda el número con el texto', () => {
    montar(1)
    expect(screen.getByText('Hay 1 sesión agendada en este horario.')).toBeInTheDocument()
  })

  it('concuerda el plural', () => {
    montar(3)
    expect(screen.getByText('Hay 3 sesiones agendadas en este horario.')).toBeInTheDocument()
  })

  it('cada opción llama a su callback', () => {
    const { onSoloNuevas, onCancelarYDesactivar } = montar(2)

    fireEvent.click(screen.getByRole('button', { name: 'Solo dejar de recibir nuevas' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar esas sesiones y desactivar' }))

    expect(onSoloNuevas).toHaveBeenCalledTimes(1)
    expect(onCancelarYDesactivar).toHaveBeenCalledTimes(1)
  })
})
