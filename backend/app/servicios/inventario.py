"""Único módulo que modifica producto.stock.

Cada movimiento se registra en una transacción: bloqueo del producto con
SELECT ... FOR UPDATE, validación, inserción del movimiento con stock_despues,
actualización del stock y commit. Si algún día hay varias bodegas, el cambio
queda aquí: el stock pasaría a leerse y escribirse por (producto, bodega)
dentro de _bloquear_producto y _aplicar.
"""

from decimal import Decimal

from fastapi import status
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, lazyload

from app.modelos import Motivo, Movimiento, Producto, Rol, TipoMovimiento, Unidad, Usuario

MOTIVOS_VALIDOS = {
    TipoMovimiento.ENTRADA: {Motivo.COMPRA, Motivo.DEVOLUCION, Motivo.AJUSTE},
    TipoMovimiento.SALIDA: {Motivo.USO, Motivo.VENTA, Motivo.PERDIDA, Motivo.AJUSTE},
}

NOMBRE_UNIDAD = {
    Unidad.UNIDAD: "unidades",
    Unidad.KG: "kg",
    Unidad.LITRO: "litros",
    Unidad.CAJA: "cajas",
}


class ErrorInventario(Exception):
    """Error de negocio con el código HTTP que le corresponde."""

    def __init__(self, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.estado = estado


def _texto_cantidad(cantidad: Decimal) -> str:
    """5.000 -> "5", 2.500 -> "2,5"."""
    return f"{cantidad.normalize():f}".replace(".", ",")


def _bloquear_producto(db: Session, producto_id: int) -> Producto:
    # lazyload: FOR UPDATE no admite el LEFT JOIN de la categoría
    producto = db.scalar(
        select(Producto)
        .where(Producto.id == producto_id)
        .options(lazyload(Producto.categoria))
        .with_for_update()
    )
    if producto is None:
        raise ErrorInventario("El producto no existe", status.HTTP_404_NOT_FOUND)
    return producto


def _aplicar(
    db: Session,
    producto: Producto,
    usuario: Usuario,
    tipo: TipoMovimiento,
    motivo: Motivo,
    cantidad: Decimal,
    precio_unitario: Decimal,
    comentario: str | None = None,
    anula_a: int | None = None,
) -> Movimiento:
    """Calcula el stock nuevo, lo valida y deja el movimiento listo para el commit."""
    signo = 1 if tipo == TipoMovimiento.ENTRADA else -1
    nuevo_stock = producto.stock + signo * cantidad
    if nuevo_stock < 0:
        unidad = NOMBRE_UNIDAD[Unidad(producto.unidad)]
        raise ErrorInventario(
            f"Stock insuficiente: quedan {_texto_cantidad(producto.stock)} {unidad}",
            status.HTTP_409_CONFLICT,
        )
    movimiento = Movimiento(
        producto=producto,
        usuario=usuario,
        tipo=tipo,
        motivo=motivo,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        stock_despues=nuevo_stock,
        comentario=comentario or None,
        anula_a=anula_a,
    )
    db.add(movimiento)
    producto.stock = nuevo_stock
    return movimiento


def _guardar(db: Session, movimiento: Movimiento) -> Movimiento:
    db.commit()
    db.refresh(movimiento)
    return movimiento


def registrar_movimiento(
    db: Session,
    *,
    producto_id: int,
    usuario: Usuario,
    tipo: TipoMovimiento,
    motivo: Motivo,
    cantidad: Decimal,
    precio_unitario: Decimal | None = None,
    comentario: str | None = None,
    actualizar_precio: bool = False,
) -> Movimiento:
    tipo, motivo = TipoMovimiento(tipo), Motivo(motivo)
    if motivo not in MOTIVOS_VALIDOS[tipo]:
        validos = ", ".join(sorted(MOTIVOS_VALIDOS[tipo]))
        raise ErrorInventario(
            f"Motivo no válido para una {tipo.lower()}. Usa: {validos}",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    if actualizar_precio and usuario.rol != Rol.ADMIN:
        raise ErrorInventario(
            "Solo un administrador puede actualizar el precio de compra",
            status.HTTP_403_FORBIDDEN,
        )
    if actualizar_precio and tipo != TipoMovimiento.ENTRADA:
        raise ErrorInventario(
            "El precio de compra solo se actualiza con una entrada",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    producto = _bloquear_producto(db, producto_id)
    if not producto.activo:
        raise ErrorInventario("El producto está desactivado", status.HTTP_409_CONFLICT)

    if precio_unitario is None:
        es_entrada = tipo == TipoMovimiento.ENTRADA
        precio_unitario = producto.precio_compra if es_entrada else producto.precio_venta

    movimiento = _aplicar(
        db, producto, usuario, tipo, motivo, cantidad, precio_unitario, comentario
    )
    if actualizar_precio:
        producto.precio_compra = precio_unitario
    return _guardar(db, movimiento)


def anular_movimiento(db: Session, *, movimiento_id: int, usuario: Usuario) -> Movimiento:
    """Crea el movimiento contrario al original. Solo ADMIN (se valida en el router)."""
    # Bloquear el original serializa dos anulaciones simultáneas del mismo movimiento
    original = db.scalar(
        select(Movimiento)
        .where(Movimiento.id == movimiento_id)
        .options(lazyload("*"))
        .with_for_update()
    )
    if original is None:
        raise ErrorInventario("El movimiento no existe", status.HTTP_404_NOT_FOUND)
    if original.motivo == Motivo.ANULACION:
        raise ErrorInventario("Una anulación no se puede anular", status.HTTP_409_CONFLICT)
    ya_anulado = select(exists().where(Movimiento.anula_a == original.id))
    if db.scalar(ya_anulado):
        raise ErrorInventario("Este movimiento ya fue anulado", status.HTTP_409_CONFLICT)

    producto = _bloquear_producto(db, original.producto_id)
    contrario = (
        TipoMovimiento.SALIDA if original.tipo == TipoMovimiento.ENTRADA else TipoMovimiento.ENTRADA
    )
    movimiento = _aplicar(
        db,
        producto,
        usuario,
        contrario,
        Motivo.ANULACION,
        original.cantidad,
        original.precio_unitario,
        anula_a=original.id,
    )
    try:
        return _guardar(db, movimiento)
    except IntegrityError:
        # Respaldo: la restricción única de anula_a impide una segunda anulación
        db.rollback()
        raise ErrorInventario("Este movimiento ya fue anulado", status.HTTP_409_CONFLICT) from None
