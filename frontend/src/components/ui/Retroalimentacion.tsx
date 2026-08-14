import { useCallback, useState } from 'react'

type TipoMensaje = 'exito' | 'error'
interface Mensaje {
  texto: string
  tipo: TipoMensaje
}

/** Debe coincidir con la duración de `.salida-toast` en `index.css`. */
const SALIDA_MS = 200
/** Tiempo con el toast completamente visible antes de empezar a salir. */
const VISIBLE_MS = 2700

export function useRetroalimentacion() {
  const [mensaje, setMensaje] = useState<Mensaje | null>(null)
  const [saliendo, setSaliendo] = useState(false)

  const mostrar = useCallback((texto: string, tipo: TipoMensaje = 'exito') => {
    // Cierre en dos tiempos: primero se marca la salida (que aplica
    // `.salida-toast`), y sólo cuando esa animación terminó se desmonta. Antes
    // el toast desaparecía de golpe al limpiar `mensaje`.
    setSaliendo(false)
    setMensaje({ texto, tipo })
    setTimeout(() => setSaliendo(true), VISIBLE_MS)
    setTimeout(() => {
      setMensaje(null)
      setSaliendo(false)
    }, VISIBLE_MS + SALIDA_MS)
  }, [])

  return { mensaje, saliendo, mostrar }
}

export function Retroalimentacion({
  mensaje,
  saliendo,
}: {
  mensaje: Mensaje | null
  saliendo: boolean
}) {
  if (!mensaje) return null
  const color = mensaje.tipo === 'exito' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'
  return (
    <div
      role="status"
      className={`${saliendo ? 'salida-toast' : 'entrada-lista'} fixed inset-x-0 bottom-6 mx-auto w-fit rounded-full px-4 py-2 text-sm font-medium shadow-lg ${color}`}
    >
      {mensaje.texto}
    </div>
  )
}
