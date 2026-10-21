import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useEditarProducto, useProducto } from '../api/productos'
import FormProducto from '../componentes/FormProducto'
import { estaBajoMinimo, formatoCantidad, formatoDinero, UNIDADES, UNIDADES_CORTAS } from '../formato'

function Dato({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-sm text-slate-500">{titulo}</dt>
      <dd className="font-medium text-slate-800">{children}</dd>
    </div>
  )
}

export default function ProductoDetalle() {
  const id = Number(useParams().id)
  const { data: usuario } = useUsuarioActual()
  const esAdmin = usuario?.rol === 'ADMIN'
  const { data: producto, isPending, error } = useProducto(id)
  const editar = useEditarProducto(id)
  const [editando, setEditando] = useState(false)

  if (isPending) return <p className="text-slate-500">Cargando…</p>
  if (error) return <p className="text-red-700">{error.message}</p>

  const bajo = estaBajoMinimo(producto)
  const unidad = UNIDADES_CORTAS[producto.unidad]

  return (
    <section className="mx-auto max-w-lg space-y-4">
      <Link to="/productos" className="text-sm text-slate-600 hover:underline">
        ← Productos
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-slate-800">{producto.nombre}</h1>
        <p className="text-slate-500">{producto.codigo}</p>
        {!producto.activo && (
          <p className="mt-2 inline-block rounded bg-slate-200 px-2 py-0.5 text-sm font-medium text-slate-700">
            Desactivado
          </p>
        )}
      </div>

      {editando ? (
        <div className="tarjeta">
          <FormProducto
            producto={producto}
            textoBoton="Guardar cambios"
            pendiente={editar.isPending}
            error={editar.error}
            onEnviar={(datos) => editar.mutate(datos, { onSuccess: () => setEditando(false) })}
            onCancelar={() => {
              editar.reset()
              setEditando(false)
            }}
          />
        </div>
      ) : (
        <>
          <div className={`tarjeta ${bajo ? 'ring-2 ring-red-200' : ''}`}>
            <p className="text-sm text-slate-500">Stock actual</p>
            <p className={`text-4xl font-bold tabular-nums ${bajo ? 'text-red-700' : 'text-slate-800'}`}>
              {formatoCantidad(producto.stock)} <span className="text-xl font-semibold">{unidad}</span>
            </p>
            <p className={`mt-1 text-sm ${bajo ? 'font-medium text-red-700' : 'text-slate-500'}`}>
              {bajo ? 'Bajo el mínimo · ' : ''}Mínimo: {formatoCantidad(producto.stock_minimo)} {unidad}
            </p>
          </div>

          <dl className="tarjeta grid grid-cols-2 gap-4">
            <Dato titulo="Precio de compra">{formatoDinero(producto.precio_compra)}</Dato>
            <Dato titulo="Precio de venta">{formatoDinero(producto.precio_venta)}</Dato>
            <Dato titulo="Categoría">{producto.categoria?.nombre ?? 'Sin categoría'}</Dato>
            <Dato titulo="Unidad">{UNIDADES[producto.unidad]}</Dato>
            {producto.nota && (
              <div className="col-span-2">
                <Dato titulo="Nota">{producto.nota}</Dato>
              </div>
            )}
          </dl>

          {esAdmin && (
            <div className="flex flex-col gap-2 sm:flex-row">
              <button onClick={() => setEditando(true)} className="boton-secundario sm:flex-1">
                Editar
              </button>
              <button
                onClick={() => editar.mutate({ activo: !producto.activo })}
                disabled={editar.isPending}
                className="boton-secundario sm:flex-1"
              >
                {producto.activo ? 'Desactivar' : 'Reactivar'}
              </button>
            </div>
          )}
          {editar.error && <p className="text-sm text-red-700">{editar.error.message}</p>}
        </>
      )}
    </section>
  )
}
