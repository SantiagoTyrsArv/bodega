from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.modelos import Motivo, Rol, TipoMovimiento, Unidad

# Los Decimal viajan en JSON como texto ("12.50") para no perder precisión
Precio = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Cantidad = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=3)]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class LoginEntrada(BaseModel):
    correo: str = Field(min_length=3)
    clave: str = Field(min_length=1)


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol: Rol
    activo: bool
    creado_en: datetime


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSalida


class CategoriaEntrada(BaseModel):
    nombre: Texto


class CategoriaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProductoCrear(BaseModel):
    # forbid: el stock no se puede enviar; solo cambia con movimientos
    model_config = ConfigDict(extra="forbid")

    codigo: Texto
    nombre: Texto
    categoria_id: int | None = None
    unidad: Unidad
    precio_compra: Precio
    precio_venta: Precio
    stock_minimo: Cantidad = Decimal(0)
    nota: str | None = None


class ProductoEditar(BaseModel):
    """Cambios parciales: solo se aplican los campos enviados."""

    model_config = ConfigDict(extra="forbid")

    codigo: Texto | None = None
    nombre: Texto | None = None
    categoria_id: int | None = None
    unidad: Unidad | None = None
    precio_compra: Precio | None = None
    precio_venta: Precio | None = None
    stock_minimo: Cantidad | None = None
    nota: str | None = None
    activo: bool | None = None


class ProductoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    categoria: CategoriaSalida | None
    unidad: Unidad
    precio_compra: Decimal
    precio_venta: Decimal
    stock: Decimal
    stock_minimo: Decimal
    nota: str | None
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class MovimientoEntrada(BaseModel):
    producto_id: int
    tipo: TipoMovimiento
    motivo: Motivo
    cantidad: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=3)]
    # Si no se envía: precio de compra en entradas, precio de venta en salidas
    precio_unitario: Precio | None = None
    comentario: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    # Solo ADMIN y solo en entradas: actualiza producto.precio_compra
    actualizar_precio: bool = False


class ProductoBreve(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    unidad: Unidad


class UsuarioBreve(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class MovimientoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto: ProductoBreve
    usuario: UsuarioBreve
    tipo: TipoMovimiento
    motivo: Motivo
    cantidad: Decimal
    precio_unitario: Decimal
    stock_despues: Decimal
    comentario: str | None
    anula_a: int | None
    anulado_por: int | None
    fecha: datetime


class PaginaMovimientos(BaseModel):
    items: list[MovimientoSalida]
    total: int
    pagina: int
    por_pagina: int
