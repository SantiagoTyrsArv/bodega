import { useState } from 'react'
import { Navigate } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useCategorias, useGuardarCategoria } from '../api/categorias'
import { useGuardarUsuario, useUsuarios } from '../api/usuarios'
import FormUsuario from '../componentes/FormUsuario'
import type { Categoria, Usuario } from '../tipos'

function FilaCategoria({ categoria }: { categoria: Categoria }) {
  const guardar = useGuardarCategoria()
  const [nombre, setNombre] = useState(categoria.nombre)
  const cambiado = nombre.trim() !== categoria.nombre

  return (
    <li className="py-2">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          guardar.mutate({ id: categoria.id, nombre: nombre.trim() })
        }}
        className="flex gap-2"
      >
        <input
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          aria-label={`Nombre de la categoría ${categoria.nombre}`}
          className="campo mt-0"
        />
        {cambiado && (
          <button type="submit" disabled={guardar.isPending || !nombre.trim()} className="boton-primario">
            Guardar
          </button>
        )}
      </form>
      {guardar.error && <p className="error-campo">{guardar.error.message}</p>}
    </li>
  )
}

function Categorias() {
  const { data: categorias, isPending, error } = useCategorias()
  const crear = useGuardarCategoria()
  const [nombre, setNombre] = useState('')

  return (
    <div className="tarjeta space-y-3">
      <h2 className="text-lg font-semibold text-slate-800">Categorías</h2>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          crear.mutate({ nombre: nombre.trim() }, { onSuccess: () => setNombre('') })
        }}
        className="flex gap-2"
      >
        <input
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Nueva categoría"
          aria-label="Nueva categoría"
          className="campo mt-0"
        />
        <button type="submit" disabled={crear.isPending || !nombre.trim()} className="boton-primario">
          Agregar
        </button>
      </form>
      {crear.error && <p className="error-campo">{crear.error.message}</p>}

      {isPending ? (
        <p className="text-slate-500">Cargando…</p>
      ) : error ? (
        <p className="text-red-700">{error.message}</p>
      ) : categorias.length === 0 ? (
        <p className="text-sm text-slate-500">Todavía no hay categorías.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {categorias.map((c) => (
            // key con el nombre: si cambia desde el servidor, la fila se reinicia
            <FilaCategoria key={`${c.id}-${c.nombre}`} categoria={c} />
          ))}
        </ul>
      )}
    </div>
  )
}

function FilaUsuario({ usuario, esYo }: { usuario: Usuario; esYo: boolean }) {
  const guardar = useGuardarUsuario()
  const [editando, setEditando] = useState(false)

  if (editando) {
    return (
      <li className="py-3">
        <FormUsuario
          usuario={usuario}
          esYo={esYo}
          pendiente={guardar.isPending}
          error={guardar.error}
          onEnviar={(datos) => guardar.mutate({ id: usuario.id, ...datos }, { onSuccess: () => setEditando(false) })}
          onCancelar={() => {
            guardar.reset()
            setEditando(false)
          }}
        />
      </li>
    )
  }

  return (
    <li className={`py-3 ${usuario.activo ? '' : 'opacity-60'}`}>
      <div className="flex flex-wrap items-center gap-2">
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-800">
            {usuario.nombre}
            {esYo && <span className="ml-1 text-sm font-normal text-slate-500">(tú)</span>}
            {usuario.rol === 'ADMIN' && (
              <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800">Admin</span>
            )}
            {!usuario.activo && (
              <span className="ml-2 rounded bg-slate-200 px-1.5 py-0.5 text-xs font-medium text-slate-700">Desactivado</span>
            )}
          </p>
          <p className="truncate text-sm text-slate-500">{usuario.correo}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setEditando(true)} className="boton-secundario text-sm">
            Editar
          </button>
          {!esYo && (
            <button
              onClick={() => guardar.mutate({ id: usuario.id, activo: !usuario.activo })}
              disabled={guardar.isPending}
              className="boton-secundario text-sm"
            >
              {usuario.activo ? 'Desactivar' : 'Reactivar'}
            </button>
          )}
        </div>
      </div>
      {guardar.error && <p className="error-campo">{guardar.error.message}</p>}
    </li>
  )
}

function Usuarios({ yo }: { yo: Usuario }) {
  const { data: usuarios, isPending, error } = useUsuarios()
  const crear = useGuardarUsuario()
  const [creando, setCreando] = useState(false)

  return (
    <div className="tarjeta space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-800">Usuarios</h2>
        {!creando && (
          <button onClick={() => setCreando(true)} className="boton-primario">
            + Nuevo
          </button>
        )}
      </div>

      {creando && (
        <div className="rounded-lg border border-slate-200 p-3">
          <FormUsuario
            pendiente={crear.isPending}
            error={crear.error}
            onEnviar={(datos) => crear.mutate(datos, { onSuccess: () => setCreando(false) })}
            onCancelar={() => {
              crear.reset()
              setCreando(false)
            }}
          />
        </div>
      )}

      {isPending ? (
        <p className="text-slate-500">Cargando…</p>
      ) : error ? (
        <p className="text-red-700">{error.message}</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {usuarios.map((u) => (
            <FilaUsuario key={u.id} usuario={u} esYo={u.id === yo.id} />
          ))}
        </ul>
      )}
    </div>
  )
}

export default function Ajustes() {
  const { data: usuario } = useUsuarioActual()
  if (!usuario || usuario.rol !== 'ADMIN') return <Navigate to="/" replace />

  return (
    <section className="mx-auto max-w-lg space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Ajustes</h1>
      <Usuarios yo={usuario} />
      <Categorias />
    </section>
  )
}
