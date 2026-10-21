export type Rol = 'ADMIN' | 'USUARIO'
export type Unidad = 'UNIDAD' | 'KG' | 'LITRO' | 'CAJA'
export type TipoMovimiento = 'ENTRADA' | 'SALIDA'
export type Motivo = 'COMPRA' | 'DEVOLUCION' | 'USO' | 'VENTA' | 'PERDIDA' | 'AJUSTE' | 'ANULACION'

export interface Usuario {
  id: number
  nombre: string
  correo: string
  rol: Rol
  activo: boolean
  creado_en: string
}

export interface TokenSalida {
  access_token: string
  token_type: string
  usuario: Usuario
}

export interface Categoria {
  id: number
  nombre: string
}

// Cantidades y precios llegan como texto ("12.50") para no perder precisión
export interface Producto {
  id: number
  codigo: string
  nombre: string
  categoria: Categoria | null
  unidad: Unidad
  precio_compra: string
  precio_venta: string
  stock: string
  stock_minimo: string
  nota: string | null
  activo: boolean
  creado_en: string
  actualizado_en: string
}

/** Datos que se envían al crear o editar un producto (sin stock). */
export interface ProductoDatos {
  codigo: string
  nombre: string
  categoria_id: number | null
  unidad: Unidad
  precio_compra: string
  precio_venta: string
  stock_minimo: string
  nota: string | null
}

export interface Movimiento {
  id: number
  producto: Pick<Producto, 'id' | 'codigo' | 'nombre' | 'unidad'>
  usuario: Pick<Usuario, 'id' | 'nombre'>
  tipo: TipoMovimiento
  motivo: Motivo
  cantidad: string
  precio_unitario: string
  stock_despues: string
  comentario: string | null
  anula_a: number | null
  anulado_por: number | null
  fecha: string
}

export interface MovimientoDatos {
  producto_id: number
  tipo: TipoMovimiento
  motivo: Motivo
  cantidad: string
  precio_unitario?: string
  comentario?: string | null
  actualizar_precio?: boolean
}

export interface Pagina<T> {
  items: T[]
  total: number
  pagina: number
  por_pagina: number
}
