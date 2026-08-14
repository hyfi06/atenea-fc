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
      <Logo className="entrada-deleite h-16 w-16 text-primary" />
      <p className="entrada-deleite text-5xl font-semibold text-primary" style={{ animationDelay: '70ms' }}>404</p>
      <h1 className="entrada-deleite text-lg font-semibold text-on-background" style={{ animationDelay: '140ms' }}>
        Página no encontrada
      </h1>
      <p className="entrada-deleite max-w-[28ch] text-sm text-on-surface-variant" style={{ animationDelay: '210ms' }}>
        La dirección que abriste no existe o cambió de lugar.
      </p>
      <Boton type="button" onClick={() => navigate('/')} className="entrada-deleite px-6" style={{ animationDelay: '280ms' }}>
        Volver al inicio
      </Boton>
    </main>
  )
}
