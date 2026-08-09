import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import { useMisAsesorias, useSemestres, useAsesoriasDeSemestre } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { proximas, historial } from '../logica'
import { TarjetaAsesoria } from '../components/TarjetaAsesoria'
import { Skeleton } from '../../../components/ui/Skeleton'
import { useEsAsesor, useEsAlumno } from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

export function Asesorias() {
  const navigate = useNavigate()
  const location = useLocation()
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()
  // `location.state` sobrevive a refresh/back-nav, así que el resaltado se
  // reactivaría sobre una asesoría vieja. Lo consumimos una vez: leemos el id
  // a estado local y limpiamos el state de navegación para que el pulso/scroll
  // dispare sólo tras el agendado real.
  const [nuevaAsesoriaId, setNuevaAsesoriaId] = useState<number | null>(null)
  const nombreMateria = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

  useEffect(() => {
    const id = (location.state as { nuevaAsesoriaId?: number } | null)?.nuevaAsesoriaId
    if (id != null) {
      setNuevaAsesoriaId(id)
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location, navigate])

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>

      <div className="flex gap-2">
        {esAsesor && (
          <>
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
          </>
        )}
        {esAlumno && (
          <button
            type="button"
            onClick={() => navigate('/asesorias/nueva')}
            className="foco-visible min-h-11 flex-1 rounded-full bg-primary px-3 text-sm font-semibold text-on-primary"
          >
            Nueva asesoría
          </button>
        )}
      </div>

      <Tabs defaultValue="proximas">
        <TabsList>
          <TabsTrigger value="proximas">Próximas</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="proximas">
          <ListaAsesorias
            asesorias={proximas(asesorias)}
            cargando={isPending}
            nombreMateria={nombreMateria}
            destacarId={nuevaAsesoriaId}
            vacio="No tienes asesorías próximas."
          />
        </TabsContent>
        <TabsContent value="historial">
          <Historial nombreMateria={nombreMateria} />
        </TabsContent>
      </Tabs>
    </main>
  )
}

function Historial({ nombreMateria }: { nombreMateria: (id: number) => string }) {
  const { data: semestres = [], isPending } = useSemestres()
  const [activo, setActivo] = useState<string | null>(null)
  const semestre = activo ?? semestres[0] ?? null
  const { data: asesorias = [], isPending: cargandoLista } = useAsesoriasDeSemestre(semestre)

  if (isPending) return <Skeleton className="h-8 w-40" />
  if (semestres.length === 0) return <p className="text-sm text-on-surface-variant">Aún no hay historial.</p>

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Semestre">
        {semestres.map((s) => (
          <button
            key={s}
            type="button"
            role="tab"
            aria-selected={s === semestre}
            onClick={() => setActivo(s)}
            className={`foco-visible min-h-11 rounded-full px-3 text-sm ${
              s === semestre ? 'bg-primary-container text-on-primary-container' : 'border border-outline text-primary'
            }`}
          >
            {s}
          </button>
        ))}
      </div>
      <ListaAsesorias
        asesorias={historial(asesorias)}
        cargando={cargandoLista}
        nombreMateria={nombreMateria}
        destacarId={null}
        vacio="Sin sesiones en este semestre."
      />
    </div>
  )
}

function ListaAsesorias({
  asesorias,
  cargando,
  nombreMateria,
  destacarId,
  vacio,
}: {
  asesorias: Asesoria[]
  cargando: boolean
  nombreMateria: (id: number) => string
  destacarId: number | null
  vacio: string
}) {
  if (cargando) {
    return (
      <ul className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <li key={i}><Skeleton className="h-16" /></li>
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
          nombreMateria={nombreMateria(asesoria.materia)}
          indice={indice}
          destacar={asesoria.id === destacarId}
        />
      ))}
    </ul>
  )
}
