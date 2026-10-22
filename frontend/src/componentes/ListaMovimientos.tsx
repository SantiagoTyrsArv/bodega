import { useState } from 'react'
import { formatoCantidad, formatoDinero, formatoFecha, nombreProducto, UNIDADES_CORTAS } from '../formato'
import { TEXTO_MOTIVO } from '../inventario'
import type { Movimiento } from '../tipos'

interface Props {
  movimientos: Movimiento[]
  mostrarProducto?: boolean
  // Solo para ADMIN: muestra "Anular" en los movimientos que se pueden anular
  onAnular?: (m: Movimiento) => void
  anulandoId?: number | null
}

/** Lista de movimientos, del más reciente al más antiguo. */
export default function ListaMovimientos({ movimientos, mostrarProducto = false, onAnular, anulandoId = null }: Props) {
  // Movimiento que espera confirmación para anularse
  const [confirmando, setConfirmando] = useState<number | null>(null)

  if (movimientos.length === 0) {
    return <p className="text-sm text-slate-500">Todavía no hay movimientos.</p>
  }

  return (
    <ul className="divide-y divide-slate-100">
      {movimientos.map((m) => {
        const entrada = m.tipo === 'ENTRADA'
        const unidad = UNIDADES_CORTAS[m.producto.unidad]
        const anulado = m.anulado_por !== null
        const anulable = onAnular && !anulado && m.motivo !== 'ANULACION'
        return (
          <li key={m.id} className={`flex flex-wrap gap-3 py-3 ${anulado ? 'opacity-60' : ''}`}>
            <span
              aria-hidden
              className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full text-lg font-bold ${entrada ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}
            >
              {entrada ? '+' : '−'}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-slate-800">
                {mostrarProducto && <span>{nombreProducto(m.producto)} · </span>}
                <span className={anulado ? 'line-through' : ''}>
                  {entrada ? 'Entrada' : 'Salida'} · {TEXTO_MOTIVO[m.motivo]}
                </span>
                {anulado && <span className="ml-2 rounded bg-slate-200 px-1.5 text-xs font-medium text-slate-700">Anulado</span>}
                {m.anula_a && <span className="ml-2 text-xs text-slate-500">(anula el movimiento #{m.anula_a})</span>}
              </p>
              <p className="text-sm text-slate-500">
                {formatoFecha(m.fecha)} · {m.usuario.nombre} · #{m.id}
              </p>
              {(m.responsable || m.pedido) && (
                <p className="text-sm text-slate-600">
                  {[m.responsable, m.pedido && `Pedido ${m.pedido}`].filter(Boolean).join(' · ')}
                </p>
              )}
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
            {anulable && (
              <div className="flex w-full justify-end gap-2 pl-11">
                {confirmando === m.id ? (
                  <>
                    <span className="self-center text-sm text-slate-700">¿Anular este movimiento?</span>
                    <button onClick={() => setConfirmando(null)} className="boton-secundario min-h-11 text-sm">
                      No
                    </button>
                    <button
                      onClick={() => {
                        setConfirmando(null)
                        onAnular(m)
                      }}
                      className="boton min-h-11 bg-red-700 text-sm whitespace-nowrap text-white hover:bg-red-800"
                    >
                      Sí, anular
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setConfirmando(m.id)}
                    disabled={anulandoId !== null}
                    className="boton-secundario min-h-11 text-sm text-red-700"
                  >
                    {anulandoId === m.id ? 'Anulando…' : 'Anular'}
                  </button>
                )}
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}
