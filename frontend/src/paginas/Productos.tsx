import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useCategorias } from '../api/categorias'
import { useProductos } from '../api/productos'
import { estaBajoMinimo, formatoCantidad, formatoDinero, UNIDADES_CORTAS } from '../formato'

export default function Productos() {
  const { data: usuario } = useUsuarioActual()
  const esAdmin = usuario?.rol === 'ADMIN'
  const { data: categorias = [] } = useCategorias()

  const [texto, setTexto] = useState('')
  const [q, setQ] = useState('')
  const [categoriaId, setCategoriaId] = useState('')
  const [verInactivos, setVerInactivos] = useState(false)

  // Espera a que se deje de escribir antes de buscar
  useEffect(() => {
    const t = setTimeout(() => setQ(texto.trim()), 300)
    return () => clearTimeout(t)
  }, [texto])

  const { data: productos, isPending, error, isFetching } = useProductos({
    q: q || undefined,
    categoria_id: categoriaId ? Number(categoriaId) : undefined,
    activo: !verInactivos,
  })

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Productos</h1>
        {esAdmin && (
          <Link to="/productos/nuevo" className="boton-primario">
            + Nuevo
          </Link>
        )}
      </div>

      <div className="grid gap-2 sm:grid-cols-[1fr_14rem]">
        <input
          type="search"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Buscar por nombre o código"
          aria-label="Buscar productos"
          className="campo mt-0"
        />
        <select
          value={categoriaId}
          onChange={(e) => setCategoriaId(e.target.value)}
          aria-label="Filtrar por categoría"
          className="campo mt-0"
        >
          <option value="">Todas las categorías</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
      </div>

      {esAdmin && (
        <label className="flex min-h-11 items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={verInactivos}
            onChange={(e) => setVerInactivos(e.target.checked)}
            className="size-5"
          />
          Ver productos desactivados
        </label>
      )}

      {isPending ? (
        <p className="text-slate-500">Cargando…</p>
      ) : error ? (
        <p className="text-red-700">{error.message}</p>
      ) : productos.length === 0 ? (
        <p className="tarjeta text-center text-slate-500">
          {q || categoriaId ? 'No hay productos que coincidan.' : 'Todavía no hay productos.'}
        </p>
      ) : (
        <ul className={`divide-y divide-slate-100 overflow-hidden rounded-xl bg-white shadow-sm ${isFetching ? 'opacity-70' : ''}`}>
          {productos.map((p) => {
            const bajo = estaBajoMinimo(p)
            return (
              <li key={p.id}>
                <Link to={`/productos/${p.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-slate-800">{p.nombre}</p>
                    <p className="truncate text-sm text-slate-500">
                      {p.codigo}
                      {p.categoria && ` · ${p.categoria.nombre}`}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold tabular-nums ${bajo ? 'text-red-700' : 'text-slate-800'}`}>
                      {bajo && <span className="sr-only">Bajo mínimo: </span>}
                      {formatoCantidad(p.stock)} {UNIDADES_CORTAS[p.unidad]}
                    </p>
                    <p className="text-sm text-slate-500 tabular-nums">{formatoDinero(p.precio_venta)}</p>
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
