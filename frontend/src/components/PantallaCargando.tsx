/**
 * Spinner de página completa mientras se resuelve el estado de la sesión.
 *
 * Vivía como función local en `auth/RutaProtegida.tsx`; se extrajo al ganar
 * consumidores fuera de las guardas (`Landing` y `Login` también esperan a
 * que `status` deje de ser 'loading'). Un solo markup para los cinco.
 */
export function PantallaCargando() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="spinner h-6 w-6 text-primary" aria-label="Cargando" />
    </div>
  )
}
