import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SinRegistroAsesor } from './SinRegistroAsesor'
import * as api from '../api'
import * as client from '../../../api/client'
import * as academico from '../../academico/api'

function montar(ventanaAbierta = true) {
  const mutate = vi.fn()
  vi.spyOn(api, 'useCrearRegistro').mockReturnValue({
    mutate,
    isPending: false,
  } as unknown as ReturnType<typeof api.useCrearRegistro>)
  vi.spyOn(academico, 'useRegistroAsesoresAbierto').mockReturnValue(ventanaAbierta)

  render(
    <MemoryRouter>
      <SinRegistroAsesor titulo="Mis materias" />
    </MemoryRouter>,
  )
  return mutate
}

describe('SinRegistroAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('propone el semestre en curso con ventana abierta', () => {
    const mutate = montar()
    fireEvent.click(screen.getByRole('button', { name: /Registrar semestre/ }))
    expect(mutate).toHaveBeenCalledWith(expect.any(String), expect.anything())
  })

  it('anuncia el título de la pantalla desde la que se llegó', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Mis materias' })).toBeInTheDocument()
  })

  it('no ofrece registrar cuando la ventana está cerrada', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(404, { detail: 'no hay periodo' }))
    montar(false)
    expect(await screen.findByText(/no está abierto/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Registrar semestre/ })).not.toBeInTheDocument()
  })
})
