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

export function MisMaterias() {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()
  const { registro, cargando } = useRegistroDelSemestre()
  const mapaMaterias = useMapaMaterias()

  const agregarMateria = useAgregarMateria(registro?.id ?? 0)
  const quitarMateria = useQuitarMateria(registro?.id ?? 0)

  const [dialogoAgregarAbierto, setDialogoAgregarAbierto] = useState(false)
  const [errorAgregar, setErrorAgregar] = useState<string | null>(null)
  const [materiaAQuitar, setMateriaAQuitar] = useState<number | null>(null)
  const [errorQuitar, setErrorQuitar] = useState<string | null>(null)
  const [expandida, setExpandida] = useState<number | null>(null)

  if (cargando) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }

  const nombreDe = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

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

      <p className="text-xs text-on-surface-variant">Semestre {registro.semestre}</p>

      {registro.materias.length === 0 ? (
        <p className="text-sm text-on-surface-variant">
          Todavía no impartes ninguna materia este semestre.
        </p>
      ) : (
        <ul className="flex flex-col">
          {registro.materias.map((id) => (
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
            </li>
          ))}
        </ul>
      )}

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
