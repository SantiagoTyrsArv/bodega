import { NavLink, Navigate, Outlet, useLocation } from 'react-router'
import { useLogout, useUsuarioActual } from '../api/auth'

interface Enlace {
  a: string
  texto: string
  icono: string // path de un SVG de 24x24
  soloAdmin?: boolean
}

const ENLACES: Enlace[] = [
  { a: '/', texto: 'Inicio', icono: 'M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10' },
  { a: '/productos', texto: 'Productos', icono: 'M3 7l9-4 9 4-9 4-9-4zm0 0v10l9 4 9-4V7M12 11v10' },
  { a: '/historial', texto: 'Historial', icono: 'M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0' },
  {
    a: '/ajustes',
    texto: 'Ajustes',
    icono: 'M4 6h16M4 12h16M4 18h16M8 4v4M16 10v4M10 16v4',
    soloAdmin: true,
  },
]

function Icono({ d }: { d: string }) {
  return (
    <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  )
}

/** Estructura de las páginas con sesión. Sin sesión, redirige al login. */
export default function Layout() {
  const { data: usuario, isPending, error, refetch, isFetching } = useUsuarioActual()
  const logout = useLogout()
  const ubicacion = useLocation()

  if (isPending) {
    return <p className="p-6 text-center text-slate-500">Cargando…</p>
  }
  if (error) {
    return (
      <div className="space-y-3 p-6 text-center">
        <p className="text-red-700">{error.message}</p>
        <button onClick={() => refetch()} disabled={isFetching} className="boton-secundario">
          {isFetching ? 'Reintentando…' : 'Reintentar'}
        </button>
      </div>
    )
  }
  if (!usuario) {
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  }

  const enlaces = ENLACES.filter((e) => !e.soloAdmin || usuario.rol === 'ADMIN')
  const claseEnlace = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'text-emerald-700' : 'text-slate-500 hover:text-slate-800'

  return (
    <div className="min-h-screen bg-slate-100 md:pl-56">
      {/* Lateral en pantallas anchas */}
      <nav className="fixed inset-y-0 left-0 hidden w-56 flex-col gap-1 border-r border-slate-200 bg-white p-3 md:flex">
        <span className="px-3 py-3 text-xl font-bold tracking-tight text-slate-800">BODEGA</span>
        {enlaces.map((e) => (
          <NavLink
            key={e.a}
            to={e.a}
            end={e.a === '/'}
            className={(estado) =>
              `flex min-h-11 items-center gap-3 rounded-lg px-3 font-medium ${claseEnlace(estado)} ${estado.isActive ? 'bg-emerald-50' : ''}`
            }
          >
            <Icono d={e.icono} />
            {e.texto}
          </NavLink>
        ))}
      </nav>

      <header className="sticky top-0 z-10 flex items-center justify-between gap-3 bg-white px-4 py-1 shadow-sm">
        <span className="text-lg font-bold tracking-tight text-slate-800 md:invisible">BODEGA</span>
        <div className="flex items-center gap-2">
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

      {/* pb-24: espacio para la navegación inferior en celular */}
      <main className="mx-auto max-w-5xl p-4 pb-24 md:pb-8">
        <Outlet />
      </main>

      {/* Inferior en celular */}
      <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] md:hidden">
        {enlaces.map((e) => (
          <NavLink
            key={e.a}
            to={e.a}
            end={e.a === '/'}
            className={(estado) =>
              `flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-xs font-medium ${claseEnlace(estado)}`
            }
          >
            <Icono d={e.icono} />
            {e.texto}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
