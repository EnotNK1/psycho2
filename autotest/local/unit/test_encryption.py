from cryptography.fernet import Fernet

from src import config
from src.utils import encryption as encryption_module
from src.utils.encryption import (
    EncryptedFloatType,
    EncryptedIntType,
    EncryptedJSONType,
    EncryptedStringType,
    decrypt_from_storage,
    encrypt_for_storage,
)


def test_encrypt_roundtrip_for_supported_values(monkeypatch):
    monkeypatch.setattr(config.settings, "DATA_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    encryption_module.get_fernet.cache_clear()

    encrypted_int = encrypt_for_storage(42)
    encrypted_float = encrypt_for_storage(3.14)
    encrypted_string = encrypt_for_storage("secret")
    encrypted_json = encrypt_for_storage(["a", 1, {"k": "v"}])

    assert decrypt_from_storage(encrypted_int, int) == 42
    assert decrypt_from_storage(encrypted_float, float) == 3.14
    assert decrypt_from_storage(encrypted_string, str) == "secret"
    assert decrypt_from_storage(encrypted_json, lambda value: value) == ["a", 1, {"k": "v"}]


def test_decrypt_from_storage_supports_legacy_plaintext():
    assert decrypt_from_storage("42", int) == 42
    assert decrypt_from_storage("3.14", float) == 3.14
    assert decrypt_from_storage("secret", str) == "secret"


def test_encrypted_sqlalchemy_types_roundtrip(monkeypatch):
    monkeypatch.setattr(config.settings, "DATA_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    encryption_module.get_fernet.cache_clear()

    encrypted_int = EncryptedIntType().process_bind_param(7, None)
    encrypted_float = EncryptedFloatType().process_bind_param(2.5, None)
    encrypted_string = EncryptedStringType().process_bind_param("hello", None)
    encrypted_json = EncryptedJSONType().process_bind_param({"foo": ["bar"]}, None)

    assert EncryptedIntType().process_result_value(encrypted_int, None) == 7
    assert EncryptedFloatType().process_result_value(encrypted_float, None) == 2.5
    assert EncryptedStringType().process_result_value(encrypted_string, None) == "hello"
    assert EncryptedJSONType().process_result_value(encrypted_json, None) == {"foo": ["bar"]}
