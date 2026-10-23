import { Link } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useResumen } from '../api/resumen'
import ListaMovimientos from '../componentes/ListaMovimientos'
import { formatoCantidad, formatoDinero, nombreProducto, UNIDADES_CORTAS } from '../formato'

function Tarjeta({ titulo, valor, alerta = false }: { titulo: string; valor: string; alerta?: boolean }) {
  return (
    <div className={`tarjeta ${alerta ? 'bg-red-50 ring-1 ring-red-200' : ''}`}>
      <p className={`text-sm ${alerta ? 'text-red-800' : 'text-slate-500'}`}>{titulo}</p>
      <p className={`mt-1 text-xl font-bold tabular-nums ${alerta ? 'text-red-700' : 'text-slate-800'}`}>{valor}</p>
    </div>
  )
}

export default function Inicio() {
  const { data: usuario } = useUsuarioActual()
  const { data: resumen, error } = useResumen()

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Hola, {usuario?.nombre}</h1>

      <div className="grid grid-cols-2 gap-2">
        <Link to="/movimiento/entrada" className="boton min-h-20 bg-emerald-700 text-xl text-white hover:bg-emerald-800">
          + Entrada
        </Link>
        <Link to="/movimiento/salida" className="boton min-h-20 bg-amber-600 text-xl text-white hover:bg-amber-700">
          − Salida
        </Link>
      </div>

      {error ? (
        <p className="text-red-700">{error.message}</p>
      ) : !resumen ? (
        <p className="text-slate-500">Cargando…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            <Tarjeta titulo="Productos" valor={formatoCantidad(resumen.total_productos)} />
            <Tarjeta titulo="Bajo mínimo" valor={formatoCantidad(resumen.bajo_minimo.length)} alerta={resumen.bajo_minimo.length > 0} />
            <Tarjeta titulo="Valor a precio de compra" valor={formatoDinero(resumen.valor_compra)} />
            <Tarjeta titulo="Valor a precio de venta" valor={formatoDinero(resumen.valor_venta)} />
          </div>

          {resumen.bajo_minimo.length > 0 && (
            <div className="tarjeta">
              <h2 className="font-semibold text-red-800">Productos bajo mínimo</h2>
              <ul className="mt-2 divide-y divide-slate-100">
                {resumen.bajo_minimo.map((p) => {
                  const unidad = UNIDADES_CORTAS[p.unidad]
                  return (
                    <li key={p.id}>
                      <Link to={`/productos/${p.id}`} className="flex min-h-11 items-center gap-3 py-2 hover:bg-slate-50">
                        <span className="min-w-0 flex-1 truncate font-medium text-slate-800">{nombreProducto(p)}</span>
                        <span className="text-right text-sm tabular-nums">
                          <span className="font-semibold text-red-700">
                            {formatoCantidad(p.stock)} {unidad}
                          </span>
                          <span className="block text-slate-500">
                            mínimo {formatoCantidad(p.stock_minimo)} {unidad}
                          </span>
                        </span>
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}

          <div className="tarjeta">
            <h2 className="font-semibold text-slate-800">Últimos movimientos</h2>
            <ListaMovimientos movimientos={resumen.ultimos_movimientos} mostrarProducto />
          </div>
        </>
      )}
    </section>
  )
}
