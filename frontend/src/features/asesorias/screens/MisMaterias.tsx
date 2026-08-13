import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { primerMensajeDeError } from '../../../api/errores'
import { IconBasura } from '../../../components/icons/UiIcons'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { useMapaMaterias } from '../../catalogo/api'
import { useAgregarMateria, useQuitarMateria, useRegistroDelSemestre } from '../api'
import { DialogoAgregarMateria } from '../components/DialogoAgregarMateria'
import { DialogoQuitarMateria } from '../components/DialogoQuitarMateria'
import { SinRegistroAsesor } from '../components/SinRegistroAsesor'

interface MisMateriasProps {
  /** Modo consulta (SAE): sin agregar/quitar, sin diálogos y sin `<main>` propio. */
  soloLectura?: boolean
  /** Ids de materias a mostrar. `null` → las del registro propio del asesor. */
  materias?: number[] | null
  /** Semestre a etiquetar cuando `materias` viene de fuera. */
  semestre?: string | null
}

export function MisMaterias({ soloLectura = false, materias = null, semestre = null }: MisMateriasProps) {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()
  // En modo consulta quien mira es SAE: GET /registros/ le daría 403, así que
  // la query se apaga y los datos llegan por props.
  const { registro, cargando } = useRegistroDelSemestre(undefined, !soloLectura)
  const mapaMaterias = useMapaMaterias()

  const agregarMateria = useAgregarMateria(registro?.id ?? 0)
  const quitarMateria = useQuitarMateria(registro?.id ?? 0)

  const [dialogoAgregarAbierto, setDialogoAgregarAbierto] = useState(false)
  const [errorAgregar, setErrorAgregar] = useState<string | null>(null)
  const [materiaAQuitar, setMateriaAQuitar] = useState<number | null>(null)
  const [errorQuitar, setErrorQuitar] = useState<string | null>(null)
  const [expandida, setExpandida] = useState<number | null>(null)

  const nombreDe = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`
  const ids = soloLectura ? (materias ?? []) : (registro?.materias ?? [])
  const etiquetaSemestre = soloLectura ? semestre : (registro?.semestre ?? null)

  if (!soloLectura && cargando) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }

  const lista =
    ids.length === 0 ? (
      <p className="text-sm text-on-surface-variant">
        {soloLectura
          ? 'Este asesor no imparte materias en el semestre seleccionado.'
          : 'Todavía no impartes ninguna materia este semestre.'}
      </p>
    ) : (
      <ul className="flex flex-col">
        {ids.map((id) => (
          <li key={id} className="flex items-center gap-2 border-b border-outline-variant">
            <button
              type="button"
              title={nombreDe(id)}
              onClick={() => setExpandida((previa) => (previa === id ? null : id))}
              className={`foco-visible min-h-11 min-w-0 flex-1 rounded-md px-2 py-2 text-left text-sm text-on-surface ${
                expandida === id ? '' : 'truncate'
              }`}
            >
              {nombreDe(id)}
            </button>
            {!soloLectura && (
              <button
                type="button"
                aria-label={`Quitar ${nombreDe(id)}`}
                onClick={() => {
                  setErrorQuitar(null)
                  setMateriaAQuitar(id)
                }}
                className="foco-visible flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-high"
              >
                <IconBasura className="h-5 w-5" />
              </button>
            )}
          </li>
        ))}
      </ul>
    )

  if (soloLectura) {
    return (
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-on-background">Materias</h2>
        {etiquetaSemestre !== null && (
          <p className="text-xs text-on-surface-variant">Semestre {etiquetaSemestre}</p>
        )}
        {lista}
      </section>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>

      <div className="flex items-center justify-between gap-2">
        <h1 className="text-lg font-semibold text-on-background">Mis materias</h1>
        <button
          type="button"
          onClick={() => {
            setErrorAgregar(null)
            setDialogoAgregarAbierto(true)
          }}
          className="foco-visible min-h-11 rounded-full px-2 text-sm font-medium text-primary"
        >
          + Agregar
        </button>
      </div>

      <p className="text-xs text-on-surface-variant">Semestre {etiquetaSemestre}</p>

      {lista}

      <DialogoAgregarMateria
        abierto={dialogoAgregarAbierto}
        cargando={agregarMateria.isPending}
        error={errorAgregar}
        onConfirmar={(materiaId) =>
          agregarMateria.mutate(materiaId, {
            onSuccess: () => {
              setDialogoAgregarAbierto(false)
              mostrar('Materia agregada')
            },
            onError: (error) => setErrorAgregar(primerMensajeDeError(error)),
          })
        }
        onCerrar={() => setDialogoAgregarAbierto(false)}
      />

      <DialogoQuitarMateria
        abierto={materiaAQuitar !== null}
        nombreMateria={materiaAQuitar !== null ? nombreDe(materiaAQuitar) : ''}
        cargando={quitarMateria.isPending}
        error={errorQuitar}
        onConfirmar={() => {
          if (materiaAQuitar === null) return
          quitarMateria.mutate(materiaAQuitar, {
            onSuccess: () => {
              setMateriaAQuitar(null)
              mostrar('Materia quitada')
            },
            onError: (error) => setErrorQuitar(primerMensajeDeError(error)),
          })
        }}
        onCerrar={() => setMateriaAQuitar(null)}
      />

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
