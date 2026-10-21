import { useState } from 'react'
import { Navigate } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useCategorias, useGuardarCategoria } from '../api/categorias'
import type { Categoria } from '../tipos'

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

export default function Ajustes() {
  const { data: usuario } = useUsuarioActual()
  if (usuario?.rol !== 'ADMIN') return <Navigate to="/" replace />

  return (
    <section className="mx-auto max-w-lg space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Ajustes</h1>
      <Categorias />
    </section>
  )
}
