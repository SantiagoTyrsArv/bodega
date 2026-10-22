"""Importa productos y movimientos del Excel de control de inventario que se usaba antes
de la app (hojas "Inventario" y "Movimientos").

Uso:
    uv run python -m app.importar_excel archivo.xlsx            # solo muestra el plan
    uv run python -m app.importar_excel archivo.xlsx --aplicar  # lo guarda en la base

Reglas:
- El ID del Excel (P001...) queda como código del producto hasta que tenga código de barras.
- El "Precio unitario" es el precio de compra y las cantidades son cajas.
- El stock entra con movimientos, nunca escribiendo producto.stock: primero una entrada de
  AJUSTE con el stock inicial y luego cada fila de "Movimientos", en orden.
- El stock inicial se calcula para que el stock final sea el "Stock actual" del Excel.
- Las filas sin fecha se registran el día anterior al primer movimiento con fecha.
"""

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.modelos import Motivo, Producto, Rol, TipoMovimiento, Unidad, Usuario
from app.servicios import inventario

# Colombia no tiene horario de verano
ZONA = timezone(timedelta(hours=-5))
STOCK_MINIMO = Decimal(5)  # el Excel marcaba "STOCK BAJO" con 5 o menos
COMENTARIO_INICIAL = "Stock inicial (importado del Excel)"
SIN_FECHA = "fecha no registrada en el Excel"
SIN_FECHA_INICIO = "Fecha no registrada en el Excel"
# En "Cliente / Responsable" a veces se escribió el motivo en vez de una persona
MOTIVOS_EN_RESPONSABLE = {"compra": Motivo.COMPRA, "venta": Motivo.VENTA}
CORRECCIONES_RESPONSABLE = {"riben": "ruben"}


@dataclass
class ProductoExcel:
    codigo: str
    nombre: str
    presentacion: str | None
    precio_compra: Decimal
    stock_inicial_excel: Decimal
    stock_actual_excel: Decimal
    stock_inicial: Decimal = Decimal(0)


@dataclass
class MovimientoExcel:
    fila: int
    codigo: str
    tipo: TipoMovimiento
    motivo: Motivo
    cantidad: Decimal
    fecha: datetime | None
    pedido: str | None
    responsable: str | None
    comentario: str | None


@dataclass
class Plan:
    productos: list[ProductoExcel]
    movimientos: list[MovimientoExcel]
    avisos: list[str] = field(default_factory=list)


def _texto(valor) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _decimal(valor) -> Decimal:
    return Decimal(str(valor)) if valor not in (None, "") else Decimal(0)


def _fila_encabezado(hoja, primera: str) -> int:
    for fila in hoja.iter_rows():
        if _texto(fila[0].value) == primera:
            return fila[0].row
    raise ValueError(f'No encontré el encabezado "{primera}" en la hoja {hoja.title}')


def leer_productos(hoja) -> list[ProductoExcel]:
    """Columnas: ID, Producto, Presentación, Stock inicial, Entradas, Salidas, Stock actual,
    Precio unitario. Se omiten las filas con ID pero sin nombre (plantilla vacía)."""
    productos = []
    inicio = _fila_encabezado(hoja, "ID") + 1
    for fila in hoja.iter_rows(min_row=inicio, values_only=True):
        codigo, nombre = _texto(fila[0]), _texto(fila[1])
        if not codigo or not nombre:
            continue
        productos.append(
            ProductoExcel(
                codigo=codigo.upper(),
                nombre=nombre,
                presentacion=_texto(fila[2]),
                precio_compra=_decimal(fila[7]),
                stock_inicial_excel=_decimal(fila[3]),
                stock_actual_excel=_decimal(fila[6]),
            )
        )
    return productos


def _fecha(valor) -> datetime | None:
    """Las fechas del Excel no traen hora: se dejan al mediodía en Colombia."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        return datetime.combine(valor, time(12), ZONA)
    raise ValueError(f"Fecha no válida: {valor!r}")


def leer_movimientos(hoja, avisos: list[str]) -> list[MovimientoExcel]:
    """Columnas: Fecha, ID Producto, Producto, Presentación, Cantidad, Tipo, N° Pedido,
    Cliente / Responsable, Observaciones. Termina en la primera fila sin ID de producto."""
    movimientos = []
    inicio = _fila_encabezado(hoja, "Fecha") + 1
    for n, fila in enumerate(hoja.iter_rows(min_row=inicio, values_only=True), start=inicio):
        codigo = _texto(fila[1])
        if not codigo:
            if any(v is not None for v in fila[1:]):
                avisos.append(f"Movimientos fila {n}: sin ID de producto, se omite")
            continue
        cantidad, tipo = fila[4], (_texto(fila[5]) or "").lower()
        if cantidad in (None, "") or tipo not in ("entrada", "salida"):
            avisos.append(
                f"Movimientos fila {n} ({codigo.upper()}): sin cantidad o sin tipo, se omite"
                f" (observación: {_texto(fila[8]) or '—'})"
            )
            continue

        tipo = TipoMovimiento.ENTRADA if tipo == "entrada" else TipoMovimiento.SALIDA
        responsable = _texto(fila[7])
        motivo = None
        if responsable and responsable.lower() in MOTIVOS_EN_RESPONSABLE:
            motivo = MOTIVOS_EN_RESPONSABLE[responsable.lower()]
            responsable = None
        if responsable:
            responsable = CORRECCIONES_RESPONSABLE.get(responsable.lower(), responsable)
            responsable = responsable.capitalize()
        if motivo is None or motivo not in inventario.MOTIVOS_VALIDOS[tipo]:
            # Sin motivo escrito: las salidas a una persona son ventas; las entradas, compras
            motivo = Motivo.COMPRA if tipo == TipoMovimiento.ENTRADA else Motivo.VENTA

        fecha = _fecha(fila[0])
        comentario = _texto(fila[8])
        if fecha is None:
            comentario = f"{comentario}; {SIN_FECHA}" if comentario else SIN_FECHA_INICIO
        movimientos.append(
            MovimientoExcel(
                fila=n,
                codigo=codigo.upper(),
                tipo=tipo,
                motivo=motivo,
                cantidad=_decimal(cantidad),
                fecha=fecha,
                pedido=_texto(fila[6]),
                responsable=responsable,
                comentario=comentario,
            )
        )
    return movimientos


def armar_plan(ruta: Path) -> Plan:
    """Lee el Excel, ordena los movimientos y valida que el stock nunca quede negativo."""
    libro = load_workbook(ruta, data_only=True)
    avisos: list[str] = []
    productos = leer_productos(libro["Inventario"])
    movimientos = leer_movimientos(libro["Movimientos"], avisos)

    por_codigo = {p.codigo: p for p in productos}
    for m in movimientos:
        if m.codigo not in por_codigo:
            raise ValueError(f"Movimientos fila {m.fila}: el producto {m.codigo} no existe")

    # Fechas: primero los que no tienen, el día anterior al primer movimiento con fecha
    fechadas = [m.fecha for m in movimientos if m.fecha]
    primer_dia = min(fechadas) if fechadas else datetime.combine(date.today(), time(12), ZONA)
    base = primer_dia - timedelta(days=1)
    sin_fecha = [m for m in movimientos if m.fecha is None]
    con_fecha = sorted((m for m in movimientos if m.fecha), key=lambda m: m.fecha)
    for i, m in enumerate(sin_fecha):
        m.fecha = base + timedelta(seconds=i)
    # Segundos de diferencia para conservar el orden de las filas del mismo día
    for i, m in enumerate(con_fecha):
        m.fecha = m.fecha + timedelta(seconds=i)
    ordenados = sin_fecha + con_fecha

    # Stock inicial tal que el stock final sea el "Stock actual" del Excel
    neto: dict[str, Decimal] = defaultdict(Decimal)
    for m in ordenados:
        neto[m.codigo] += m.cantidad if m.tipo == TipoMovimiento.ENTRADA else -m.cantidad
    for p in productos:
        p.stock_inicial = p.stock_actual_excel - neto[p.codigo]
        if p.stock_inicial != p.stock_inicial_excel:
            avisos.append(
                f"{p.codigo} {p.nombre} {p.presentacion or ''}: el Excel dice stock inicial"
                f" {p.stock_inicial_excel}, pero con sus movimientos el stock actual"
                f" ({p.stock_actual_excel}) solo cuadra con {p.stock_inicial}; se usa"
                f" {p.stock_inicial}"
            )
        if p.stock_inicial < 0:
            raise ValueError(f"{p.codigo}: el stock inicial calculado es negativo")

    # Simulación: ningún movimiento puede dejar el stock negativo
    stock = {p.codigo: p.stock_inicial for p in productos}
    for m in ordenados:
        stock[m.codigo] += m.cantidad if m.tipo == TipoMovimiento.ENTRADA else -m.cantidad
        if stock[m.codigo] < 0:
            raise ValueError(f"Movimientos fila {m.fila}: el stock de {m.codigo} queda negativo")

    return Plan(productos=productos, movimientos=ordenados, avisos=avisos)


def aplicar(db: Session, plan: Plan, usuario: Usuario) -> None:
    """Crea los productos y registra los movimientos con el servicio de inventario."""
    codigos = [p.codigo for p in plan.productos]
    existentes = db.scalars(select(Producto.codigo).where(Producto.codigo.in_(codigos))).all()
    if existentes:
        raise ValueError(f"Ya existen productos con estos códigos: {', '.join(existentes)}")

    ids: dict[str, int] = {}
    for p in plan.productos:
        producto = Producto(
            codigo=p.codigo,
            nombre=p.nombre,
            presentacion=p.presentacion,
            unidad=Unidad.CAJA,
            precio_compra=p.precio_compra,
            precio_venta=Decimal(0),
            stock_minimo=STOCK_MINIMO,
        )
        db.add(producto)
        db.flush()
        ids[p.codigo] = producto.id
    db.commit()

    # El stock inicial va justo antes del primer movimiento
    inicio = min((m.fecha for m in plan.movimientos), default=datetime.now(ZONA))
    for p in plan.productos:
        if p.stock_inicial > 0:
            inventario.registrar_movimiento(
                db,
                producto_id=ids[p.codigo],
                usuario=usuario,
                tipo=TipoMovimiento.ENTRADA,
                motivo=Motivo.AJUSTE,
                cantidad=p.stock_inicial,
                comentario=COMENTARIO_INICIAL,
                fecha=inicio - timedelta(hours=1),
            )
    for m in plan.movimientos:
        inventario.registrar_movimiento(
            db,
            producto_id=ids[m.codigo],
            usuario=usuario,
            tipo=m.tipo,
            motivo=m.motivo,
            cantidad=m.cantidad,
            comentario=m.comentario,
            pedido=m.pedido,
            responsable=m.responsable,
            fecha=m.fecha,
        )


def _mostrar(plan: Plan) -> None:
    print(f"Productos ({len(plan.productos)}):")
    for p in plan.productos:
        print(
            f"  {p.codigo}  {p.nombre} {p.presentacion or ''}  inicial {p.stock_inicial}"
            f"  final {p.stock_actual_excel}  compra {p.precio_compra}"
        )
    print(f"Movimientos ({len(plan.movimientos)}):")
    for m in plan.movimientos:
        print(
            f"  {m.fecha:%Y-%m-%d %H:%M}  {m.codigo}  {m.tipo:<7} {m.motivo:<7} {m.cantidad:>4}"
            f"  {m.responsable or ''}  {m.comentario or ''}"
        )
    for aviso in plan.avisos:
        print(f"AVISO: {aviso}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--aplicar", action="store_true", help="guardar en la base")
    args = parser.parse_args()

    plan = armar_plan(args.archivo)
    _mostrar(plan)
    if not args.aplicar:
        print("\nNo se guardó nada. Usa --aplicar para importar.")
        return
    with SessionLocal() as db:
        admin = db.scalar(
            select(Usuario)
            .where(Usuario.rol == Rol.ADMIN, Usuario.activo.is_(True))
            .order_by(Usuario.id)
        )
        if admin is None:
            raise SystemExit("No hay un ADMIN activo para firmar los movimientos")
        aplicar(db, plan, admin)
    print(f"\nImportado a nombre de {admin.nombre}.")


if __name__ == "__main__":
    main()
