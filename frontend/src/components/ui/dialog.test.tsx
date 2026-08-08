import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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
  it('expone el contenido como diálogo con nombre accesible tomado del título', () => {
    abrirDialogo()

    expect(screen.getByRole('dialog', { name: 'Título de prueba' })).toBeInTheDocument()
    expect(screen.getByText('Descripción de prueba')).toBeInTheDocument()
  })

  it('cierra con Escape sin que el componente intercepte el teclado', () => {
    const onOpenChange = abrirDialogo()

    fireEvent.keyDown(document, { key: 'Escape' })

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
