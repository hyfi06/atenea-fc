import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CampoTexto } from './CampoTexto'

describe('CampoTexto', () => {
  it('asocia el label al input y muestra foco visible', () => {
    render(
      <CampoTexto etiqueta="Correo" tipo="email" autoComplete="email" valor="" onChange={vi.fn()} />,
    )

    const input = screen.getByLabelText('Correo')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('type', 'email')
    expect(input).toHaveClass('focus-visible:outline-2')
    expect(input).toHaveClass('focus-visible:outline-primary')
  })

  it('propaga los cambios', () => {
    const onChange = vi.fn()
    render(
      <CampoTexto etiqueta="Correo" tipo="email" autoComplete="email" valor="" onChange={onChange} />,
    )

    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'ana@ciencias.unam.mx' } })

    expect(onChange).toHaveBeenCalledTimes(1)
  })
})
