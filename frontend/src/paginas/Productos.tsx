import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useCategorias } from '../api/categorias'
import { descargar } from '../api/cliente'
import { useBuscarCodigo, useProductos } from '../api/productos'
import Buscador, { AvisoCodigoNuevo } from '../componentes/Buscador'
import { desfaseLocal, estaBajoMinimo, formatoCantidad, formatoDinero, nombreProducto, UNIDADES_CORTAS } from '../formato'

export default function Productos() {
  const { data: usuario } = useUsuarioActual()
  const esAdmin = usuario?.rol === 'ADMIN'
  const { data: categorias = [] } = useCategorias()

  const [texto, setTexto] = useState('')
  const [q, setQ] = useState('')
  const [categoriaId, setCategoriaId] = useState('')
  const [verInactivos, setVerInactivos] = useState(false)
  const [descargando, setDescargando] = useState(false)
  const [errorDescarga, setErrorDescarga] = useState('')
  const navegar = useNavigate()
  // Un código escaneado (o escrito + Enter) que existe abre su ficha
  const codigo = useBuscarCodigo((p) => navegar(`/productos/${p.id}`))

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

  // Stock de todos los productos activos, sin importar los filtros de la pantalla
  const descargarExcel = async () => {
    setDescargando(true)
    setErrorDescarga('')
    try {
      await descargar(`/reportes/stock.xlsx?desfase=${desfaseLocal()}`)
    } catch (e) {
      setErrorDescarga(e instanceof Error ? e.message : 'No se pudo descargar')
    } finally {
      setDescargando(false)
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Productos</h1>
        <div className="flex gap-2">
          <button onClick={descargarExcel} disabled={descargando} className="boton-secundario">
            {descargando ? 'Descargando…' : 'Excel'}
          </button>
          {esAdmin && (
            <Link to="/productos/nuevo" className="boton-primario">
              + Nuevo
            </Link>
          )}
        </div>
      </div>
      {errorDescarga && <p className="text-sm text-red-700">{errorDescarga}</p>}

      <div className="grid gap-2 sm:grid-cols-[1fr_14rem]">
        <Buscador
          valor={texto}
          onCambiar={setTexto}
          onCodigo={(c) => {
            setQ(c)
            codigo.buscar(c)
          }}
          placeholder="Buscar por nombre o código"
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

      {codigo.error && <p className="text-sm text-red-700">{codigo.error}</p>}

      {isPending ? (
        <p className="text-slate-500">Cargando…</p>
      ) : error ? (
        <p className="text-red-700">{error.message}</p>
      ) : productos.length === 0 && codigo.noEncontrado !== '' && codigo.noEncontrado === texto.trim() ? (
        <AvisoCodigoNuevo codigo={codigo.noEncontrado} />
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
                    <p className="truncate font-medium text-slate-800">{nombreProducto(p)}</p>
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
