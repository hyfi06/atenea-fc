import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SinRegistroAsesor } from './SinRegistroAsesor'
import * as api from '../api'

function montar() {
  const mutate = vi.fn()
  vi.spyOn(api, 'useCrearRegistro').mockReturnValue({
    mutate,
    isPending: false,
  } as unknown as ReturnType<typeof api.useCrearRegistro>)

  render(
    <MemoryRouter>
      <SinRegistroAsesor titulo="Mis materias" />
    </MemoryRouter>,
  )
  return mutate
}

describe('SinRegistroAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('propone el semestre en curso y lo deja editar antes de registrar', () => {
    const mutate = montar()
    const campo = screen.getByLabelText('Semestre (AAAAN)') as HTMLInputElement

    expect(campo.value).toBeTruthy()

    fireEvent.change(campo, { target: { value: '20271' } })
    fireEvent.click(screen.getByRole('button', { name: /Registrar semestre 20271/ }))

    expect(mutate).toHaveBeenCalledWith('20271', expect.anything())
  })

  it('anuncia el título de la pantalla desde la que se llegó', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Mis materias' })).toBeInTheDocument()
  })
})
