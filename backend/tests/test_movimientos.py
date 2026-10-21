import threading
from decimal import Decimal

import pytest

from app.db import SessionLocal
from app.modelos import Movimiento, Producto, Rol, Usuario
from app.servicios import inventario
from app.servicios.inventario import ErrorInventario


@pytest.fixture
def admin(crear_usuario, headers_de):
    crear_usuario("admin2@prueba.local", rol=Rol.ADMIN)
    return headers_de("admin2@prueba.local")


@pytest.fixture
def usuario(crear_usuario, headers_de):
    crear_usuario("ana@prueba.local")
    return headers_de("ana@prueba.local")


@pytest.fixture
def producto(cliente, admin):
    datos = {
        "codigo": "770100",
        "nombre": "Arroz",
        "unidad": "KG",
        "precio_compra": "2500.00",
        "precio_venta": "3200.00",
    }
    r = cliente.post("/api/productos", json=datos, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


def mover(cliente, headers, producto_id, tipo, cantidad, motivo=None, **extra):
    motivo = motivo or ("COMPRA" if tipo == "ENTRADA" else "USO")
    datos = {"producto_id": producto_id, "tipo": tipo, "motivo": motivo, "cantidad": cantidad}
    return cliente.post("/api/movimientos", json={**datos, **extra}, headers=headers)


def stock(cliente, headers, producto_id):
    return cliente.get(f"/api/productos/{producto_id}", headers=headers).json()["stock"]


# --- Entradas y salidas ---


def test_entrada_suma_stock_y_guarda_stock_despues(cliente, usuario, producto):
    r = mover(cliente, usuario, producto["id"], "ENTRADA", "10.5")
    assert r.status_code == 201, r.text
    m = r.json()
    assert m["stock_despues"] == "10.500"
    assert m["tipo"] == "ENTRADA"
    assert m["usuario"]["nombre"] == "ana"
    assert m["producto"]["nombre"] == "Arroz"
    assert stock(cliente, usuario, producto["id"]) == "10.500"

    r = mover(cliente, usuario, producto["id"], "ENTRADA", "2")
    assert r.json()["stock_despues"] == "12.500"


def test_salida_resta_stock(cliente, usuario, producto):
    mover(cliente, usuario, producto["id"], "ENTRADA", "10")
    r = mover(cliente, usuario, producto["id"], "SALIDA", "4", motivo="VENTA")
    assert r.status_code == 201
    assert r.json()["stock_despues"] == "6.000"
    assert stock(cliente, usuario, producto["id"]) == "6.000"


def test_salida_mayor_al_stock_da_409_y_no_cambia_nada(cliente, usuario, producto, db):
    mover(cliente, usuario, producto["id"], "ENTRADA", "5")
    r = mover(cliente, usuario, producto["id"], "SALIDA", "5.001")
    assert r.status_code == 409
    assert r.json() == {"detail": "Stock insuficiente: quedan 5 kg"}
    assert stock(cliente, usuario, producto["id"]) == "5.000"
    assert db.query(Movimiento).count() == 1


def test_salida_de_todo_el_stock_deja_cero(cliente, usuario, producto):
    mover(cliente, usuario, producto["id"], "ENTRADA", "5")
    r = mover(cliente, usuario, producto["id"], "SALIDA", "5")
    assert r.status_code == 201
    assert r.json()["stock_despues"] == "0.000"


def test_precio_por_defecto_segun_tipo(cliente, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "5").json()
    salida = mover(cliente, usuario, producto["id"], "SALIDA", "1").json()
    assert entrada["precio_unitario"] == "2500.00"
    assert salida["precio_unitario"] == "3200.00"

    otra = mover(cliente, usuario, producto["id"], "SALIDA", "1", precio_unitario="3000")
    assert otra.json()["precio_unitario"] == "3000.00"


def test_motivo_debe_corresponder_al_tipo(cliente, usuario, producto):
    casos = [("ENTRADA", "VENTA"), ("SALIDA", "COMPRA"), ("ENTRADA", "ANULACION")]
    for tipo, motivo in casos:
        r = mover(cliente, usuario, producto["id"], tipo, "1", motivo=motivo)
        assert r.status_code == 422, (tipo, motivo)
        assert r.json()["detail"].startswith("Motivo no válido")


def test_cantidad_debe_ser_positiva(cliente, usuario, producto):
    for cantidad in ("0", "-1", "1.0001"):
        assert mover(cliente, usuario, producto["id"], "ENTRADA", cantidad).status_code == 422


def test_producto_inexistente_o_desactivado(cliente, admin, usuario, producto):
    assert mover(cliente, usuario, 999, "ENTRADA", "1").status_code == 404
    cliente.patch(f"/api/productos/{producto['id']}", json={"activo": False}, headers=admin)
    r = mover(cliente, usuario, producto["id"], "ENTRADA", "1")
    assert r.status_code == 409
    assert r.json() == {"detail": "El producto está desactivado"}


def test_admin_puede_actualizar_precio_de_compra_con_una_entrada(cliente, admin, producto):
    mover(
        cliente,
        admin,
        producto["id"],
        "ENTRADA",
        "1",
        precio_unitario="2700",
        actualizar_precio=True,
    )
    p = cliente.get(f"/api/productos/{producto['id']}", headers=admin).json()
    assert p["precio_compra"] == "2700.00"

    # Sin la marca, el precio del producto no cambia
    mover(cliente, admin, producto["id"], "ENTRADA", "1", precio_unitario="9999")
    p = cliente.get(f"/api/productos/{producto['id']}", headers=admin).json()
    assert p["precio_compra"] == "2700.00"


def test_usuario_recibe_403_al_actualizar_precio(cliente, usuario, producto):
    r = mover(
        cliente,
        usuario,
        producto["id"],
        "ENTRADA",
        "1",
        precio_unitario="1",
        actualizar_precio=True,
    )
    assert r.status_code == 403
    assert stock(cliente, usuario, producto["id"]) == "0.000"


def test_movimientos_requieren_sesion(cliente, producto):
    assert cliente.post("/api/movimientos", json={}).status_code == 401
    assert cliente.get("/api/movimientos").status_code == 401


# --- Anulación ---


def test_anular_una_entrada_resta_el_stock(cliente, admin, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "10").json()
    mover(cliente, usuario, producto["id"], "ENTRADA", "3")

    r = cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=admin)
    assert r.status_code == 201, r.text
    anulacion = r.json()
    assert anulacion["tipo"] == "SALIDA"
    assert anulacion["motivo"] == "ANULACION"
    assert anulacion["anula_a"] == entrada["id"]
    assert anulacion["cantidad"] == "10.000"
    assert anulacion["stock_despues"] == "3.000"
    assert stock(cliente, usuario, producto["id"]) == "3.000"


def test_anular_dos_veces_falla(cliente, admin, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "10").json()
    cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=admin)
    r = cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=admin)
    assert r.status_code == 409
    assert r.json() == {"detail": "Este movimiento ya fue anulado"}
    assert stock(cliente, usuario, producto["id"]) == "0.000"


def test_una_anulacion_no_se_puede_anular(cliente, admin, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "10").json()
    anulacion = cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=admin).json()
    r = cliente.post(f"/api/movimientos/{anulacion['id']}/anular", headers=admin)
    assert r.status_code == 409
    assert r.json() == {"detail": "Una anulación no se puede anular"}


def test_anular_una_salida_devuelve_el_stock(cliente, admin, usuario, producto):
    mover(cliente, usuario, producto["id"], "ENTRADA", "10")
    salida = mover(cliente, usuario, producto["id"], "SALIDA", "4").json()
    r = cliente.post(f"/api/movimientos/{salida['id']}/anular", headers=admin)
    assert r.json()["tipo"] == "ENTRADA"
    assert stock(cliente, usuario, producto["id"]) == "10.000"


def test_no_se_anula_una_entrada_si_el_stock_ya_se_uso(cliente, admin, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "10").json()
    mover(cliente, usuario, producto["id"], "SALIDA", "8")
    r = cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=admin)
    assert r.status_code == 409
    assert r.json() == {"detail": "Stock insuficiente: quedan 2 kg"}


def test_usuario_recibe_403_al_anular(cliente, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "10").json()
    r = cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=usuario)
    assert r.status_code == 403
    assert stock(cliente, usuario, producto["id"]) == "10.000"


def test_anular_movimiento_inexistente(cliente, admin):
    r = cliente.post("/api/movimientos/999/anular", headers=admin)
    assert r.status_code == 404
    assert r.json() == {"detail": "El movimiento no existe"}


def test_listado_marca_los_movimientos_anulados(cliente, admin, usuario, producto):
    entrada = mover(cliente, usuario, producto["id"], "ENTRADA", "10").json()
    anulacion = cliente.post(f"/api/movimientos/{entrada['id']}/anular", headers=admin).json()
    items = cliente.get("/api/movimientos", headers=usuario).json()["items"]
    por_id = {m["id"]: m for m in items}
    assert por_id[entrada["id"]]["anulado_por"] == anulacion["id"]
    assert por_id[anulacion["id"]]["anulado_por"] is None


# --- Consultas ---


def test_listar_con_filtros_y_paginacion(cliente, admin, usuario, producto):
    otro = cliente.post(
        "/api/productos",
        json={
            **{k: producto[k] for k in ("precio_compra", "precio_venta")},
            "codigo": "2",
            "nombre": "Sal",
            "unidad": "UNIDAD",
        },
        headers=admin,
    ).json()
    for _ in range(3):
        mover(cliente, usuario, producto["id"], "ENTRADA", "1")
    mover(cliente, usuario, producto["id"], "SALIDA", "1")
    mover(cliente, usuario, otro["id"], "ENTRADA", "1")

    todo = cliente.get("/api/movimientos", headers=usuario).json()
    assert todo["total"] == 5
    # Los más recientes primero
    assert todo["items"][0]["producto"]["nombre"] == "Sal"

    r = cliente.get("/api/movimientos?tipo=SALIDA", headers=usuario).json()
    assert r["total"] == 1

    r = cliente.get(f"/api/movimientos?producto_id={producto['id']}", headers=usuario).json()
    assert r["total"] == 4

    r = cliente.get("/api/movimientos?por_pagina=2&pagina=3", headers=usuario).json()
    assert len(r["items"]) == 1
    assert r["pagina"] == 3

    historial = cliente.get(f"/api/productos/{otro['id']}/movimientos", headers=usuario).json()
    assert historial["total"] == 1


def test_listar_por_rango_de_fechas(cliente, usuario, producto, db):
    mover(cliente, usuario, producto["id"], "ENTRADA", "1")
    viejo = mover(cliente, usuario, producto["id"], "ENTRADA", "1").json()
    db.get(Movimiento, viejo["id"]).fecha = db.get(Movimiento, viejo["id"]).fecha.replace(year=2020)
    db.commit()

    r = cliente.get("/api/movimientos?desde=2021-01-01T00:00:00-05:00", headers=usuario).json()
    assert r["total"] == 1
    r = cliente.get("/api/movimientos?hasta=2021-01-01T00:00:00-05:00", headers=usuario).json()
    assert [m["id"] for m in r["items"]] == [viejo["id"]]


# --- Concurrencia ---


def test_dos_salidas_simultaneas_no_dejan_stock_negativo(cliente, usuario, producto, db):
    mover(cliente, usuario, producto["id"], "ENTRADA", "10")
    ana = db.query(Usuario).filter_by(correo="ana@prueba.local").one()
    resultados: list[str] = []
    barrera = threading.Barrier(5)

    def sacar_todo():
        with SessionLocal() as sesion:
            barrera.wait()
            try:
                inventario.registrar_movimiento(
                    sesion,
                    producto_id=producto["id"],
                    usuario=sesion.get(Usuario, ana.id),
                    tipo="SALIDA",
                    motivo="USO",
                    cantidad=Decimal(10),
                )
                resultados.append("ok")
            except ErrorInventario as e:
                resultados.append(e.mensaje)

    hilos = [threading.Thread(target=sacar_todo) for _ in range(5)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert sorted(resultados) == ["Stock insuficiente: quedan 0 kg"] * 4 + ["ok"]
    db.expire_all()
    assert db.get(Producto, producto["id"]).stock == 0
