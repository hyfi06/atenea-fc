import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { Dialogo } from './Dialogo'

function etiquetasDeBotones() {
  return screen.getAllByRole('button').map((boton) => boton.textContent)
}

describe('Dialogo — convención de orden de botones (paso 3)', () => {
  it('con una sola acción pone salir a la izquierda y la acción a la derecha', () => {
    render(
      <Dialogo
        abierto
        titulo="Cancelar asesoría"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Confirmar cancelación', tono: 'peligro', onClick: vi.fn() }]}
      />,
    )

    expect(etiquetasDeBotones()).toEqual(['Volver', 'Confirmar cancelación'])
  })

  it('con dos o más acciones pasa a columna, respeta el orden y deja salir al final', () => {
    render(
      <Dialogo
        abierto
        titulo="Este horario tiene sesiones agendadas"
        onCerrar={vi.fn()}
        acciones={[
          { etiqueta: 'Solo dejar de recibir nuevas', onClick: vi.fn() },
          { etiqueta: 'Cancelar esas sesiones y desactivar', tono: 'peligro', onClick: vi.fn() },
        ]}
      />,
    )

    expect(etiquetasDeBotones()).toEqual([
      'Solo dejar de recibir nuevas',
      'Cancelar esas sesiones y desactivar',
      'Volver',
    ])
  })

  it('en columna la acción consecuente va en contorno, nunca rellena', () => {
    render(
      <Dialogo
        abierto
        titulo="Bloque activo"
        onCerrar={vi.fn()}
        acciones={[
          { etiqueta: 'Desactivar', onClick: vi.fn() },
          { etiqueta: 'Eliminar', tono: 'peligro', onClick: vi.fn() },
        ]}
      />,
    )

    const consecuente = screen.getByRole('button', { name: 'Eliminar' })
    expect(consecuente).toHaveClass('bg-transparent')
    expect(consecuente).toHaveClass('border-error')
  })

  it('los botones no se desbordan con etiquetas largas (min-w-0 + salto de línea)', () => {
    render(
      <Dialogo
        abierto
        titulo="Quitar materia"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Quitar Aplicación de las Ciencias de la Tierra', tono: 'peligro', onClick: vi.fn() }]}
      />,
    )

    for (const boton of screen.getAllByRole('button')) {
      expect(boton).toHaveClass('min-w-0')
      expect(boton).toHaveClass('whitespace-normal')
    }
  })

  it('todo botón del diálogo lleva el estado de foco visible del paso 7', () => {
    render(
      <Dialogo abierto titulo="Con foco" onCerrar={vi.fn()} acciones={[{ etiqueta: 'Aceptar', onClick: vi.fn() }]} />,
    )

    for (const boton of screen.getAllByRole('button')) {
      expect(boton).toHaveClass('foco-visible')
    }
  })
})

describe('Dialogo — comportamiento', () => {
  afterEach(() => vi.useRealTimers())

  it('el botón de salir llama a onCerrar de inmediato', () => {
    const onCerrar = vi.fn()
    render(<Dialogo abierto titulo="Salir" onCerrar={onCerrar} acciones={[]} etiquetaSalir="Cerrar" />)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))

    // El botón invoca `onCerrar` directo, sin pasar por Radix: no hay salida
    // que esperar. Escape sí pasa por Radix, y ese camino se prueba abajo.
    expect(onCerrar).toHaveBeenCalledTimes(1)
  })

  it('Escape llama a onCerrar cuando termina la animación de salida', () => {
    vi.useFakeTimers()
    const onCerrar = vi.fn()
    render(<Dialogo abierto titulo="Salir" onCerrar={onCerrar} acciones={[]} etiquetaSalir="Cerrar" />)

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onCerrar).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(150)
    })

    expect(onCerrar).toHaveBeenCalledTimes(1)
  })

  it('una acción deshabilitada no dispara su onClick', () => {
    const onClick = vi.fn()
    render(
      <Dialogo
        abierto
        titulo="Agregar materia"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Agregar', deshabilitada: true, onClick }]}
      />,
    )

    const boton = screen.getByRole('button', { name: 'Agregar' })
    expect(boton).toBeDisabled()
    fireEvent.click(boton)
    expect(onClick).not.toHaveBeenCalled()
  })

  it('una acción cargando se deshabilita sola', () => {
    render(
      <Dialogo
        abierto
        titulo="Creando"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Crear', cargando: true, onClick: vi.fn() }]}
      />,
    )

    expect(screen.getByRole('button', { name: 'Crear' })).toBeDisabled()
  })

  it('el error se anuncia como alerta', () => {
    render(
      <Dialogo abierto titulo="Con error" error="No se pudo guardar." onCerrar={vi.fn()} acciones={[]} />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo guardar.')
  })

  it('renderiza el contenido propio del consumidor', () => {
    render(
      <Dialogo abierto titulo="Con formulario" onCerrar={vi.fn()} acciones={[]}>
        <label htmlFor="campo">Motivo</label>
        <input id="campo" />
      </Dialogo>,
    )

    expect(screen.getByLabelText('Motivo')).toBeInTheDocument()
  })
})
