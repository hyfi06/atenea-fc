import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from './dialog'

function abrirDialogo(onOpenChange = vi.fn()) {
  render(
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>Título de prueba</DialogTitle>
        <DialogDescription>Descripción de prueba</DialogDescription>
      </DialogContent>
    </Dialog>,
  )
  return onOpenChange
}

describe('dialog', () => {
  afterEach(() => vi.useRealTimers())

  it('expone el contenido como diálogo con nombre accesible tomado del título', () => {
    abrirDialogo()

    expect(screen.getByRole('dialog', { name: 'Título de prueba' })).toBeInTheDocument()
    expect(screen.getByText('Descripción de prueba')).toBeInTheDocument()
  })

  it('cierra con Escape, propagando el cierre cuando termina la salida', () => {
    vi.useFakeTimers()
    const onOpenChange = abrirDialogo()

    fireEvent.keyDown(document, { key: 'Escape' })

    // El cierre no se propaga de inmediato: el contenido sigue montado con la
    // clase de salida. La duración visual de la animación no se testea.
    expect(onOpenChange).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog', { name: 'Título de prueba' })).toHaveClass('salida-dialogo')

    act(() => {
      vi.advanceTimersByTime(150)
    })

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('un segundo Escape durante la salida no duplica el onOpenChange(false)', () => {
    vi.useFakeTimers()
    const onOpenChange = abrirDialogo()

    fireEvent.keyDown(document, { key: 'Escape' })
    // Segundo Escape mientras `open` de Radix sigue en `true` (la salida
    // diferida aún no corrió): no debe agendar un segundo timer.
    fireEvent.keyDown(document, { key: 'Escape' })

    act(() => {
      vi.advanceTimersByTime(150)
    })

    expect(onOpenChange).toHaveBeenCalledTimes(1)
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('no renderiza nada cuando está cerrado', () => {
    render(
      <Dialog open={false}>
        <DialogContent>
          <DialogTitle>Oculto</DialogTitle>
        </DialogContent>
      </Dialog>,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
