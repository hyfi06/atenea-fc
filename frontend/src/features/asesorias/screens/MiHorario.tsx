import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { primerMensajeDeError } from '../../../api/errores'
import type { Disponibilidad, FormatoAsesoria } from '../../../api/types'
import { IconPresencial, IconVirtual } from '../../../components/icons/UiIcons'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { Skeleton } from '../../../components/ui/Skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import {
  useActualizarDisponibilidad,
  useCrearDisponibilidad,
  useDesactivarDisponibilidad,
  useEliminarDisponibilidad,
  useMisDisponibilidades,
  useRegistroDelSemestre,
  useSesionesFuturas,
} from '../api'
import { DialogoBloqueActivo } from '../components/DialogoBloqueActivo'
import { DialogoDesactivarConSesiones } from '../components/DialogoDesactivarConSesiones'
import { DialogoNuevoBloque } from '../components/DialogoNuevoBloque'
import { SinRegistroAsesor } from '../components/SinRegistroAsesor'
import { diaSemanaHoy, slotsDelDia } from '../logica'

const DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const INSTRUCCION =
  'Cada celda es un horario disponible: toca para activarlo o editarlo. Para cambiar de día, usa las pestañas. Los cambios se autoguardan.'

function Leyenda() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant">
      <span className="rounded-full bg-primary-container px-2 py-0.5 text-on-primary-container">Activo</span>
      <span className="rounded-full bg-surface-variant px-2 py-0.5 text-on-surface-variant">Inactivo</span>
      <span className="flex items-center gap-1">
        <IconVirtual className="h-4 w-4" /> Virtual
      </span>
      <span className="flex items-center gap-1">
        <IconPresencial className="h-4 w-4" /> Presencial
      </span>
    </div>
  )
}

export function MiHorario() {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()

  const { registro, cargando: cargandoRegistro } = useRegistroDelSemestre()
  const { data: disponibilidades = [], isPending: cargandoDisponibilidades } = useMisDisponibilidades()

  const crearDisponibilidad = useCrearDisponibilidad()
  const actualizarDisponibilidad = useActualizarDisponibilidad()
  const eliminarDisponibilidad = useEliminarDisponibilidad()
  const desactivarDisponibilidad = useDesactivarDisponibilidad()

  const [bloqueSeleccionado, setBloqueSeleccionado] = useState<Disponibilidad | null>(null)
  const [celdaVacia, setCeldaVacia] = useState<{ dia: number; hora: string } | null>(null)
  const [advertenciaAbierta, setAdvertenciaAbierta] = useState(false)
  const [errorBloque, setErrorBloque] = useState<string | null>(null)
  const [errorAdvertencia, setErrorAdvertencia] = useState<string | null>(null)

  const sesionesFuturas = useSesionesFuturas(bloqueSeleccionado?.id ?? null)

  if (cargandoRegistro) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!registro) {
    return <SinRegistroAsesor titulo="Mi horario" />
  }

  function tocarSlot(dia: number, hora: string, disponibilidad: Disponibilidad | null) {
    if (disponibilidad === null) {
      setErrorBloque(null)
      setCeldaVacia({ dia, hora })
      return
    }
    if (!disponibilidad.activa) {
      // Autoguardado: reactivar no destruye nada, no necesita confirmación.
      actualizarDisponibilidad.mutate(
        { id: disponibilidad.id, activa: true },
        { onSuccess: () => mostrar('Bloque activado') },
      )
      return
    }
    setBloqueSeleccionado(disponibilidad)
  }

  function desactivar(cancelarSesiones: boolean) {
    if (!bloqueSeleccionado) return
    desactivarDisponibilidad.mutate(
      { id: bloqueSeleccionado.id, cancelarSesiones },
      {
        onSuccess: () => {
          setAdvertenciaAbierta(false)
          setBloqueSeleccionado(null)
          mostrar(cancelarSesiones ? 'Bloque desactivado y sesiones canceladas' : 'Bloque desactivado')
        },
        onError: (error) => setErrorAdvertencia(primerMensajeDeError(error)),
      },
    )
  }

  function manejarDesactivar() {
    if ((sesionesFuturas.data?.total ?? 0) > 0) {
      setErrorAdvertencia(null)
      setAdvertenciaAbierta(true)
      return
    }
    desactivar(false)
  }

  function manejarEliminar() {
    if (!bloqueSeleccionado) return
    const id = bloqueSeleccionado.id
    setBloqueSeleccionado(null)
    eliminarDisponibilidad.mutate(id, { onSuccess: () => mostrar('Bloque eliminado') })
  }

  function manejarCrear(datos: { formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }) {
    if (!celdaVacia || !registro) return
    crearDisponibilidad.mutate(
      {
        registro: registro.id,
        dia_semana: celdaVacia.dia,
        hora_inicio: celdaVacia.hora,
        ...datos,
      },
      {
        onSuccess: () => {
          setCeldaVacia(null)
          mostrar('Bloque creado')
        },
        onError: (error) => setErrorBloque(primerMensajeDeError(error)),
      },
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

      <h1 className="text-lg font-semibold text-on-background">Mi horario</h1>
      <p className="text-xs text-on-surface-variant">{INSTRUCCION}</p>
      <Leyenda />

      <Tabs defaultValue={String(diaSemanaHoy())}>
        <TabsList className="gap-2 overflow-x-auto">
          {DIAS_CORTOS.map((dia, indice) => (
            <TabsTrigger key={dia} value={String(indice)}>
              {dia}
            </TabsTrigger>
          ))}
        </TabsList>

        {DIAS_CORTOS.map((_, indice) => (
          <TabsContent key={indice} value={String(indice)}>
            {cargandoDisponibilidades ? (
              <ul className="flex flex-col gap-1">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-11" />
                ))}
              </ul>
            ) : (
              <ul className="flex flex-col">
                {slotsDelDia(indice, disponibilidades).map((slot) => (
                  <li key={slot.clave}>
                    <button
                      type="button"
                      onClick={() => tocarSlot(indice, slot.hora, slot.disponibilidad)}
                      aria-label={`Horario ${slot.hora.slice(0, 5)}, ${slot.activo ? 'activo' : 'inactivo'}`}
                      className="foco-visible flex min-h-11 w-full items-center gap-2 border-b border-outline-variant px-2 text-sm text-on-surface hover:bg-surface-container-high"
                    >
                      <span className="w-12 shrink-0 text-on-surface-variant">{slot.hora.slice(0, 5)}</span>

                      {slot.activo && slot.disponibilidad !== null && (
                        <span className="flex min-w-0 flex-1 items-center gap-2">
                          {slot.disponibilidad.formato === 'virtual' ? (
                            <IconVirtual className="h-4 w-4 shrink-0" />
                          ) : (
                            <IconPresencial className="h-4 w-4 shrink-0" />
                          )}
                          {slot.disponibilidad.formato === 'presencial' && (
                            <span className="truncate">{slot.disponibilidad.ubicacion}</span>
                          )}
                        </span>
                      )}

                      <span
                        className={`ml-auto shrink-0 rounded-full px-2 py-0.5 text-xs ${
                          slot.activo
                            ? 'bg-primary-container text-on-primary-container'
                            : 'bg-surface-variant text-on-surface-variant'
                        }`}
                      >
                        {slot.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </TabsContent>
        ))}
      </Tabs>

      <DialogoBloqueActivo
        abierto={bloqueSeleccionado !== null && !advertenciaAbierta}
        disponibilidad={bloqueSeleccionado}
        cargando={desactivarDisponibilidad.isPending || sesionesFuturas.isPending}
        onDesactivar={manejarDesactivar}
        onEliminar={manejarEliminar}
        onCerrar={() => setBloqueSeleccionado(null)}
      />

      <DialogoDesactivarConSesiones
        abierto={advertenciaAbierta}
        total={sesionesFuturas.data?.total ?? 0}
        cargando={desactivarDisponibilidad.isPending}
        error={errorAdvertencia}
        onSoloNuevas={() => desactivar(false)}
        onCancelarYDesactivar={() => desactivar(true)}
        onCerrar={() => setAdvertenciaAbierta(false)}
      />

      <DialogoNuevoBloque
        abierto={celdaVacia !== null}
        diaSemana={celdaVacia?.dia ?? null}
        horaInicio={celdaVacia?.hora ?? null}
        nombreDia={celdaVacia ? DIAS[celdaVacia.dia] : ''}
        cargando={crearDisponibilidad.isPending}
        error={errorBloque}
        onConfirmar={manejarCrear}
        onCerrar={() => setCeldaVacia(null)}
      />

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
