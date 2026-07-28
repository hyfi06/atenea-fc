import { useEffect, useState } from 'react'
import { getHealth } from '../api/health'

type Status =
  | { kind: 'loading' }
  | { kind: 'success'; message: string }
  | { kind: 'error'; message: string }

export function HealthCheck() {
  const [status, setStatus] = useState<Status>({ kind: 'loading' })

  useEffect(() => {
    getHealth()
      .then((data) => setStatus({ kind: 'success', message: data.status }))
      .catch((error: unknown) =>
        setStatus({
          kind: 'error',
          message: error instanceof Error ? error.message : 'Error desconocido',
        }),
      )
  }, [])

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-medium">Atenea</h1>
      {status.kind === 'loading' && <p className="text-gray-500">Conectando con el backend…</p>}
      {status.kind === 'success' && (
        <p className="text-green-600">Backend conectado: {status.message}</p>
      )}
      {status.kind === 'error' && <p className="text-red-600">Error: {status.message}</p>}
    </main>
  )
}
