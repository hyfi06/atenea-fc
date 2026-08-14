import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { MenuUsuario } from '../components/MenuUsuario'
import { IconTutorias } from '../components/icons/ServiceIcons'
import { services } from '../data/services'
import { useEsMiembroSAE } from '../auth/rol'

export function Home() {
  const navigate = useNavigate()
  const esMiembroSAE = useEsMiembroSAE()

  return (
    <main className="min-h-svh px-4 pb-8">
      <header className="flex items-center gap-2 py-4">
        <Logo className="h-7 w-7 text-primary" />
        <span className="text-base font-semibold">Atenea</span>
        <span className="flex-1" />
        <MenuUsuario />
      </header>

      <p className="pb-4 text-sm text-on-surface-variant">Hola</p>

      <div className="grid grid-cols-3 gap-3">
        {esMiembroSAE && (
          <button
            type="button"
            onClick={() => navigate('/sae/asesorias')}
            className="presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl bg-secondary-container p-3 text-center text-on-secondary-container"
          >
            <IconTutorias className="h-6 w-6" />
            <span className="text-xs font-semibold leading-tight">Asesorías · SAE</span>
          </button>
        )}
        {services.map(({ id, label, Icon, containerClassName, onContainerClassName }, indice) => (
          <div
            key={id}
            style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}
            className={`entrada-lista flex flex-col items-center gap-2 rounded-2xl p-3 text-center ${containerClassName} ${onContainerClassName}`}
          >
            <Icon className="h-6 w-6" />
            <span className="text-xs font-semibold leading-tight">{label}</span>
          </div>
        ))}
      </div>
    </main>
  )
}