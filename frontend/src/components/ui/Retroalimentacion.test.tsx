import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { Retroalimentacion, useRetroalimentacion } from './Retroalimentacion'

/** Arnés mínimo: el hook y el componente sólo tienen sentido juntos. */
function Arnes() {
  const { mensaje, saliendo, mostrar } = useRetroalimentacion()
  return (
    <>
      <button type="button" onClick={() => mostrar('Materia agregada')}>
        disparar
      </button>
      <Retroalimentacion mensaje={mensaje} saliendo={saliendo} />
    </>
  )
}

describe('Retroalimentacion', () => {
  afterEach(() => vi.useRealTimers())

  it('entra, marca su salida y termina desmontado', () => {
    vi.useFakeTimers()
    render(<Arnes />)

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    const toast = screen.getByRole('status')
    expect(toast).toHaveTextContent('Materia agregada')
    expect(toast).toHaveClass('entrada-lista')

    // A los 2700 ms el toast sigue montado, ya con la clase de salida: es lo
    // observable del cierre en dos tiempos. La duración visual de la
    // animación CSS no se testea.
    act(() => {
      vi.advanceTimersByTime(2700)
    })
    expect(screen.getByRole('status')).toHaveClass('salida-toast')

    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('un mensaje nuevo cancela el estado de salida del anterior', () => {
    vi.useFakeTimers()
    render(<Arnes />)

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))
    act(() => {
      vi.advanceTimersByTime(2700)
    })
    expect(screen.getByRole('status')).toHaveClass('salida-toast')

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    expect(screen.getByRole('status')).toHaveClass('entrada-lista')
  })

  it('dos llamadas seguidas a mostrar() no dejan que los timers de la primera afecten al segundo toast', () => {
    vi.useFakeTimers()
    render(<Arnes />)

    // Primera llamada en t=0: agenda salida en t=2700 y desmontaje en t=2900.
    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    // Segunda llamada en t=1000: debe cancelar los timers de la primera y
    // agendar los suyos (salida en t=3700, desmontaje en t=3900).
    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))
    expect(screen.getByRole('status')).toHaveClass('entrada-lista')

    // t=2700: si los timers de la primera llamada no se hubieran limpiado,
    // aquí marcarían la salida antes de tiempo.
    act(() => {
      vi.advanceTimersByTime(1700)
    })
    expect(screen.getByRole('status')).toHaveClass('entrada-lista')

    // t=3700: ahora sí corresponde que el segundo toast empiece a salir.
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(screen.getByRole('status')).toHaveClass('salida-toast')

    // t=3900: y se desmonta con su propio temporizador, no antes.
    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
