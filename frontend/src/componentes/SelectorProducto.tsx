import { useEffect, useState } from 'react'
import { useBuscarCodigo, useProductos } from '../api/productos'
import { formatoCantidad, UNIDADES_CORTAS } from '../formato'
import type { Producto } from '../tipos'
import Buscador, { AvisoCodigoNuevo } from './Buscador'

/** Buscador para elegir un producto activo por nombre o código, escribiendo o escaneando. */
export default function SelectorProducto({ onElegir }: { onElegir: (p: Producto) => void }) {
  const [texto, setTexto] = useState('')
  const [q, setQ] = useState('')
  const codigo = useBuscarCodigo(onElegir)

  useEffect(() => {
    const t = setTimeout(() => setQ(texto.trim()), 300)
    return () => clearTimeout(t)
  }, [texto])

  const { data: productos, isFetching } = useProductos({ q: q || undefined })
  const resultados = (productos ?? []).slice(0, 20)
  // El aviso solo se muestra mientras el campo tenga el código que no se encontró
  const mostrarAviso = codigo.noEncontrado !== '' && codigo.noEncontrado === texto.trim()

  return (
    <div className="space-y-2">
      <Buscador
        valor={texto}
        onCambiar={setTexto}
        onCodigo={(c) => {
          setQ(c)
          codigo.buscar(c)
        }}
        placeholder="Buscar producto por nombre o código"
        autoFocus
      />
      {codigo.error && <p className="px-1 text-sm text-red-700">{codigo.error}</p>}
      {mostrarAviso && resultados.length === 0 ? (
        <AvisoCodigoNuevo codigo={codigo.noEncontrado} />
      ) : productos && resultados.length === 0 ? (
        <p className="px-1 text-sm text-slate-500">No hay productos que coincidan.</p>
      ) : (
        <ul className={`divide-y divide-slate-100 rounded-lg border border-slate-200 ${isFetching || codigo.pendiente ? 'opacity-70' : ''}`}>
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
