import { formatoCantidad, formatoDinero, formatoFecha, UNIDADES_CORTAS } from '../formato'
import { TEXTO_MOTIVO } from '../inventario'
import type { Movimiento } from '../tipos'

interface Props {
  movimientos: Movimiento[]
  mostrarProducto?: boolean
}

/** Lista de movimientos, del más reciente al más antiguo. */
export default function ListaMovimientos({ movimientos, mostrarProducto = false }: Props) {
  if (movimientos.length === 0) {
    return <p className="text-sm text-slate-500">Todavía no hay movimientos.</p>
  }

  return (
    <ul className="divide-y divide-slate-100">
      {movimientos.map((m) => {
        const entrada = m.tipo === 'ENTRADA'
        const unidad = UNIDADES_CORTAS[m.producto.unidad]
        const anulado = m.anulado_por !== null
        return (
          <li key={m.id} className={`flex gap-3 py-3 ${anulado ? 'opacity-60' : ''}`}>
            <span
              aria-hidden
              className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full text-lg font-bold ${entrada ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}
            >
              {entrada ? '+' : '−'}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-slate-800">
                {mostrarProducto && <span>{m.producto.nombre} · </span>}
                <span className={anulado ? 'line-through' : ''}>
                  {entrada ? 'Entrada' : 'Salida'} · {TEXTO_MOTIVO[m.motivo]}
                </span>
                {anulado && <span className="ml-2 rounded bg-slate-200 px-1.5 text-xs font-medium text-slate-700">Anulado</span>}
                {m.anula_a && <span className="ml-2 text-xs text-slate-500">(anula el movimiento #{m.anula_a})</span>}
              </p>
              <p className="text-sm text-slate-500">
                {formatoFecha(m.fecha)} · {m.usuario.nombre} · #{m.id}
              </p>
              {m.comentario && <p className="text-sm text-slate-600">“{m.comentario}”</p>}
            </div>
            <div className="text-right">
              <p className={`font-semibold tabular-nums ${entrada ? 'text-emerald-700' : 'text-amber-700'}`}>
                {entrada ? '+' : '−'}
                {formatoCantidad(m.cantidad)} {unidad}
              </p>
              <p className="text-xs text-slate-500 tabular-nums">a {formatoDinero(m.precio_unitario)}</p>
              <p className="text-xs text-slate-500 tabular-nums">
                Queda {formatoCantidad(m.stock_despues)} {unidad}
              </p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
