import pytest

from app.modelos import Rol

PRODUCTO = {
    "codigo": "7701234567890",
    "nombre": "Arroz 1 kg",
    "unidad": "UNIDAD",
    "precio_compra": "2500.00",
    "precio_venta": "3200.50",
    "stock_minimo": "10",
}


@pytest.fixture
def admin(crear_usuario, headers_de):
    crear_usuario("admin2@prueba.local", rol=Rol.ADMIN)
    return headers_de("admin2@prueba.local")


@pytest.fixture
def usuario(crear_usuario, headers_de):
    crear_usuario("ana@prueba.local")
    return headers_de("ana@prueba.local")


def crear_producto(cliente, headers, **cambios):
    r = cliente.post("/api/productos", json={**PRODUCTO, **cambios}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# --- Categorías ---


def test_admin_crea_y_edita_categorias(cliente, admin, usuario):
    r = cliente.post("/api/categorias", json={"nombre": "  Granos "}, headers=admin)
    assert r.status_code == 201
    assert r.json()["nombre"] == "Granos"
    cid = r.json()["id"]

    r = cliente.patch(f"/api/categorias/{cid}", json={"nombre": "Abarrotes"}, headers=admin)
    assert r.json()["nombre"] == "Abarrotes"

    # USUARIO también ve las categorías
    r = cliente.get("/api/categorias", headers=usuario)
    assert [c["nombre"] for c in r.json()] == ["Abarrotes"]


def test_categoria_duplicada_sin_importar_mayusculas(cliente, admin):
    cliente.post("/api/categorias", json={"nombre": "Granos"}, headers=admin)
    r = cliente.post("/api/categorias", json={"nombre": "granos"}, headers=admin)
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe una categoría con ese nombre"}


def test_usuario_no_crea_ni_edita_categorias(cliente, admin, usuario):
    cid = cliente.post("/api/categorias", json={"nombre": "Granos"}, headers=admin).json()["id"]
    assert cliente.post("/api/categorias", json={"nombre": "X"}, headers=usuario).status_code == 403
    r = cliente.patch(f"/api/categorias/{cid}", json={"nombre": "X"}, headers=usuario)
    assert r.status_code == 403


# --- Productos ---


def test_admin_crea_producto_con_stock_en_cero(cliente, admin):
    cid = cliente.post("/api/categorias", json={"nombre": "Granos"}, headers=admin).json()["id"]
    p = crear_producto(cliente, admin, categoria_id=cid)
    assert p["stock"] == "0.000"
    assert p["precio_venta"] == "3200.50"
    assert p["categoria"] == {"id": cid, "nombre": "Granos"}
    assert p["activo"] is True


def test_no_se_puede_enviar_stock(cliente, admin):
    r = cliente.post("/api/productos", json={**PRODUCTO, "stock": "50"}, headers=admin)
    assert r.status_code == 422
    p = crear_producto(cliente, admin)
    r = cliente.patch(f"/api/productos/{p['id']}", json={"stock": "50"}, headers=admin)
    assert r.status_code == 422
    assert r.json() == {"detail": "Dato inválido en 'stock'"}
    assert cliente.get(f"/api/productos/{p['id']}", headers=admin).json()["stock"] == "0.000"


def test_codigo_duplicado(cliente, admin):
    crear_producto(cliente, admin)
    r = cliente.post("/api/productos", json=PRODUCTO, headers=admin)
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un producto con el código 7701234567890"}


def test_validaciones_de_producto(cliente, admin):
    casos = [
        {"precio_compra": "-1"},
        {"precio_venta": "1.234"},  # más de 2 decimales
        {"unidad": "LATA"},
        {"nombre": "   "},
        {"categoria_id": 999},
    ]
    for cambio in casos:
        r = cliente.post("/api/productos", json={**PRODUCTO, **cambio}, headers=admin)
        assert r.status_code == 422, cambio


def test_usuario_recibe_403_al_crear_productos_o_cambiar_precios(cliente, admin, usuario):
    assert cliente.post("/api/productos", json=PRODUCTO, headers=usuario).status_code == 403
    p = crear_producto(cliente, admin)
    r = cliente.patch(f"/api/productos/{p['id']}", json={"precio_venta": "1"}, headers=usuario)
    assert r.status_code == 403
    r = cliente.patch(f"/api/productos/{p['id']}", json={"activo": False}, headers=usuario)
    assert r.status_code == 403


def test_admin_edita_y_desactiva(cliente, admin, usuario):
    p = crear_producto(cliente, admin)
    r = cliente.patch(
        f"/api/productos/{p['id']}",
        json={"precio_venta": "3500", "nombre": "Arroz premium", "nota": None},
        headers=admin,
    )
    assert r.status_code == 200
    assert r.json()["precio_venta"] == "3500.00"
    assert r.json()["nombre"] == "Arroz premium"

    r = cliente.patch(f"/api/productos/{p['id']}", json={"nombre": None}, headers=admin)
    assert r.status_code == 422

    cliente.patch(f"/api/productos/{p['id']}", json={"activo": False}, headers=admin)
    assert cliente.get("/api/productos", headers=usuario).json() == []
    inactivos = cliente.get("/api/productos?activo=false", headers=usuario).json()
    assert [x["id"] for x in inactivos] == [p["id"]]


def test_buscar_por_nombre_codigo_y_categoria(cliente, admin, usuario):
    cid = cliente.post("/api/categorias", json={"nombre": "Aseo"}, headers=admin).json()["id"]
    crear_producto(cliente, admin)
    crear_producto(cliente, admin, codigo="111", nombre="Jabón", categoria_id=cid)

    def nombres(consulta):
        r = cliente.get(f"/api/productos{consulta}", headers=usuario)
        return [p["nombre"] for p in r.json()]

    assert nombres("") == ["Arroz 1 kg", "Jabón"]
    assert nombres("?q=arroz") == ["Arroz 1 kg"]
    assert nombres("?q=7701") == ["Arroz 1 kg"]
    assert nombres(f"?categoria_id={cid}") == ["Jabón"]


def test_filtro_bajo_minimo(cliente, admin, usuario):
    crear_producto(cliente, admin, codigo="1", nombre="Sin mínimo", stock_minimo="0")
    crear_producto(cliente, admin, codigo="2", nombre="Bajo")
    justo = crear_producto(cliente, admin, codigo="3", nombre="Justo en el mínimo")
    sobre = crear_producto(cliente, admin, codigo="4", nombre="Sobre")
    for producto, cantidad in ((justo, "10"), (sobre, "11")):
        movimiento = {"producto_id": producto["id"], "tipo": "ENTRADA", "motivo": "COMPRA"}
        r = cliente.post(
            "/api/movimientos", json={**movimiento, "cantidad": cantidad}, headers=admin
        )
        assert r.status_code == 201

    r = cliente.get("/api/productos?bajo_minimo=true", headers=usuario)
    assert [p["nombre"] for p in r.json()] == ["Bajo", "Justo en el mínimo"]


def test_resolver_codigo_escaneado(cliente, admin, usuario):
    p = crear_producto(cliente, admin)
    r = cliente.get("/api/productos/codigo/7701234567890", headers=usuario)
    assert r.status_code == 200
    assert r.json()["id"] == p["id"]


def test_codigo_inexistente_devuelve_404(cliente, usuario):
    r = cliente.get("/api/productos/codigo/000000", headers=usuario)
    assert r.status_code == 404
    assert r.json() == {"detail": "No existe un producto con el código 000000"}


def test_productos_requieren_sesion(cliente):
    assert cliente.get("/api/productos").status_code == 401
    assert cliente.get("/api/categorias").status_code == 401
