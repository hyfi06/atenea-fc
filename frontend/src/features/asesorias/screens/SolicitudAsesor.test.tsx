import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SolicitudAsesor } from './SolicitudAsesor'
import * as client from '../../../api/client'
import * as auth from '../../../auth/AuthContext'
import { usuarioDePrueba } from '../../../test/factories'

function montar() {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: usuarioDePrueba({ roles: ['academico'] }),
    roles: ['academico'],
    status: 'authenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
    refrescarSesion: vi.fn().mockResolvedValue(undefined),
  } as ReturnType<typeof auth.useAuth>)

  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SolicitudAsesor />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SolicitudAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('envía el área elegida y avisa que queda pendiente de validación', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue([{ id: 2, nombre: 'Matemáticas' }])
    const apiPost = vi
      .spyOn(client, 'apiPost')
      .mockResolvedValue({ id: 3, area: 2, area_nombre: 'Matemáticas', activo: false })

    montar()
    // Esperar a que la opción cargada por la query exista en el DOM: si se
    // dispara el `change` antes, jsdom ignora el value porque aún no hay
    // <option value="2">.
    await screen.findByRole('option', { name: 'Matemáticas' })
    fireEvent.change(screen.getByLabelText('Área'), { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Solicitar' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/asesorias/asesores/solicitud/', { area: 2 }),
    )
    expect(await screen.findByText(/pendiente de que la SAE/i)).toBeInTheDocument()
  })
})
