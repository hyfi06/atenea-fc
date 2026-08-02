import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useMisRegistros,
  useCrearRegistro,
  useAgregarMateria,
  useMisDisponibilidades,
  useCrearDisponibilidad,
  useActualizarDisponibilidad,
  useEliminarDisponibilidad,
} from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { semestreActual } from '../logica'
import { GrillaDisponibilidad } from '../components/GrillaDisponibilidad'
import { DialogoNuevoBloque } from '../components/DialogoNuevoBloque'
import { DialogoAgregarMateria } from '../components/DialogoAgregarMateria'
import { Boton } from '../../../components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { ApiError } from '../../../api/client'
import type { Disponibilidad, FormatoAsesoria } from '../../../api/types'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

function primerMensajeDeError(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: string[] | string } | null
    if (Array.isArray(body?.detail)) return body.detail[0]
    if (typeof body?.detail === 'string') return body.detail
  }
  return 'Ocurrió un error inesperado.'
}

export function DisponibilidadAsesor() {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()

  const { data: registros, isPending: cargandoRegistros } = useMisRegistros()
  const crearRegistro = useCrearRegistro()
  const [semestreEditable, setSemestreEditable] = useState(semestreActual())

  const registroActual = registros?.find((r) => r.semestre === semestreEditable)

  const { data: disponibilidades = [], isPending: cargandoDisponibilidades } = useMisDisponibilidades()
  const crearDisponibilidad = useCrearDisponibilidad()
  const actualizarDisponibilidad = useActualizarDisponibilidad()
  const eliminarDisponibilidad = useEliminarDisponibilidad()
  const agregarMateria = useAgregarMateria(registroActual?.id ?? 0)
  const mapaMaterias = useMapaMaterias()

  const [celdaSeleccionada, setCeldaSeleccionada] = useState<{ dia: number; hora: string } | null>(null)
  const [errorBloque, setErrorBloque] = useState<string | null>(null)
  const [dialogoMateriaAbierto, setDialogoMateriaAbierto] = useState(false)
  const [errorMateria, setErrorMateria] = useState<string | null>(null)

  if (cargandoRegistros) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!registroActual) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate(-1)} className="text-sm text-primary">
          ← Volver
        </button>
        <h1 className="text-lg font-semibold text-on-background">Registrar disponibilidad</h1>
        <p className="text-sm text-on-surface-variant">
          Aún no tienes un registro de asesor para este semestre.
        </p>
        <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
          Semestre (AAAAN)
          <input
            type="text"
            value={semestreEditable}
            onChange={(e) => setSemestreEditable(e.target.value)}
            className="h-11 w-32 rounded-md border border-outline bg-transparent px-3 text-sm text-on-surface"
          />
        </label>
        <Boton
          type="button"
          cargando={crearRegistro.isPending}
          onClick={() => crearRegistro.mutate(semestreEditable, { onSuccess: () => mostrar('Registro creado') })}
          className="w-fit px-6"
        >
          Registrar semestre {semestreEditable}
        </Boton>
        <Retroalimentacion mensaje={mensaje} />
      </main>
    )
  }

  function manejarCeldaVacia(dia: number, hora: string) {
    setErrorBloque(null)
    setCeldaSeleccionada({ dia, hora })
  }

  function manejarCeldaActiva(disponibilidad: Disponibilidad) {
    if (window.confirm('¿Eliminar este bloque de disponibilidad?')) {
      eliminarDisponibilidad.mutate(disponibilidad.id, {
        onSuccess: () => mostrar('Bloque eliminado'),
      })
    } else {
      actualizarDisponibilidad.mutate(
        { id: disponibilidad.id, activa: !disponibilidad.activa },
        { onSuccess: () => mostrar('Bloque actualizado') },
      )
    }
  }

  function manejarConfirmarBloque(datos: { formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }) {
    if (!celdaSeleccionada || !registroActual) return
    crearDisponibilidad.mutate(
      {
        registro: registroActual.id,
        dia_semana: celdaSeleccionada.dia,
        hora_inicio: celdaSeleccionada.hora,
        ...datos,
      },
      {
        onSuccess: () => {
          setCeldaSeleccionada(null)
          mostrar('Bloque creado')
        },
        onError: (error) => setErrorBloque(primerMensajeDeError(error)),
      },
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-6 px-6 py-6">
      <button type="button" onClick={() => navigate(-1)} className="w-fit text-sm text-primary">
        ← Volver
      </button>
      <h1 className="text-lg font-semibold text-on-background">Disponibilidad — semestre {registroActual.semestre}</h1>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium text-on-surface">Materias</h2>
          <button type="button" onClick={() => setDialogoMateriaAbierto(true)} className="text-xs font-medium text-primary">
            + Agregar materia
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {registroActual.materias.map((id) => (
            <span key={id} className="rounded-full bg-surface-container-high px-3 py-1 text-xs text-on-surface">
              {mapaMaterias.get(id)?.nombre ?? `Materia #${id}`}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium text-on-surface">Horario semanal</h2>
        <GrillaDisponibilidad
          disponibilidades={disponibilidades}
          cargando={cargandoDisponibilidades}
          onCeldaVacia={manejarCeldaVacia}
          onCeldaActiva={manejarCeldaActiva}
        />
      </section>

      <DialogoNuevoBloque
        abierto={celdaSeleccionada !== null}
        diaSemana={celdaSeleccionada?.dia ?? null}
        horaInicio={celdaSeleccionada?.hora ?? null}
        nombreDia={celdaSeleccionada ? DIAS[celdaSeleccionada.dia] : ''}
        cargando={crearDisponibilidad.isPending}
        error={errorBloque}
        onConfirmar={manejarConfirmarBloque}
        onCerrar={() => setCeldaSeleccionada(null)}
      />

      <DialogoAgregarMateria
        abierto={dialogoMateriaAbierto}
        cargando={agregarMateria.isPending}
        error={errorMateria}
        onConfirmar={(materiaId) =>
          agregarMateria.mutate(materiaId, {
            onSuccess: () => {
              setDialogoMateriaAbierto(false)
              setErrorMateria(null)
              mostrar('Materia agregada')
            },
            onError: (error) => setErrorMateria(primerMensajeDeError(error)),
          })
        }
        onCerrar={() => setDialogoMateriaAbierto(false)}
      />

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
