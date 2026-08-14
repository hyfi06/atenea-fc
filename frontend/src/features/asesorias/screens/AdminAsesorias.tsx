import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import { Skeleton } from '../../../components/ui/Skeleton'
import { TarjetaAsesoria } from '../components/TarjetaAsesoria'
import { useAdminAsesorias, useAdminSemestres, useBuscarAlumnos, useBuscarAsesores } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { historial, proximas } from '../logica'
import type { AlumnoBusqueda, AsesorBusqueda, AsesoriaAdmin } from '../../../api/types'

export function AdminAsesorias() {
  const navigate = useNavigate()
  const mapaMaterias = useMapaMaterias()
  const [asesor, setAsesor] = useState<AsesorBusqueda | null>(null)
  const [alumno, setAlumno] = useState<AlumnoBusqueda | null>(null)
  const idAsesor = asesor?.perfil_id ?? null
  const idAlumno = alumno?.perfil_id ?? null

  const { data: asesorias = [], isPending } = useAdminAsesorias({ asesor: idAsesor, alumno: idAlumno })
  const nombreMateria = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={() => navigate('/home')} className="foco-visible w-fit min-h-11 text-sm text-primary">
        ← Inicio
      </button>
      <h1 className="text-lg font-semibold text-on-background">Asesorías · SAE</h1>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => navigate('/sae/asesorias/oferta')}
          className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
        >
          Consultar oferta
        </button>
        <button
          type="button"
          onClick={() => navigate('/sae/asesores')}
          className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
        >
          Asesores
        </button>
      </div>

      <div className="flex flex-col gap-3">
        <FiltroAsesor valor={asesor} onCambiar={setAsesor} />
        <FiltroAlumno valor={alumno} onCambiar={setAlumno} />
      </div>

      <Tabs defaultValue="proximas">
        <TabsList>
          <TabsTrigger value="proximas">Próximas</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="proximas">
          <ListaAdmin
            asesorias={proximas(asesorias)}
            cargando={isPending}
            nombreMateria={nombreMateria}
            vacio="No hay asesorías próximas con estos filtros."
          />
        </TabsContent>
        <TabsContent value="historial">
          <Historial asesor={idAsesor} alumno={idAlumno} nombreMateria={nombreMateria} />
        </TabsContent>
      </Tabs>
    </main>
  )
}

function FiltroAsesor({
  valor,
  onCambiar,
}: {
  valor: AsesorBusqueda | null
  onCambiar: (a: AsesorBusqueda | null) => void
}) {
  const [busqueda, setBusqueda] = useState('')
  // Espejo del filtro de alumno: el directorio crece y hay que poder buscar
  // por número de trabajador, así que es búsqueda en servidor y no un select.
  const { data: resultados = [] } = useBuscarAsesores(busqueda)

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="filtro-asesor" className="text-xs text-on-surface-variant">Asesor</label>
      <input
        id="filtro-asesor"
        type="text"
        placeholder="Nombre o número de trabajador…"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
      />

      {valor !== null ? (
        <button
          type="button"
          onClick={() => { onCambiar(null); setBusqueda('') }}
          aria-label={`Quitar filtro de ${valor.nombre}`}
          className="foco-visible min-h-11 w-fit rounded-full bg-primary-container px-3 text-sm text-on-primary-container"
        >
          {valor.nombre} ✕
        </button>
      ) : (
        busqueda.length >= 2 && resultados.length > 0 && (
          <ul className="flex flex-col gap-1" aria-label="Resultados de asesores">
            {resultados.map((a) => (
              <li key={a.perfil_id}>
                <button
                  type="button"
                  onClick={() => onCambiar(a)}
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-md bg-surface-container px-3 text-left text-sm text-on-surface"
                >
                  <span className="truncate" title={a.nombre}>{a.nombre}</span>
                  <span className="ml-3 shrink-0 text-xs text-on-surface-variant">{a.numero_trabajador}</span>
                </button>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  )
}

function FiltroAlumno({
  valor,
  onCambiar,
}: {
  valor: AlumnoBusqueda | null
  onCambiar: (a: AlumnoBusqueda | null) => void
}) {
  const [busqueda, setBusqueda] = useState('')
  // El conjunto de alumnos es grande: búsqueda en servidor, no select.
  const { data: resultados = [] } = useBuscarAlumnos(busqueda)

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="filtro-alumno" className="text-xs text-on-surface-variant">Alumno</label>
      <input
        id="filtro-alumno"
        type="text"
        placeholder="Nombre o número de cuenta…"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
      />

      {valor !== null ? (
        <button
          type="button"
          onClick={() => { onCambiar(null); setBusqueda('') }}
          aria-label={`Quitar filtro de ${valor.nombre}`}
          className="foco-visible min-h-11 w-fit rounded-full bg-primary-container px-3 text-sm text-on-primary-container"
        >
          {valor.nombre} ✕
        </button>
      ) : (
        busqueda.length >= 2 && resultados.length > 0 && (
          <ul className="flex flex-col gap-1" aria-label="Resultados de alumnos">
            {resultados.map((a) => (
              <li key={a.perfil_id}>
                <button
                  type="button"
                  onClick={() => onCambiar(a)}
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-md bg-surface-container px-3 text-left text-sm text-on-surface"
                >
                  <span className="truncate" title={a.nombre}>{a.nombre}</span>
                  <span className="ml-3 shrink-0 text-xs text-on-surface-variant">{a.numero_cuenta}</span>
                </button>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  )
}

function Historial({
  asesor,
  alumno,
  nombreMateria,
}: {
  asesor: number | null
  alumno: number | null
  nombreMateria: (id: number) => string
}) {
  const { data: semestres = [], isPending } = useAdminSemestres()
  const [activo, setActivo] = useState<string | null>(null)
  const semestre = activo ?? semestres[0] ?? null

  if (isPending) return <Skeleton className="h-8 w-40" />
  if (semestre === null) return <p className="text-sm text-on-surface-variant">Aún no hay historial.</p>

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
      <ListaDeSemestre asesor={asesor} alumno={alumno} semestre={semestre} nombreMateria={nombreMateria} />
    </div>
  )
}

function ListaDeSemestre({
  asesor,
  alumno,
  semestre,
  nombreMateria,
}: {
  asesor: number | null
  alumno: number | null
  semestre: string
  nombreMateria: (id: number) => string
}) {
  const { data: asesorias = [], isPending } = useAdminAsesorias({ asesor, alumno, semestre })
  return (
    <ListaAdmin
      asesorias={historial(asesorias)}
      cargando={isPending}
      nombreMateria={nombreMateria}
      vacio="Sin sesiones en este semestre."
    />
  )
}

function ListaAdmin({
  asesorias,
  cargando,
  nombreMateria,
  vacio,
}: {
  asesorias: AsesoriaAdmin[]
  cargando: boolean
  nombreMateria: (id: number) => string
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
          admin
        />
      ))}
    </ul>
  )
}
