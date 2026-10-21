from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()


def hashear_clave(clave: str) -> str:
    return _hasher.hash(clave)


def verificar_clave(clave: str, clave_hash: str) -> bool:
    try:
        return _hasher.verify(clave_hash, clave)
    except (VerifyMismatchError, InvalidHashError):
        return False
