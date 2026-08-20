import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { apiGet } from '../../../api/client'
import { primerMensajeDeError } from '../../../api/errores'
import { useAuth } from '../../../auth/AuthContext'
import { Boton } from '../../../components/ui/Boton'
import { useSolicitarSerAsesor } from '../api'

interface Area {
  id: number
  nombre: string
}

export function SolicitudAsesor() {
  const navigate = useNavigate()
  const { data: areas = [] } = useQuery({
    queryKey: ['areas'],
    queryFn: () => apiGet<Area[]>('/api/carreras/areas/'),
    staleTime: Infinity,
  })
  const solicitar = useSolicitarSerAsesor()
  const { refrescarSesion } = useAuth()
  const [area, setArea] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [listo, setListo] = useState(false)

  if (listo) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <h1 className="text-lg font-semibold text-on-background">Solicitud enviada</h1>
        <p className="text-sm text-on-surface-variant">
          Tu perfil de asesor quedó pendiente de que la SAE confirme que tu
          nombramiento está vigente. En cuanto quede aprobado podrás cargar tus
          materias y tu horario.
        </p>
        <Boton type="button" onClick={() => navigate('/asesorias')} className="w-fit px-6">
          Ir a Asesorías
        </Boton>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit min-h-11 text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">Registrarme como asesor</h1>
      <p className="text-sm text-on-surface-variant">
        Elige el área en la que darás asesorías. La SAE confirmará que tu nombramiento
        esté vigente antes de publicar tu disponibilidad.
      </p>

      {error && <p role="alert" className="text-xs text-error">{error}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="area-solicitud" className="text-xs text-on-surface-variant">Área</label>
        <select
          id="area-solicitud"
          value={area ?? ''}
          onChange={(e) => setArea(e.target.value === '' ? null : Number(e.target.value))}
          className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
        >
          <option value="">Elige un área</option>
          {areas.map((a) => (
            <option key={a.id} value={a.id}>{a.nombre}</option>
          ))}
        </select>
      </div>

      <Boton
        type="button"
        disabled={area === null}
        cargando={solicitar.isPending}
        onClick={() => {
          if (area === null) return
          setError(null)
          solicitar.mutate(area, {
            onSuccess: async () => {
              await refrescarSesion()
              setListo(true)
            },
            onError: (err) => setError(primerMensajeDeError(err)),
          })
        }}
        className="w-fit px-6"
      >
        Solicitar
      </Boton>
    </main>
  )
}
