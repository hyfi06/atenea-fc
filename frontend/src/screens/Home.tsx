import { Logo } from '../components/Logo'
import { services } from '../data/services'

export function Home() {
  return (
    <main className="min-h-svh px-4 pb-8">
      <header className="flex items-center gap-2 py-4">
        <Logo className="h-7 w-7 text-primary" />
        <span className="text-base font-semibold">Atenea</span>
        <span className="flex-1" />
        <button type="button" aria-label="Menú" className="flex h-9 w-9 items-center justify-center text-on-background">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="h-5 w-5">
            <line x1="4" y1="7" x2="20" y2="7" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="17" x2="20" y2="17" />
          </svg>
        </button>
      </header>

      <p className="pb-4 text-sm text-on-surface-variant">Hola</p>

      <div className="grid grid-cols-3 gap-3">
        {services.map(({ id, label, Icon, containerClassName, onContainerClassName }) => (
          <div
            key={id}
            className={`flex flex-col items-center gap-2 rounded-2xl p-3 text-center ${containerClassName} ${onContainerClassName}`}
          >
            <Icon className="h-6 w-6" />
            <span className="text-xs font-semibold leading-tight">{label}</span>
          </div>
        ))}
      </div>
    </main>
  )
}
