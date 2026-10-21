import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useCategorias } from '../api/categorias'
import { UNIDADES } from '../formato'
import type { Categoria, Producto, ProductoDatos, Unidad } from '../tipos'

/** Número decimal escrito por la persona: acepta coma o punto. */
const decimal = (maxDecimales: number, mensaje: string) =>
  z
    .string()
    .trim()
    .transform((s) => s.replace(',', '.'))
    .pipe(z.string().regex(new RegExp(`^\\d{1,9}(\\.\\d{1,${maxDecimales}})?$`), mensaje))

const esquema = z.object({
  codigo: z.string().trim().min(1, 'Escribe o escanea el código'),
  nombre: z.string().trim().min(1, 'Escribe el nombre'),
  categoria_id: z.string(),
  unidad: z.enum(Object.keys(UNIDADES) as [Unidad, ...Unidad[]]),
  precio_compra: decimal(2, 'Precio inválido (máximo 2 decimales)'),
  precio_venta: decimal(2, 'Precio inválido (máximo 2 decimales)'),
  stock_minimo: decimal(3, 'Cantidad inválida (máximo 3 decimales)'),
  nota: z.string().trim(),
})

type Entrada = z.input<typeof esquema>
type Salida = z.output<typeof esquema>

interface Props {
  producto?: Producto
  codigoInicial?: string
  textoBoton: string
  pendiente: boolean
  error: Error | null
  onEnviar: (datos: ProductoDatos) => void
  onCancelar?: () => void
}

export default function FormProducto(props: Props) {
  const { data: categorias, isPending, error } = useCategorias()
  // El select necesita las opciones antes de tomar su valor inicial
  if (isPending) return <p className="text-slate-500">Cargando…</p>
  if (error) return <p className="text-red-700">{error.message}</p>
  return <Formulario {...props} categorias={categorias} />
}

function Formulario({
  producto,
  codigoInicial = '',
  textoBoton,
  pendiente,
  error,
  onEnviar,
  onCancelar,
  categorias,
}: Props & { categorias: Categoria[] }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Entrada, unknown, Salida>({
    resolver: zodResolver(esquema),
    defaultValues: {
      codigo: producto?.codigo ?? codigoInicial,
      nombre: producto?.nombre ?? '',
      categoria_id: producto?.categoria ? String(producto.categoria.id) : '',
      unidad: producto?.unidad ?? 'UNIDAD',
      precio_compra: producto?.precio_compra ?? '',
      precio_venta: producto?.precio_venta ?? '',
      stock_minimo: producto ? String(Number(producto.stock_minimo)) : '0',
      nota: producto?.nota ?? '',
    },
  })

  const enviar = (d: Salida) =>
    onEnviar({
      ...d,
      categoria_id: d.categoria_id ? Number(d.categoria_id) : null,
      nota: d.nota || null,
    })

  return (
    <form onSubmit={handleSubmit(enviar)} noValidate className="space-y-4">
      <label className="block">
        <span className="etiqueta">Código de barras</span>
        <input {...register('codigo')} inputMode="numeric" autoComplete="off" className="campo" />
        {errors.codigo && <span className="error-campo">{errors.codigo.message}</span>}
      </label>

      <label className="block">
        <span className="etiqueta">Nombre</span>
        <input {...register('nombre')} autoComplete="off" className="campo" />
        {errors.nombre && <span className="error-campo">{errors.nombre.message}</span>}
      </label>

      <label className="block">
        <span className="etiqueta">Categoría</span>
        <select {...register('categoria_id')} className="campo">
          <option value="">Sin categoría</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="etiqueta">Unidad</span>
        <select {...register('unidad')} className="campo">
          {Object.entries(UNIDADES).map(([valor, texto]) => (
            <option key={valor} value={valor}>
              {texto}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="etiqueta">Precio de compra</span>
        <input {...register('precio_compra')} inputMode="decimal" autoComplete="off" className="campo" />
        {errors.precio_compra && <span className="error-campo">{errors.precio_compra.message}</span>}
      </label>

      <label className="block">
        <span className="etiqueta">Precio de venta</span>
        <input {...register('precio_venta')} inputMode="decimal" autoComplete="off" className="campo" />
        {errors.precio_venta && <span className="error-campo">{errors.precio_venta.message}</span>}
      </label>

      <label className="block">
        <span className="etiqueta">Stock mínimo</span>
        <input {...register('stock_minimo')} inputMode="decimal" autoComplete="off" className="campo" />
        <span className="mt-1 block text-xs text-slate-500">Con 0 no se generan alertas de stock bajo.</span>
        {errors.stock_minimo && <span className="error-campo">{errors.stock_minimo.message}</span>}
      </label>

      <label className="block">
        <span className="etiqueta">Nota (opcional)</span>
        <textarea {...register('nota')} rows={2} className="campo py-2" />
      </label>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          {error.message}
        </p>
      )}

      <div className="flex flex-col gap-2 sm:flex-row">
        <button type="submit" disabled={pendiente} className="boton-primario sm:flex-1">
          {pendiente ? 'Guardando…' : textoBoton}
        </button>
        {onCancelar && (
          <button type="button" onClick={onCancelar} className="boton-secundario sm:flex-1">
            Cancelar
          </button>
        )}
      </div>
    </form>
  )
}
