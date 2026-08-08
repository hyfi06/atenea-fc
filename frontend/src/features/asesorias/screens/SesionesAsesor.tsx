import { useNavigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
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
      <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => navigate('/asesorias/materias')}
          className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
        >
          Mis materias
        </button>
        <button
          type="button"
          onClick={() => navigate('/asesorias/horario')}
          className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
        >
          Mi horario
        </button>
      </div>

      <Tabs defaultValue="proximas">
        <TabsList>
          <TabsTrigger value="proximas">Próximas</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="proximas">
          <ListaAsesorias asesorias={proximas(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="No tienes asesorías próximas." />
        </TabsContent>
        <TabsContent value="historial">
          <ListaAsesorias asesorias={historial(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="Aún no hay historial." />
        </TabsContent>
      </Tabs>
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
