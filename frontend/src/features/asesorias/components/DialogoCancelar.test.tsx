import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoCancelar } from './DialogoCancelar'

describe('DialogoCancelar', () => {
  it('confirma con el motivo que escribió el asesor', () => {
    const onConfirmar = vi.fn()
    render(
      <DialogoCancelar abierto cargando={false} error={null} onConfirmar={onConfirmar} onCerrar={vi.fn()} />,
    )

    fireEvent.change(screen.getByLabelText(/Motivo/), { target: { value: 'Junta académica.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar cancelación' }))

    expect(onConfirmar).toHaveBeenCalledWith('Junta académica.')
  })

  it('sigue la convención de 2 acciones: salir a la izquierda', () => {
    render(<DialogoCancelar abierto cargando={false} error={null} onConfirmar={vi.fn()} onCerrar={vi.fn()} />)

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'Volver',
      'Confirmar cancelación',
    ])
  })

  it('muestra el error del backend como alerta', () => {
    render(
      <DialogoCancelar
        abierto
        cargando={false}
        error="No se pudo cancelar."
        onConfirmar={vi.fn()}
        onCerrar={vi.fn()}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo cancelar.')
  })
})
