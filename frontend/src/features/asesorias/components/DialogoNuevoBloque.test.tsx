import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoNuevoBloque } from './DialogoNuevoBloque'

function montar() {
  const onConfirmar = vi.fn()
  render(
    <DialogoNuevoBloque
      abierto
      diaSemana={0}
      horaInicio="09:00:00"
      nombreDia="Lunes"
      cargando={false}
      error={null}
      onConfirmar={onConfirmar}
      onCerrar={vi.fn()}
    />,
  )
  return onConfirmar
}

describe('DialogoNuevoBloque', () => {
  it('pide la liga cuando el formato es virtual y la ubicación cuando es presencial', () => {
    montar()

    expect(screen.getByLabelText('Liga de la sesión')).toBeInTheDocument()
    expect(screen.queryByLabelText('Ubicación')).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Formato'), { target: { value: 'presencial' } })

    expect(screen.getByLabelText('Ubicación')).toBeInTheDocument()
    expect(screen.queryByLabelText('Liga de la sesión')).not.toBeInTheDocument()
  })

  it('confirma con el formato y los datos capturados', () => {
    const onConfirmar = montar()

    fireEvent.change(screen.getByLabelText('Formato'), { target: { value: 'presencial' } })
    fireEvent.change(screen.getByLabelText('Ubicación'), { target: { value: 'Salón O-221' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear' }))

    expect(onConfirmar).toHaveBeenCalledWith({
      formato: 'presencial',
      ubicacion: 'Salón O-221',
      liga_virtual: '',
    })
  })

  it('no renderiza nada sin celda seleccionada', () => {
    render(
      <DialogoNuevoBloque
        abierto
        diaSemana={null}
        horaInicio={null}
        nombreDia=""
        cargando={false}
        error={null}
        onConfirmar={vi.fn()}
        onCerrar={vi.fn()}
      />,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
