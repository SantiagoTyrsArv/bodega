import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router'
import { z } from 'zod'
import { useLogin, useUsuarioActual } from '../api/auth'

const esquema = z.object({
  // Mismo criterio que el backend: un correo que la API acepta debe poder ingresar
  correo: z.string().trim().regex(/^[^@\s]+@[^@\s]+$/, 'Escribe un correo válido'),
  clave: z.string().min(1, 'Escribe tu clave'),
})

type Datos = z.infer<typeof esquema>

export default function Login() {
  const { data: usuario } = useUsuarioActual()
  const login = useLogin()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  // Vuelve a la página que se intentó abrir antes de iniciar sesión
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? '/'

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Datos>({ resolver: zodResolver(esquema) })

  if (usuario) return <Navigate to={destino} replace />

  const enviar = (datos: Datos) =>
    login.mutate(datos, { onSuccess: () => navegar(destino, { replace: true }) })

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form
        onSubmit={handleSubmit(enviar)}
        noValidate
        className="w-full max-w-sm space-y-5 rounded-2xl bg-white p-6 shadow-sm"
      >
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-800">BODEGA</h1>
          <p className="mt-1 text-sm text-slate-500">Ingresa para continuar</p>
        </div>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Correo</span>
          <input
            type="email"
            autoComplete="username"
            autoFocus
            {...register('correo')}
            className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 px-3 text-base focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
          />
          {errors.correo && <span className="mt-1 block text-sm text-red-700">{errors.correo.message}</span>}
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Clave</span>
          <input
            type="password"
            autoComplete="current-password"
            {...register('clave')}
            className="mt-1 block min-h-11 w-full rounded-lg border border-slate-300 px-3 text-base focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
          />
          {errors.clave && <span className="mt-1 block text-sm text-red-700">{errors.clave.message}</span>}
        </label>

        {login.error && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
            {login.error.message}
          </p>
        )}

        <button
          type="submit"
          disabled={login.isPending}
          className="min-h-11 w-full rounded-lg bg-emerald-700 font-semibold text-white hover:bg-emerald-800 disabled:opacity-60"
        >
          {login.isPending ? 'Ingresando…' : 'Ingresar'}
        </button>
      </form>
    </main>
  )
}
