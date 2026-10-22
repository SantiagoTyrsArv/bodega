import { useState } from 'react'
import { Link } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import Escaner from './Escaner'

export function IconoCamara({ className = 'size-6' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M3 8h3l2-3h8l2 3h3v11H3z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  )
}

/**
 * Campo para buscar productos escribiendo o escaneando.
 * Enter cuenta como escaneo: así funcionan los lectores USB/Bluetooth, que escriben el código y un Enter.
 */
export default function Buscador({
  valor,
  onCambiar,
  onCodigo,
  placeholder,
  autoFocus,
}: {
  valor: string
  onCambiar: (texto: string) => void
  onCodigo: (codigo: string) => void
  placeholder: string
  autoFocus?: boolean
}) {
  const [escaneando, setEscaneando] = useState(false)

  return (
    <div className="flex gap-2">
      <input
        type="search"
        value={valor}
        onChange={(e) => onCambiar(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && valor.trim()) {
            e.preventDefault()
            onCodigo(valor.trim())
          }
        }}
        placeholder={placeholder}
        aria-label={placeholder}
        autoComplete="off"
        autoFocus={autoFocus}
        className="campo mt-0 flex-1"
      />
      <button
        type="button"
        onClick={() => setEscaneando(true)}
        aria-label="Escanear con la cámara"
        title="Escanear con la cámara"
        className="boton-secundario w-11 shrink-0 px-0"
      >
        <IconoCamara />
      </button>
      {escaneando && (
        <Escaner
          onCerrar={() => setEscaneando(false)}
          onLeer={(codigo) => {
            setEscaneando(false)
            onCambiar(codigo)
            onCodigo(codigo)
          }}
        />
      )}
    </div>
  )
}

/** Aviso para un código sin producto. A ADMIN le ofrece crearlo. */
export function AvisoCodigoNuevo({ codigo }: { codigo: string }) {
  const { data: usuario } = useUsuarioActual()
  return (
    <div role="status" className="space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
      <p>
        Ningún producto tiene el código <span className="font-semibold break-all">{codigo}</span>.
      </p>
      {usuario?.rol === 'ADMIN' && (
        <Link to={`/productos/nuevo?codigo=${encodeURIComponent(codigo)}`} className="boton-primario">
          Crear producto con este código
        </Link>
      )}
    </div>
  )
}
