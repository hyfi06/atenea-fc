import { useCallback, useState } from 'react'

type TipoMensaje = 'exito' | 'error'
interface Mensaje {
  texto: string
  tipo: TipoMensaje
}

export function useRetroalimentacion() {
  const [mensaje, setMensaje] = useState<Mensaje | null>(null)

  const mostrar = useCallback((texto: string, tipo: TipoMensaje = 'exito') => {
    setMensaje({ texto, tipo })
    setTimeout(() => setMensaje(null), 3000)
  }, [])

  return { mensaje, mostrar }
}

export function Retroalimentacion({ mensaje }: { mensaje: Mensaje | null }) {
  if (!mensaje) return null
  const color = mensaje.tipo === 'exito' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'
  return (
    <div
      role="status"
      className={`entrada-lista fixed inset-x-0 bottom-6 mx-auto w-fit rounded-full px-4 py-2 text-sm font-medium shadow-lg ${color}`}
    >
      {mensaje.texto}
    </div>
  )
}
