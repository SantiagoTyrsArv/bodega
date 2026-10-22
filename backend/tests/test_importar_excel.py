from datetime import datetime
from decimal import Decimal

import pytest
from openpyxl import Workbook
from sqlalchemy import select

from app.importar_excel import aplicar, armar_plan
from app.modelos import Motivo, Movimiento, Producto, Rol

ENCABEZADO_INVENTARIO = [
    "ID", "Producto", "Presentación", "Stock inicial", "Entradas", "Salidas",
    "Stock actual", "Precio unitario", "Valor actual", "Estado",
]  # fmt: skip
ENCABEZADO_MOVIMIENTOS = [
    "Fecha", "ID Producto", "Producto", "Presentación", "Cantidad", "Tipo",
    "N° Pedido", "Cliente / Responsable", "Observaciones",
]  # fmt: skip


def libro(tmp_path, inventario, movimientos):
    """Excel con el mismo formato que el original: título, encabezado y datos."""
    wb = Workbook()
    hoja = wb.active
    hoja.title = "Inventario"
    hoja.append(["CONTROL DE INVENTARIO – BODEGA"])
    hoja.append(ENCABEZADO_INVENTARIO)
    for fila in inventario:
        hoja.append(fila)
    hoja.append(["P099", None, None, None, 0, 0, 0, None, None, "REVISAR STOCK"])  # vacía
    hoja = wb.create_sheet("Movimientos")
    hoja.append(["REGISTRO DE ENTRADAS Y SALIDAS DE BODEGA"])
    hoja.append(ENCABEZADO_MOVIMIENTOS)
    for fila in movimientos:
        hoja.append(fila)
    ruta = tmp_path / "inventario.xlsx"
    wb.save(ruta)
    return ruta


INVENTARIO = [
    ["P001", "Coca-Cola", "1.5 L", 26, 4, 8, 22, 63000, None, "OK"],
    # La entrada de P002 ya era el stock inicial: el stock actual es 2, no 4
    ["P002", "Jugo Valle", "400 ml", 2, None, 0, 2, 20000, None, "OK"],
]
MOVIMIENTOS = [
    [None, "P001", "Coca-Cola", "1.5 L", None, None, None, "karen", "completar la fecha"],
    [None, "p001", "Coca-Cola", "1.5 L", 2, "Salida", None, "karen", None],
    [None, "P002", "Jugo Valle", "400 ml", 2, "Entrada", None, None, None],
    [None, "p001", "Coca-Cola", "1.5 L", 6, "salida", "77", "riben ", "pendiente"],
    [datetime(2026, 10, 20), "P001", "Coca-Cola", "1.5 L", 4, "Entrada", None, "compra ", None],
    [datetime(2026, 10, 17), "P001", "Coca-Cola", "1.5 L", 1, "Salida", None, "venta", None],
]


def test_plan_ordena_y_cuadra_el_stock(tmp_path):
    plan = armar_plan(libro(tmp_path, INVENTARIO, MOVIMIENTOS))

    assert [p.codigo for p in plan.productos] == ["P001", "P002"]
    p001, p002 = plan.productos
    assert p001.stock_inicial == 27  # actual 22 - entrada 4 + salidas 2, 6 y 1
    assert any("P001" in a for a in plan.avisos)  # el Excel decía 26
    assert p002.stock_inicial == 0
    assert any("P002" in a for a in plan.avisos)  # el Excel decía 2
    assert any("fila 3" in a for a in plan.avisos)  # la fila sin cantidad se omite

    # Sin fecha primero (en el orden de la hoja) y luego por fecha
    assert [m.cantidad for m in plan.movimientos] == [2, 2, 6, 1, 4]
    venta, compra = plan.movimientos[3], plan.movimientos[4]
    assert venta.motivo == Motivo.VENTA and venta.responsable is None
    assert compra.motivo == Motivo.COMPRA
    riben = plan.movimientos[2]
    assert riben.responsable == "Ruben" and riben.pedido == "77"
    assert riben.comentario == "pendiente; fecha no registrada en el Excel"
    assert plan.movimientos[0].fecha.date().isoformat() == "2026-10-16"


def test_plan_rechaza_stock_negativo(tmp_path):
    inventario = [["P001", "Coca-Cola", "1.5 L", 0, 5, 0, 5, 63000, None, "OK"]]
    movimientos = [
        [datetime(2026, 10, 17), "P001", "Coca-Cola", "1.5 L", 1, "Salida", None, None, None],
        [datetime(2026, 10, 18), "P001", "Coca-Cola", "1.5 L", 6, "Entrada", None, None, None],
    ]
    with pytest.raises(ValueError, match="negativo"):
        armar_plan(libro(tmp_path, inventario, movimientos))


def test_aplicar_crea_productos_y_movimientos(tmp_path, db, crear_usuario):
    admin = crear_usuario("admin2@prueba.local", rol=Rol.ADMIN)
    plan = armar_plan(libro(tmp_path, INVENTARIO, MOVIMIENTOS))
    aplicar(db, plan, admin)

    p001 = db.scalar(select(Producto).where(Producto.codigo == "P001"))
    assert p001.stock == 22 and p001.unidad == "CAJA" and p001.presentacion == "1.5 L"
    assert p001.precio_compra == Decimal(63000) and p001.stock_minimo == 5
    p002 = db.scalar(select(Producto).where(Producto.codigo == "P002"))
    assert p002.stock == 2

    movimientos = db.scalars(
        select(Movimiento).where(Movimiento.producto_id == p001.id).order_by(Movimiento.fecha)
    ).all()
    assert movimientos[0].motivo == Motivo.AJUSTE and movimientos[0].cantidad == 27
    assert [m.stock_despues for m in movimientos] == [27, 25, 19, 18, 22]
    assert movimientos[-1].precio_unitario == Decimal(63000)

    # Importar dos veces no duplica
    with pytest.raises(ValueError, match="Ya existen"):
        aplicar(db, plan, admin)
