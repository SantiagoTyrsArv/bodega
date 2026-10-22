from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Nombres de restricciones predecibles para que Alembic las genere bien
CONVENCION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Cantidad = Numeric(12, 3)
Precio = Numeric(12, 2)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION)


class Rol(StrEnum):
    ADMIN = "ADMIN"
    USUARIO = "USUARIO"


class Unidad(StrEnum):
    UNIDAD = "UNIDAD"
    KG = "KG"
    LITRO = "LITRO"
    CAJA = "CAJA"


class TipoMovimiento(StrEnum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"


class Motivo(StrEnum):
    COMPRA = "COMPRA"
    DEVOLUCION = "DEVOLUCION"
    USO = "USO"
    VENTA = "VENTA"
    PERDIDA = "PERDIDA"
    AJUSTE = "AJUSTE"
    ANULACION = "ANULACION"


def _valores(enum: type[StrEnum]) -> str:
    """Lista SQL de valores para un CHECK ... IN (...)."""
    return ", ".join(f"'{v.value}'" for v in enum)


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (CheckConstraint(f"rol IN ({_valores(Rol)})", name="rol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(Text)
    correo: Mapped[str] = mapped_column(Text, unique=True)
    clave_hash: Mapped[str] = mapped_column(Text)
    rol: Mapped[str] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, unique=True)


class Producto(Base):
    __tablename__ = "producto"
    __table_args__ = (
        CheckConstraint(f"unidad IN ({_valores(Unidad)})", name="unidad"),
        CheckConstraint("precio_compra >= 0", name="precio_compra"),
        CheckConstraint("precio_venta >= 0", name="precio_venta"),
        CheckConstraint("stock >= 0", name="stock"),
        CheckConstraint("stock_minimo >= 0", name="stock_minimo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, unique=True)
    nombre: Mapped[str] = mapped_column(Text)
    # Tamaño o formato del producto, p. ej. "1.5 L" o "400 ml"
    presentacion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categoria.id"))
    categoria: Mapped[Categoria | None] = relationship(lazy="joined")
    unidad: Mapped[str] = mapped_column(Text)
    precio_compra: Mapped[Decimal] = mapped_column(Precio)
    precio_venta: Mapped[Decimal] = mapped_column(Precio)
    # Solo servicios/inventario.py modifica este campo
    stock: Mapped[Decimal] = mapped_column(Cantidad, default=Decimal(0), server_default="0")
    stock_minimo: Mapped[Decimal] = mapped_column(Cantidad, default=Decimal(0), server_default="0")
    nota: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Movimiento(Base):
    __tablename__ = "movimiento"
    __table_args__ = (
        CheckConstraint(f"tipo IN ({_valores(TipoMovimiento)})", name="tipo"),
        CheckConstraint(f"motivo IN ({_valores(Motivo)})", name="motivo"),
        CheckConstraint("cantidad > 0", name="cantidad"),
        CheckConstraint("stock_despues >= 0", name="stock_despues"),
        Index("ix_movimiento_producto_fecha", "producto_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    tipo: Mapped[str] = mapped_column(Text)
    motivo: Mapped[str] = mapped_column(Text)
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)
    precio_unitario: Mapped[Decimal] = mapped_column(Precio)
    stock_despues: Mapped[Decimal] = mapped_column(Cantidad)
    comentario: Mapped[str | None] = mapped_column(Text)
    pedido: Mapped[str | None] = mapped_column(Text)  # número de pedido
    responsable: Mapped[str | None] = mapped_column(Text)  # cliente o quien recibe/entrega
    # Un movimiento solo se anula una vez: unique impide dos anulaciones del mismo original
    anula_a: Mapped[int | None] = mapped_column(ForeignKey("movimiento.id"), unique=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    producto: Mapped[Producto] = relationship(lazy="joined")
    usuario: Mapped[Usuario] = relationship(lazy="joined")
    # El movimiento que anula a este, si existe
    anulacion: Mapped[Movimiento | None] = relationship(uselist=False, lazy="selectin")

    @property
    def anulado_por(self) -> int | None:
        return self.anulacion.id if self.anulacion else None
