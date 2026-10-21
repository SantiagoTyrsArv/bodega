from datetime import timedelta

from app.modelos import Rol
from app.seguridad import _crear_token, crear_refresh_token
from tests.conftest import CLAVE


def test_arranque_crea_admin_inicial(cliente, headers_de):
    r = cliente.get("/api/auth/yo", headers=headers_de("admin@prueba.local", "clave-admin"))
    assert r.status_code == 200
    assert r.json()["rol"] == "ADMIN"


def test_login_correcto_entrega_token_y_cookie(cliente, crear_usuario):
    crear_usuario("ana@prueba.local")
    r = cliente.post("/api/auth/login", json={"correo": " Ana@Prueba.local ", "clave": CLAVE})
    assert r.status_code == 200
    assert r.json()["access_token"]
    assert r.json()["usuario"]["correo"] == "ana@prueba.local"
    cookie = r.headers["set-cookie"]
    assert "refresh_token=" in cookie
    assert "HttpOnly" in cookie
    assert "Path=/api/auth" in cookie


def test_login_con_clave_incorrecta(cliente, crear_usuario):
    crear_usuario("ana@prueba.local")
    r = cliente.post("/api/auth/login", json={"correo": "ana@prueba.local", "clave": "mala"})
    assert r.status_code == 401
    assert r.json() == {"detail": "Correo o clave incorrectos"}


def test_login_de_usuario_inactivo(cliente, crear_usuario):
    crear_usuario("ana@prueba.local", activo=False)
    r = cliente.post("/api/auth/login", json={"correo": "ana@prueba.local", "clave": CLAVE})
    assert r.status_code == 401


def test_login_sin_datos_da_error_en_espanol(cliente):
    r = cliente.post("/api/auth/login", json={"correo": "ana@prueba.local"})
    assert r.status_code == 422
    assert r.json() == {"detail": "Dato inválido en 'clave'"}


def test_yo_sin_token(cliente):
    r = cliente.get("/api/auth/yo")
    assert r.status_code == 401
    assert r.json() == {"detail": "No autenticado"}


def test_yo_rechaza_token_expirado_y_refresh_como_access(cliente, crear_usuario):
    usuario = crear_usuario("ana@prueba.local")
    expirado = _crear_token(usuario.id, "access", timedelta(minutes=-1))
    for token in (expirado, crear_refresh_token(usuario.id)):
        r = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


def test_usuario_desactivado_pierde_acceso_de_inmediato(cliente, crear_usuario, headers_de, db):
    usuario = crear_usuario("ana@prueba.local")
    headers = headers_de("ana@prueba.local")
    usuario.activo = False
    db.commit()
    assert cliente.get("/api/auth/yo", headers=headers).status_code == 401
    assert cliente.post("/api/auth/refresh").status_code == 401


def test_refresh_con_cookie_entrega_nuevo_token(cliente, crear_usuario):
    crear_usuario("ana@prueba.local", rol=Rol.ADMIN)
    cliente.post("/api/auth/login", json={"correo": "ana@prueba.local", "clave": CLAVE})
    r = cliente.post("/api/auth/refresh")
    assert r.status_code == 200
    token = r.json()["access_token"]
    yo = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token}"})
    assert yo.json()["correo"] == "ana@prueba.local"


def test_refresh_sin_cookie(cliente):
    r = cliente.post("/api/auth/refresh")
    assert r.status_code == 401
    assert r.json() == {"detail": "Sesión expirada, vuelve a ingresar"}


def test_logout_borra_la_cookie(cliente, crear_usuario):
    crear_usuario("ana@prueba.local")
    cliente.post("/api/auth/login", json={"correo": "ana@prueba.local", "clave": CLAVE})
    assert cliente.post("/api/auth/logout").status_code == 204
    assert cliente.post("/api/auth/refresh").status_code == 401
