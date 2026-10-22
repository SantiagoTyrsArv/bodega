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


# Se guarda en minúsculas, igual que se busca en el login
Correo = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[^@\s]+@[^@\s]+$"),
]
# El largo mínimo de la clave lo valida el router para dar un mensaje claro
Clave = Annotated[str, StringConstraints(max_length=200)]


class UsuarioCrear(BaseModel):
    nombre: Texto
    correo: Correo
    clave: Clave
    rol: Rol = Rol.USUARIO


class UsuarioEditar(BaseModel):
    nombre: Texto | None = None
    correo: Correo | None = None
    # Si se envía, reemplaza la clave (para cuando alguien la olvida)
    clave: Clave | None = None
    rol: Rol | None = None
    activo: bool | None = None


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
    presentacion: str | None = None
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
    presentacion: str | None = None
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
    presentacion: str | None
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
    pedido: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    responsable: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    # Solo ADMIN y solo en entradas: actualiza producto.precio_compra
    actualizar_precio: bool = False


class ProductoBreve(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    presentacion: str | None
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
    pedido: str | None
    responsable: str | None
    anula_a: int | None
    anulado_por: int | None
    fecha: datetime


class PaginaMovimientos(BaseModel):
    items: list[MovimientoSalida]
    total: int
    pagina: int
    por_pagina: int


class Resumen(BaseModel):
    """Datos de la pantalla de Inicio. Solo cuenta productos activos."""

    total_productos: int
    valor_compra: Decimal  # suma de stock × precio de compra
    valor_venta: Decimal  # suma de stock × precio de venta
    bajo_minimo: list[ProductoSalida]
    ultimos_movimientos: list[MovimientoSalida]
