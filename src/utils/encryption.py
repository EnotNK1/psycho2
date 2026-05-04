import base64
import hashlib
import json
from functools import lru_cache
from typing import Any, Callable

import sqlalchemy as sa
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator

from src.config import settings

ENCRYPTED_PREFIX = "enc::"


def _derive_fernet_key(secret: str) -> str:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    raw_key = settings.DATA_ENCRYPTION_KEY or _derive_fernet_key(settings.JWT_SECRET_KEY)
    try:
        return Fernet(raw_key.encode("utf-8"))
    except Exception as ex:
        raise ValueError(
            "Invalid DATA_ENCRYPTION_KEY. Expected a valid Fernet key or leave it empty to derive from JWT_SECRET_KEY."
        ) from ex


def encrypt_for_storage(value: Any) -> str | None:
    if value is None:
        return None

    payload = json.dumps(value, ensure_ascii=False)
    token = get_fernet().encrypt(payload.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{token}"


def _coerce_int(value: Any) -> int:
    return int(value)


def _coerce_float(value: Any) -> float:
    return float(value)


def _coerce_string(value: Any) -> str:
    return str(value)


def _coerce_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def decrypt_from_storage(value: Any, coercer: Callable[[Any], Any]) -> Any:
    if value is None:
        return None

    if not isinstance(value, str):
        return coercer(value)

    if not value.startswith(ENCRYPTED_PREFIX):
        return coercer(value)

    token = value[len(ENCRYPTED_PREFIX):]
    try:
        decrypted = get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
        return coercer(json.loads(decrypted))
    except (InvalidToken, json.JSONDecodeError, TypeError, ValueError):
        return coercer(value)


class EncryptedType(TypeDecorator):
    impl = sa.Text
    cache_ok = True

    def __init__(self, coercer: Callable[[Any], Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coercer = coercer

    def process_bind_param(self, value: Any, dialect) -> str | None:
        return encrypt_for_storage(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        return decrypt_from_storage(value, self._coercer)


class EncryptedIntType(EncryptedType):
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(_coerce_int, *args, **kwargs)


class EncryptedFloatType(EncryptedType):
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(_coerce_float, *args, **kwargs)


class EncryptedStringType(EncryptedType):
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(_coerce_string, *args, **kwargs)


class EncryptedJSONType(EncryptedType):
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(_coerce_json, *args, **kwargs)
