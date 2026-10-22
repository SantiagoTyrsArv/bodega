import pytest

from app.config import Settings


@pytest.mark.parametrize(
    ("url", "esperada"),
    [
        (
            "postgresql://u:c@host/bd?sslmode=require",
            "postgresql+psycopg://u:c@host/bd?sslmode=require",
        ),
        ("postgres://u:c@host/bd", "postgresql+psycopg://u:c@host/bd"),
        ("postgresql+psycopg://u:c@host/bd", "postgresql+psycopg://u:c@host/bd"),
    ],
)
def test_database_url_usa_psycopg(url: str, esperada: str):
    s = Settings(database_url=url, admin_correo="a@b.c", admin_clave="x", jwt_secret="s" * 32)
    assert s.database_url == esperada
