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


NUEVO = {"nombre": "Luis", "correo": "  Luis@Prueba.Local ", "clave": "clave-segura"}


def crear(cliente, admin, **cambios):
    return cliente.post("/api/usuarios", json={**NUEVO, **cambios}, headers=admin)


def login(cliente, correo, clave):
    return cliente.post("/api/auth/login", json={"correo": correo, "clave": clave})


def test_admin_crea_usuario_que_puede_entrar(cliente, admin):
    r = crear(cliente, admin)
    assert r.status_code == 201, r.text
    datos = r.json()
    assert datos["correo"] == "luis@prueba.local"
    assert datos["rol"] == "USUARIO" and datos["activo"] is True
    assert "clave" not in datos and "clave_hash" not in datos
    assert login(cliente, "luis@prueba.local", "clave-segura").status_code == 200


def test_correo_repetido_da_409(cliente, admin):
    crear(cliente, admin)
    r = crear(cliente, admin, correo="LUIS@prueba.local")
    assert r.status_code == 409
    assert r.json()["detail"] == "Ya existe un usuario con el correo luis@prueba.local"


def test_validaciones_al_crear(cliente, admin):
    r = crear(cliente, admin, clave="corta")
    assert r.status_code == 422
    assert r.json()["detail"] == "La clave debe tener al menos 8 caracteres"
    assert crear(cliente, admin, correo="sin-arroba").status_code == 422
    assert crear(cliente, admin, nombre="  ").status_code == 422


def test_listar_usuarios(cliente, admin, usuario):
    r = cliente.get("/api/usuarios", headers=admin)
    assert r.status_code == 200
    correos = [u["correo"] for u in r.json()]
    # El ADMIN inicial de la app, el de la prueba y la usuaria
    assert set(correos) == {"admin@prueba.local", "admin2@prueba.local", "ana@prueba.local"}


def test_usuario_recibe_403(cliente, usuario):
    assert cliente.get("/api/usuarios", headers=usuario).status_code == 403
    assert crear(cliente, usuario).status_code == 403
    assert (
        cliente.patch("/api/usuarios/1", json={"rol": "USUARIO"}, headers=usuario).status_code
        == 403
    )


def test_editar_nombre_rol_y_clave(cliente, admin):
    id_ = crear(cliente, admin).json()["id"]
    cambios = {"nombre": "Luis Pérez", "rol": "ADMIN", "clave": "otra-clave-larga"}
    r = cliente.patch(f"/api/usuarios/{id_}", json=cambios, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["nombre"] == "Luis Pérez" and r.json()["rol"] == "ADMIN"
    assert login(cliente, "luis@prueba.local", "clave-segura").status_code == 401
    assert login(cliente, "luis@prueba.local", "otra-clave-larga").status_code == 200

    r = cliente.patch(f"/api/usuarios/{id_}", json={"clave": "corta"}, headers=admin)
    assert r.status_code == 422


def test_cambiar_correo_a_uno_ocupado_da_409(cliente, admin, usuario):
    id_ = crear(cliente, admin).json()["id"]
    r = cliente.patch(f"/api/usuarios/{id_}", json={"correo": "ana@prueba.local"}, headers=admin)
    assert r.status_code == 409


def test_desactivar_corta_el_acceso_de_inmediato(cliente, admin, headers_de):
    id_ = crear(cliente, admin).json()["id"]
    sesion = headers_de("luis@prueba.local", "clave-segura")
    assert cliente.get("/api/auth/yo", headers=sesion).status_code == 200

    r = cliente.patch(f"/api/usuarios/{id_}", json={"activo": False}, headers=admin)
    assert r.status_code == 200 and r.json()["activo"] is False
    assert cliente.get("/api/auth/yo", headers=sesion).status_code == 401
    assert login(cliente, "luis@prueba.local", "clave-segura").status_code == 401

    # Al reactivarlo vuelve a entrar
    cliente.patch(f"/api/usuarios/{id_}", json={"activo": True}, headers=admin)
    assert login(cliente, "luis@prueba.local", "clave-segura").status_code == 200


def test_admin_no_puede_dejarse_fuera(cliente, admin):
    yo = cliente.get("/api/auth/yo", headers=admin).json()
    r = cliente.patch(f"/api/usuarios/{yo['id']}", json={"activo": False}, headers=admin)
    assert r.status_code == 409
    assert r.json()["detail"] == "No puedes desactivar tu propio usuario"
    r = cliente.patch(f"/api/usuarios/{yo['id']}", json={"rol": "USUARIO"}, headers=admin)
    assert r.status_code == 409
    assert r.json()["detail"] == "No puedes cambiar tu propio rol"
    # Sí puede cambiar su nombre (y reenviar su mismo rol)
    r = cliente.patch(
        f"/api/usuarios/{yo['id']}", json={"nombre": "Jefa", "rol": "ADMIN"}, headers=admin
    )
    assert r.status_code == 200 and r.json()["nombre"] == "Jefa"


def test_editar_usuario_inexistente(cliente, admin):
    assert (
        cliente.patch("/api/usuarios/999", json={"nombre": "X"}, headers=admin).status_code == 404
    )
