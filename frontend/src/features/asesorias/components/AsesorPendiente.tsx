import { useNavigate } from 'react-router-dom'

/** Pantalla de "tu perfil de asesor está pendiente de revisión de la SAE".
 *  Reemplaza Mis materias / Mi horario mientras `activo` sea false. */
export function AsesorPendiente({ titulo }: { titulo: string }) {
  const navigate = useNavigate()
  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>
      <p role="status" className="entrada-lista max-w-prose rounded-lg bg-secondary-container px-3 py-2 text-sm text-on-secondary-container">
        Tu perfil de asesor está pendiente de que la SAE confirme tu
        nombramiento. Podrás registrar materias y disponibilidad en cuanto
        quede aprobado.
      </p>
    </main>
  )
}
