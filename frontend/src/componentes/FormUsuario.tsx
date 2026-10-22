import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import type { UsuarioDatos } from '../api/usuarios'
import type { Usuario } from '../tipos'

const CLAVE_MINIMA = 8

const esquema = (esNuevo: boolean) =>
  z.object({
    nombre: z.string().trim().min(1, 'Escribe el nombre'),
    correo: z.string().trim().toLowerCase().pipe(z.email('Escribe un correo válido')),
    // Al editar, la clave vacía significa "no cambiarla"
    clave: esNuevo
      ? z.string().min(CLAVE_MINIMA, `Mínimo ${CLAVE_MINIMA} caracteres`)
      : z.string().refine((s) => s === '' || s.length >= CLAVE_MINIMA, `Mínimo ${CLAVE_MINIMA} caracteres`),
    rol: z.enum(['ADMIN', 'USUARIO']),
  })

type Datos = z.infer<ReturnType<typeof esquema>>

interface Props {
  usuario?: Usuario
  // Quien edita su propio usuario no puede cambiarse el rol
  esYo?: boolean
  pendiente: boolean
  error: Error | null
  onEnviar: (datos: UsuarioDatos) => void
  onCancelar: () => void
}

export default function FormUsuario({ usuario, esYo = false, pendiente, error, onEnviar, onCancelar }: Props) {
  const esNuevo = !usuario
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Datos>({
    resolver: zodResolver(esquema(esNuevo)),
    defaultValues: {
      nombre: usuario?.nombre ?? '',
      correo: usuario?.correo ?? '',
      clave: '',
      rol: usuario?.rol ?? 'USUARIO',
    },
  })

  const enviar = ({ clave, rol, ...resto }: Datos) =>
    onEnviar({ ...resto, ...(clave ? { clave } : {}), ...(esYo ? {} : { rol }) })

  return (
    <form onSubmit={handleSubmit(enviar)} noValidate className="space-y-3">
      <label className="block">
        <span className="etiqueta">Nombre</span>
        <input {...register('nombre')} autoComplete="off" className="campo" />
        {errors.nombre && <span className="error-campo">{errors.nombre.message}</span>}
      </label>
      <label className="block">
        <span className="etiqueta">Correo</span>
        <input {...register('correo')} type="email" autoComplete="off" className="campo" />
        {errors.correo && <span className="error-campo">{errors.correo.message}</span>}
      </label>
      <label className="block">
        <span className="etiqueta">{esNuevo ? 'Clave' : 'Clave nueva (vacía para no cambiarla)'}</span>
        <input {...register('clave')} type="password" autoComplete="new-password" className="campo" />
        {errors.clave && <span className="error-campo">{errors.clave.message}</span>}
      </label>
      <label className="block">
        <span className="etiqueta">Rol</span>
        <select {...register('rol')} disabled={esYo} className="campo disabled:bg-slate-100">
          <option value="USUARIO">Usuario: ve todo y registra entradas y salidas</option>
          <option value="ADMIN">Administrador: además gestiona productos, precios y usuarios</option>
        </select>
        {esYo && <span className="mt-1 block text-sm text-slate-500">No puedes cambiar tu propio rol.</span>}
      </label>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          {error.message}
        </p>
      )}
      <div className="flex gap-2">
        <button type="button" onClick={onCancelar} className="boton-secundario flex-1">
          Cancelar
        </button>
        <button type="submit" disabled={pendiente} className="boton-primario flex-1">
          {pendiente ? 'Guardando…' : esNuevo ? 'Crear usuario' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}
