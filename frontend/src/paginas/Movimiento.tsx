import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, Navigate, useParams, useSearchParams } from 'react-router'
import { z } from 'zod'
import { useUsuarioActual } from '../api/auth'
import { useRegistrarMovimiento } from '../api/movimientos'
import { useProducto } from '../api/productos'
import SelectorProducto from '../componentes/SelectorProducto'
import { formatoCantidad, formatoDinero, UNIDADES_CORTAS } from '../formato'
import { MOTIVOS, stockResultante } from '../inventario'
import type { Motivo, Movimiento as TipoMov, Producto, TipoMovimiento } from '../tipos'

const RUTA_A_TIPO: Record<string, TipoMovimiento> = { entrada: 'ENTRADA', salida: 'SALIDA' }

const esquema = z.object({
  cantidad: z
    .string()
    .trim()
    .transform((s) => s.replace(',', '.'))
    .pipe(
      z
        .string()
        .regex(/^\d{1,9}(\.\d{1,3})?$/, 'Cantidad inválida (máximo 3 decimales)')
        .refine((s) => Number(s) > 0, 'La cantidad debe ser mayor que 0'),
    ),
  precio_unitario: z
    .string()
    .trim()
    .transform((s) => s.replace(',', '.'))
    .pipe(z.string().regex(/^\d{1,10}(\.\d{1,2})?$/, 'Precio inválido (máximo 2 decimales)')),
  motivo: z.string(),
  comentario: z.string().trim(),
  actualizar_precio: z.boolean(),
})

type Entrada = z.input<typeof esquema>
type Salida = z.output<typeof esquema>

function Formulario({
  producto,
  tipo,
  onListo,
  onCambiarProducto,
}: {
  producto: Producto
  tipo: TipoMovimiento
  onListo: (m: TipoMov) => void
  onCambiarProducto: () => void
}) {
  const { data: usuario } = useUsuarioActual()
  const registrar = useRegistrarMovimiento()
  const esEntrada = tipo === 'ENTRADA'
  const unidad = UNIDADES_CORTAS[producto.unidad]

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<Entrada, unknown, Salida>({
    resolver: zodResolver(esquema),
    defaultValues: {
      cantidad: '',
      precio_unitario: esEntrada ? producto.precio_compra : producto.precio_venta,
      motivo: MOTIVOS[tipo][0].valor,
      comentario: '',
      actualizar_precio: false,
    },
  })

  const cantidad = useWatch({ control, name: 'cantidad' })
  const resultante = stockResultante(producto.stock, tipo, cantidad)
  const sinStock = resultante !== null && resultante < 0

  const enviar = (d: Salida) =>
    registrar.mutate(
      {
        producto_id: producto.id,
        tipo,
        motivo: d.motivo as Motivo,
        cantidad: d.cantidad,
        precio_unitario: d.precio_unitario,
        comentario: d.comentario || null,
        actualizar_precio: esEntrada && d.actualizar_precio,
      },
      { onSuccess: onListo },
    )

  return (
    <form onSubmit={handleSubmit(enviar)} noValidate className="space-y-4">
      <div className="flex items-start justify-between gap-3 rounded-lg bg-slate-50 p-3">
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-800">{producto.nombre}</p>
          <p className="truncate text-sm text-slate-500">{producto.codigo}</p>
          <p className="text-sm text-slate-600">
            Stock actual: <span className="font-medium tabular-nums">{formatoCantidad(producto.stock)} {unidad}</span>
          </p>
        </div>
        <button type="button" onClick={onCambiarProducto} className="min-h-11 shrink-0 px-2 text-sm font-medium text-emerald-700 hover:underline">
          Cambiar
        </button>
      </div>

      <label className="block">
        <span className="etiqueta">Cantidad ({unidad})</span>
        <input {...register('cantidad')} inputMode="decimal" autoComplete="off" autoFocus className="campo text-lg" />
        {errors.cantidad && <span className="error-campo">{errors.cantidad.message}</span>}
      </label>

      <label className="block">
        <span className="etiqueta">{esEntrada ? 'Precio de compra unitario' : 'Precio de venta unitario'}</span>
        <input {...register('precio_unitario')} inputMode="decimal" autoComplete="off" className="campo" />
        {errors.precio_unitario && <span className="error-campo">{errors.precio_unitario.message}</span>}
      </label>

      {esEntrada && usuario?.rol === 'ADMIN' && (
        <label className="flex min-h-11 items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" {...register('actualizar_precio')} className="size-5" />
          Guardar este precio como nuevo precio de compra del producto
        </label>
      )}

      <label className="block">
        <span className="etiqueta">Motivo</span>
        <select {...register('motivo')} className="campo">
          {MOTIVOS[tipo].map((m) => (
            <option key={m.valor} value={m.valor}>
              {m.texto}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="etiqueta">Comentario (opcional)</span>
        <input {...register('comentario')} autoComplete="off" className="campo" />
      </label>

      <div className={`rounded-lg p-3 ${sinStock ? 'bg-red-50 text-red-800' : 'bg-emerald-50 text-emerald-900'}`}>
        <p className="text-sm">Stock después de confirmar</p>
        <p className="text-2xl font-bold tabular-nums">
          {resultante === null ? '—' : `${formatoCantidad(resultante)} ${unidad}`}
        </p>
        {sinStock && <p className="text-sm font-medium">No hay stock suficiente para esta salida.</p>}
      </div>

      {registrar.error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          {registrar.error.message}
        </p>
      )}

      <button type="submit" disabled={registrar.isPending || sinStock} className="boton-primario w-full">
        {registrar.isPending ? 'Registrando…' : esEntrada ? 'Confirmar entrada' : 'Confirmar salida'}
      </button>
    </form>
  )
}

export default function Movimiento() {
  const tipo = RUTA_A_TIPO[useParams().tipo ?? '']
  const [params, setParams] = useSearchParams()
  const productoId = Number(params.get('producto')) || 0
  const { data: producto, error } = useProducto(productoId)
  const [ultimo, setUltimo] = useState<TipoMov | null>(null)

  if (!tipo) return <Navigate to="/" replace />

  const elegir = (id: number | null) => setParams(id ? { producto: String(id) } : {}, { replace: true })
  const pestana = (t: TipoMovimiento) =>
    `boton flex-1 ${t === tipo ? (t === 'ENTRADA' ? 'bg-emerald-700 text-white' : 'bg-amber-600 text-white') : 'bg-white text-slate-700 border border-slate-300'}`

  return (
    <section className="mx-auto max-w-lg space-y-4">
      <div className="flex gap-2">
        <Link to={`/movimiento/entrada${productoId ? `?producto=${productoId}` : ''}`} replace className={pestana('ENTRADA')}>
          Entrada
        </Link>
        <Link to={`/movimiento/salida${productoId ? `?producto=${productoId}` : ''}`} replace className={pestana('SALIDA')}>
          Salida
        </Link>
      </div>

      {ultimo && (
        <div role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-900">
          <p className="font-semibold">
            {ultimo.tipo === 'ENTRADA' ? 'Entrada' : 'Salida'} registrada: {ultimo.tipo === 'ENTRADA' ? '+' : '−'}
            {formatoCantidad(ultimo.cantidad)} {UNIDADES_CORTAS[ultimo.producto.unidad]} de {ultimo.producto.nombre}
          </p>
          <p>
            Stock ahora: {formatoCantidad(ultimo.stock_despues)} {UNIDADES_CORTAS[ultimo.producto.unidad]} · Valor:{' '}
            {formatoDinero(Number(ultimo.precio_unitario) * Number(ultimo.cantidad))} ·{' '}
            <Link to={`/productos/${ultimo.producto.id}`} className="font-medium underline">
              Ver producto
            </Link>
          </p>
        </div>
      )}

      <div className="tarjeta">
        {!productoId ? (
          <SelectorProducto onElegir={(p) => elegir(p.id)} />
        ) : error ? (
          <div className="space-y-2">
            <p className="text-red-700">{error.message}</p>
            <button onClick={() => elegir(null)} className="boton-secundario">Elegir otro producto</button>
          </div>
        ) : !producto ? (
          <p className="text-slate-500">Cargando…</p>
        ) : !producto.activo ? (
          <div className="space-y-2">
            <p className="text-slate-700">{producto.nombre} está desactivado y no admite movimientos.</p>
            <button onClick={() => elegir(null)} className="boton-secundario">Elegir otro producto</button>
          </div>
        ) : (
          <Formulario
            // Al cambiar de producto o de tipo, el formulario empieza de cero
            key={`${producto.id}-${tipo}`}
            producto={producto}
            tipo={tipo}
            onCambiarProducto={() => elegir(null)}
            onListo={(m) => {
              setUltimo(m)
              elegir(null)
            }}
          />
        )}
      </div>
    </section>
  )
}
