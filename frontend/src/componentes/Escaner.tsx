import type { IScannerControls } from '@zxing/browser'
import { useEffect, useLayoutEffect, useRef, useState } from 'react'

/** Abre la cámara y lee códigos. zxing se carga solo cuando se usa, para no pesar en la carga inicial. */
async function iniciarLector(video: HTMLVideoElement, alLeer: (texto: string, controles: IScannerControls) => void) {
  const [{ BrowserMultiFormatReader }, { BarcodeFormat, DecodeHintType }] = await Promise.all([
    import('@zxing/browser'),
    import('@zxing/library'),
  ])
  const formatos = [
    BarcodeFormat.EAN_13,
    BarcodeFormat.EAN_8,
    BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E,
    BarcodeFormat.CODE_128,
  ]
  const lector = new BrowserMultiFormatReader(new Map([[DecodeHintType.POSSIBLE_FORMATS, formatos]]))
  // Sin tamaño, el navegador entrega 640×480 y cuesta leer códigos pequeños o lejanos
  const camara = { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
  return lector.decodeFromConstraints({ video: camara }, video, (resultado, _e, controles) => {
    if (resultado) alLeer(resultado.getText(), controles)
  })
}

function mensajeDeError(e: unknown): string {
  const nombre = e instanceof DOMException ? e.name : ''
  if (nombre === 'NotAllowedError') return 'No hay permiso para usar la cámara. Actívalo en el navegador.'
  if (nombre === 'NotFoundError' || nombre === 'OverconstrainedError') return 'No se encontró una cámara.'
  if (nombre === 'NotReadableError') return 'La cámara está ocupada por otra aplicación.'
  return 'No se pudo abrir la cámara.'
}

/**
 * Lector de códigos de barras con la cámara trasera, a pantalla completa.
 * Siempre ofrece escribir el código a mano.
 */
export default function Escaner({ onLeer, onCerrar }: { onLeer: (codigo: string) => void; onCerrar: () => void }) {
  const video = useRef<HTMLVideoElement>(null)
  // La cámara solo existe en HTTPS o en localhost
  const hayCamara = Boolean(navigator.mediaDevices?.getUserMedia)
  const [error, setError] = useState(hayCamara ? '' : 'La cámara solo funciona con HTTPS. Escribe el código a mano.')
  const [manual, setManual] = useState('')
  // Referencia estable para no reiniciar la cámara si el padre cambia la función
  const alLeer = useRef(onLeer)
  useLayoutEffect(() => {
    alLeer.current = onLeer
  })
  // Cada arranque espera a que termine el anterior: si no, el stop() de una cámara que
  // arrancó tarde apaga el video de la siguiente (pasa con el doble montaje de StrictMode)
  const cola = useRef(Promise.resolve())

  useEffect(() => {
    if (!hayCamara) return
    let controles: IScannerControls | null = null
    let terminado = false

    cola.current = cola.current.then(async () => {
      if (terminado) return
      try {
        const c = await iniciarLector(video.current!, (texto, ctrl) => {
          if (terminado) return
          terminado = true
          ctrl.stop()
          navigator.vibrate?.(100)
          alLeer.current(texto)
        })
        // Si el componente se cerró mientras la cámara arrancaba, se apaga de inmediato
        if (terminado) c.stop()
        else controles = c
      } catch (e) {
        if (!terminado) setError(mensajeDeError(e))
      }
    })

    return () => {
      terminado = true
      controles?.stop()
    }
  }, [hayCamara])

  // Escape cierra el escáner
  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => e.key === 'Escape' && onCerrar()
    window.addEventListener('keydown', alTeclear)
    return () => window.removeEventListener('keydown', alTeclear)
  }, [onCerrar])

  return (
    <div role="dialog" aria-modal="true" aria-label="Escanear código" className="fixed inset-0 z-50 flex flex-col bg-black text-white">
      <div className="flex items-center justify-between px-4 py-2">
        <span className="font-semibold">Escanear código</span>
        <button onClick={onCerrar} className="min-h-11 rounded-lg px-3 font-medium hover:bg-white/10">
          Cerrar
        </button>
      </div>

      <div className="relative flex flex-1 items-center justify-center overflow-hidden">
        <video ref={video} muted playsInline className="h-full w-full object-cover" />
        {error ? (
          <p className="absolute mx-6 rounded-lg bg-black/80 p-4 text-center">{error}</p>
        ) : (
          // Guía para centrar el código
          <div aria-hidden className="absolute h-32 w-4/5 max-w-sm rounded-lg border-2 border-white/80" />
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          const codigo = manual.trim()
          if (codigo) onLeer(codigo)
        }}
        className="flex gap-2 p-4 pb-[max(1rem,env(safe-area-inset-bottom))]"
      >
        <input
          value={manual}
          onChange={(e) => setManual(e.target.value)}
          placeholder="O escribe el código"
          aria-label="Código"
          autoComplete="off"
          className="campo mt-0 flex-1 text-slate-800"
        />
        <button type="submit" className="boton-primario">
          Buscar
        </button>
      </form>
    </div>
  )
}
