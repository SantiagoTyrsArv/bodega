import { useState } from 'react'
import { useUsuarioActual } from '../api/auth'
import { descargar } from '../api/cliente'
import { useAnularMovimiento, useMovimientos } from '../api/movimientos'
import ListaMovimientos from '../componentes/ListaMovimientos'
import { desfaseLocal, rangoDeDias } from '../formato'
import type { TipoMovimiento } from '../tipos'

const POR_PAGINA = 50

export default function Historial() {
  const { data: usuario } = useUsuarioActual()
  const esAdmin = usuario?.rol === 'ADMIN'
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [tipo, setTipo] = useState<TipoMovimiento | ''>('')
  const [pagina, setPagina] = useState(1)
  const [descargando, setDescargando] = useState(false)
  const [errorDescarga, setErrorDescarga] = useState('')

  const rangoInvertido = desde !== '' && hasta !== '' && desde > hasta
  const filtros = { ...(rangoInvertido ? {} : rangoDeDias(desde, hasta)), tipo: tipo || undefined }
  const { data, isPending, error, isFetching } = useMovimientos({ ...filtros, pagina, por_pagina: POR_PAGINA })
  const anular = useAnularMovimiento()
  const paginas = data ? Math.max(1, Math.ceil(data.total / POR_PAGINA)) : 1

  // Cambiar un filtro vuelve a la primera página
  const filtrar = (cambio: () => void) => {
    cambio()
    setPagina(1)
  }

  const descargarExcel = async () => {
    const params = new URLSearchParams({ desfase: String(desfaseLocal()) })
    for (const [clave, valor] of Object.entries(filtros)) if (valor) params.set(clave, valor)
    setDescargando(true)
    setErrorDescarga('')
    try {
      await descargar(`/reportes/movimientos.xlsx?${params}`)
    } catch (e) {
      setErrorDescarga(e instanceof Error ? e.message : 'No se pudo descargar')
    } finally {
      setDescargando(false)
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Historial</h1>
        <button onClick={descargarExcel} disabled={descargando || rangoInvertido} className="boton-secundario">
          {descargando ? 'Descargando…' : 'Descargar Excel'}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <label className="block">
          <span className="etiqueta">Desde</span>
          <input type="date" value={desde} onChange={(e) => filtrar(() => setDesde(e.target.value))} className="campo" />
        </label>
        <label className="block">
          <span className="etiqueta">Hasta</span>
          <input type="date" value={hasta} onChange={(e) => filtrar(() => setHasta(e.target.value))} className="campo" />
        </label>
        <label className="col-span-2 block sm:col-span-1">
          <span className="etiqueta">Tipo</span>
          <select
            value={tipo}
            onChange={(e) => filtrar(() => setTipo(e.target.value as TipoMovimiento | ''))}
            className="campo"
          >
            <option value="">Entradas y salidas</option>
            <option value="ENTRADA">Solo entradas</option>
            <option value="SALIDA">Solo salidas</option>
          </select>
        </label>
      </div>
      {rangoInvertido && <p className="text-sm text-red-700">La fecha inicial debe ser anterior a la final.</p>}
      {errorDescarga && <p className="text-sm text-red-700">{errorDescarga}</p>}
      {anular.error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          No se pudo anular: {anular.error.message}
        </p>
      )}

      <div className={`tarjeta ${isFetching ? 'opacity-70' : ''}`}>
        {isPending ? (
          <p className="text-slate-500">Cargando…</p>
        ) : error ? (
          <p className="text-red-700">{error.message}</p>
        ) : data.total === 0 && (desde || hasta || tipo) ? (
          <p className="text-sm text-slate-500">No hay movimientos con estos filtros.</p>
        ) : (
          <>
            <p className="text-sm text-slate-500">
              {data.total} {data.total === 1 ? 'movimiento' : 'movimientos'}
            </p>
            <ListaMovimientos
              movimientos={data.items}
              mostrarProducto
              onAnular={esAdmin ? (m) => anular.mutate(m.id) : undefined}
              anulandoId={anular.isPending ? (anular.variables ?? null) : null}
            />
          </>
        )}
      </div>

      {paginas > 1 && (
        <div className="flex items-center justify-between gap-2">
          <button onClick={() => setPagina(pagina - 1)} disabled={pagina <= 1} className="boton-secundario">
            ← Más recientes
          </button>
          <span className="text-sm text-slate-600">
            Página {pagina} de {paginas}
          </span>
          <button onClick={() => setPagina(pagina + 1)} disabled={pagina >= paginas} className="boton-secundario">
            Más antiguos →
          </button>
        </div>
      )}
    </section>
  )
}
