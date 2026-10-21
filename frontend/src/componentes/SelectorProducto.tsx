import { useEffect, useState } from 'react'
import { useProductos } from '../api/productos'
import { formatoCantidad, UNIDADES_CORTAS } from '../formato'
import type { Producto } from '../tipos'

/** Buscador para elegir un producto activo por nombre o código. */
export default function SelectorProducto({ onElegir }: { onElegir: (p: Producto) => void }) {
  const [texto, setTexto] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    const t = setTimeout(() => setQ(texto.trim()), 300)
    return () => clearTimeout(t)
  }, [texto])

  const { data: productos, isFetching } = useProductos({ q: q || undefined })
  const resultados = (productos ?? []).slice(0, 20)

  return (
    <div className="space-y-2">
      <input
        type="search"
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        placeholder="Buscar producto por nombre o código"
        aria-label="Buscar producto"
        autoFocus
        className="campo mt-0"
      />
      {productos && resultados.length === 0 ? (
        <p className="px-1 text-sm text-slate-500">No hay productos que coincidan.</p>
      ) : (
        <ul className={`divide-y divide-slate-100 rounded-lg border border-slate-200 ${isFetching ? 'opacity-70' : ''}`}>
          {resultados.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => onElegir(p)}
                className="flex min-h-11 w-full items-center gap-3 px-3 py-2 text-left hover:bg-slate-50"
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium text-slate-800">{p.nombre}</span>
                  <span className="block truncate text-sm text-slate-500">{p.codigo}</span>
                </span>
                <span className="text-sm text-slate-600 tabular-nums">
                  {formatoCantidad(p.stock)} {UNIDADES_CORTAS[p.unidad]}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
