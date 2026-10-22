from decimal import Decimal

import pytest

from app.modelos import Rol


@pytest.fixture
def admin(crear_usuario, headers_de):
    crear_usuario("admin2@prueba.local", rol=Rol.ADMIN)
    return headers_de("admin2@prueba.local")


@pytest.fixture
def usuario(crear_usuario, headers_de):
    crear_usuario("ana@prueba.local")
    return headers_de("ana@prueba.local")


def crear(cliente, admin, codigo, compra, venta, minimo="0", unidad="UNIDAD"):
    datos = {
        "codigo": codigo,
        "nombre": f"Producto {codigo}",
        "unidad": unidad,
        "precio_compra": compra,
        "precio_venta": venta,
        "stock_minimo": minimo,
    }
    r = cliente.post("/api/productos", json=datos, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


def entrada(cliente, headers, producto_id, cantidad):
    datos = {
        "producto_id": producto_id,
        "tipo": "ENTRADA",
        "motivo": "COMPRA",
        "cantidad": cantidad,
    }
    r = cliente.post("/api/movimientos", json=datos, headers=headers)
    assert r.status_code == 201, r.text


def test_resumen_vacio(cliente, usuario):
    r = cliente.get("/api/resumen", headers=usuario)
    assert r.status_code == 200
    assert r.json() == {
        "total_productos": 0,
        "valor_compra": "0.00",
        "valor_venta": "0.00",
        "bajo_minimo": [],
        "ultimos_movimientos": [],
    }


def test_valor_del_inventario_es_la_suma_de_stock_por_precio(cliente, admin, usuario):
    # Cantidades con decimales para comprobar que no se pierde precisión
    casos = [
        ("A1", "2500.00", "3200.00", "10.5"),
        ("B2", "1999.99", "2500.50", "3.125"),
        ("C3", "0.01", "0.03", "7"),
    ]
    for codigo, compra, venta, cantidad in casos:
        p = crear(cliente, admin, codigo, compra, venta, unidad="KG")
        entrada(cliente, usuario, p["id"], cantidad)
    # Un producto sin stock no suma
    crear(cliente, admin, "D4", "100.00", "150.00")

    datos = cliente.get("/api/resumen", headers=usuario).json()
    productos = cliente.get("/api/productos", headers=usuario).json()
    esperado_compra = sum(Decimal(p["stock"]) * Decimal(p["precio_compra"]) for p in productos)
    esperado_venta = sum(Decimal(p["stock"]) * Decimal(p["precio_venta"]) for p in productos)

    assert datos["total_productos"] == 4
    assert Decimal(datos["valor_compra"]) == esperado_compra.quantize(Decimal("0.01"))
    assert Decimal(datos["valor_venta"]) == esperado_venta.quantize(Decimal("0.01"))
    # 10.5 × 2500 + 3.125 × 1999.99 + 7 × 0.01 = 26250 + 6249.96875 + 0.07
    assert datos["valor_compra"] == "32500.04"


def test_productos_desactivados_no_cuentan(cliente, admin, usuario):
    p = crear(cliente, admin, "A1", "1000.00", "2000.00", minimo="5")
    entrada(cliente, usuario, p["id"], "2")
    r = cliente.patch(f"/api/productos/{p['id']}", json={"activo": False}, headers=admin)
    assert r.status_code == 200

    datos = cliente.get("/api/resumen", headers=usuario).json()
    assert datos["total_productos"] == 0
    assert datos["valor_compra"] == "0.00"
    assert datos["bajo_minimo"] == []


def test_bajo_minimo(cliente, admin, usuario):
    bajo = crear(cliente, admin, "A1", "10.00", "20.00", minimo="5")
    entrada(cliente, usuario, bajo["id"], "3")
    justo = crear(cliente, admin, "B2", "10.00", "20.00", minimo="5")
    entrada(cliente, usuario, justo["id"], "5")
    sobra = crear(cliente, admin, "C3", "10.00", "20.00", minimo="5")
    entrada(cliente, usuario, sobra["id"], "6")
    crear(cliente, admin, "D4", "10.00", "20.00")  # sin mínimo definido: nunca está bajo

    codigos = [
        p["codigo"] for p in cliente.get("/api/resumen", headers=usuario).json()["bajo_minimo"]
    ]
    assert codigos == ["A1", "B2"]


def test_ultimos_diez_movimientos_del_mas_reciente(cliente, admin, usuario):
    p = crear(cliente, admin, "A1", "10.00", "20.00")
    for i in range(1, 13):
        entrada(cliente, usuario, p["id"], str(i))

    ultimos = cliente.get("/api/resumen", headers=usuario).json()["ultimos_movimientos"]
    assert len(ultimos) == 10
    assert [m["cantidad"] for m in ultimos] == [f"{i}.000" for i in range(12, 2, -1)]


def test_resumen_requiere_sesion(cliente):
    assert cliente.get("/api/resumen").status_code == 401
