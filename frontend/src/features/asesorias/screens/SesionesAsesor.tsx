import { useNavigate } from 'react-router-dom'
import * as Tabs from '@radix-ui/react-tabs'
import { useMisAsesorias } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { proximas, historial } from '../logica'
import { TarjetaAsesoria } from '../components/TarjetaAsesoria'
import { Skeleton } from '../../../components/ui/Skeleton'

export function SesionesAsesor() {
  const navigate = useNavigate()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>
        <button
          type="button"
          onClick={() => navigate('/asesorias/disponibilidad')}
          className="text-xs font-medium text-primary"
        >
          Disponibilidad
        </button>
      </div>

      <Tabs.Root defaultValue="proximas">
        <Tabs.List className="mb-4 flex gap-4 border-b border-outline-variant text-sm">
          <Tabs.Trigger
            value="proximas"
            className="px-1 pb-2 text-on-surface-variant data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary"
          >
            Próximas
          </Tabs.Trigger>
          <Tabs.Trigger
            value="historial"
            className="px-1 pb-2 text-on-surface-variant data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary"
          >
            Historial
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="proximas">
          <ListaAsesorias asesorias={proximas(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="No tienes asesorías próximas." />
        </Tabs.Content>
        <Tabs.Content value="historial">
          <ListaAsesorias asesorias={historial(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="Aún no hay historial." />
        </Tabs.Content>
      </Tabs.Root>
    </main>
  )
}

function ListaAsesorias({
  asesorias,
  cargando,
  nombreMateria,
  vacio,
}: {
  asesorias: ReturnType<typeof proximas>
  cargando: boolean
  nombreMateria: (id: number) => string | undefined
  vacio: string
}) {
  if (cargando) {
    return (
      <ul className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </ul>
    )
  }

  if (asesorias.length === 0) {
    return <p className="text-sm text-on-surface-variant">{vacio}</p>
  }

  return (
    <ul className="flex flex-col gap-2">
      {asesorias.map((asesoria, indice) => (
        <TarjetaAsesoria
          key={asesoria.id}
          asesoria={asesoria}
          nombreMateria={nombreMateria(asesoria.materia) ?? `Materia #${asesoria.materia}`}
          indice={indice}
        />
      ))}
    </ul>
  )
}
