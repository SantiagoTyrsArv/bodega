/** Campo para buscar productos por nombre o código. */
export default function Buscador({
  valor,
  onCambiar,
  placeholder,
  autoFocus,
}: {
  valor: string
  onCambiar: (texto: string) => void
  placeholder: string
  autoFocus?: boolean
}) {
  return (
    <input
      type="search"
      value={valor}
      onChange={(e) => onCambiar(e.target.value)}
      placeholder={placeholder}
      aria-label={placeholder}
      autoComplete="off"
      autoFocus={autoFocus}
      className="campo mt-0 w-full"
    />
  )
}
