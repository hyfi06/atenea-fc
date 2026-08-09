import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Boton } from './Boton'

describe('Boton', () => {
  it('lleva un estado de foco visible perceptible (checklist del paso 7)', () => {
    render(<Boton>Entrar</Boton>)

    const boton = screen.getByRole('button', { name: 'Entrar' })
    expect(boton).toHaveClass('focus-visible:outline-2')
    expect(boton).toHaveClass('focus-visible:outline-offset-2')
    expect(boton).toHaveClass('focus-visible:outline-primary')
  })

  it('muestra el spinner y queda deshabilitado mientras carga', () => {
    const { container } = render(<Boton cargando>Entrar</Boton>)

    expect(screen.getByRole('button', { name: 'Entrar' })).toBeDisabled()
    const spinner = container.querySelector('.spinner')
    expect(spinner).toBeTruthy()
    expect(spinner).toHaveAttribute('aria-hidden')
  })

  it('no dispara onClick mientras carga', () => {
    const onClick = vi.fn()
    render(
      <Boton cargando onClick={onClick}>
        Entrar
      </Boton>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(onClick).not.toHaveBeenCalled()
  })

  it('la variante secundario usa el contorno y no el relleno primario', () => {
    render(<Boton variante="secundario">Continuar con Correo Ciencias</Boton>)

    const boton = screen.getByRole('button', { name: 'Continuar con Correo Ciencias' })
    expect(boton).toHaveClass('border-outline')
    expect(boton).not.toHaveClass('bg-primary')
  })
})
