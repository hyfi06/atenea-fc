import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Boton } from '../components/ui/Boton'

/**
 * Pantalla del comodín `path="*"`. La salida apunta a `/` y no a `/home`
 * porque la landing ya resuelve los dos casos: con sesión redirige a /home,
 * sin sesión se muestra a sí misma.
 */
export function NoEncontrado() {
  const navigate = useNavigate()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 px-6 py-12 text-center">
      <Logo className="h-16 w-16 text-primary" />
      <p className="text-5xl font-semibold text-primary">404</p>
      <h1 className="text-lg font-semibold text-on-background">Página no encontrada</h1>
      <p className="max-w-[28ch] text-sm text-on-surface-variant">
        La dirección que abriste no existe o cambió de lugar.
      </p>
      <Boton type="button" onClick={() => navigate('/')} className="px-6">
        Volver al inicio
      </Boton>
    </main>
  )
}
