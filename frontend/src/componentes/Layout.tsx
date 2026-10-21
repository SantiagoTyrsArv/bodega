import { Navigate, Outlet, useLocation } from 'react-router'
import { useLogout, useUsuarioActual } from '../api/auth'

/** Estructura de las páginas con sesión. Sin sesión, redirige al login. */
export default function Layout() {
  const { data: usuario, isPending, error } = useUsuarioActual()
  const logout = useLogout()
  const ubicacion = useLocation()

  if (isPending) {
    return <p className="p-6 text-center text-slate-500">Cargando…</p>
  }
  if (error) {
    return <p className="p-6 text-center text-red-700">{error.message}</p>
  }
  if (!usuario) {
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between gap-3 bg-white px-4 py-2 shadow-sm">
        <span className="text-lg font-bold tracking-tight text-slate-800">BODEGA</span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-600">
            {usuario.nombre}
            {usuario.rol === 'ADMIN' && (
              <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800">
                Admin
              </span>
            )}
          </span>
          <button
            onClick={() => logout.mutate()}
            className="min-h-11 rounded-lg px-3 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Salir
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl p-4">
        <Outlet />
      </main>
    </div>
  )
}
