import io
import json

import pytest

import src.api.chat_bot as chat_bot_module
from autotest.factories.chat_bot import build_faq_data


FAQ_DATA = {
    "groups": [build_faq_data()["groups"][0]],
}


def test_load_data_reads_json_from_custom_path(tmp_path):
    data_file = tmp_path / "faq.json"
    expected = {"groups": [{"id": 1, "name": "One"}]}
    data_file.write_text(json.dumps(expected), encoding="utf-8")
    actual = chat_bot_module.load_data(str(data_file))
    assert actual == expected


def test_load_data_raises_file_not_found_for_missing_path(tmp_path):
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        chat_bot_module.load_data(str(missing_file))


def test_load_data_raises_json_decode_error_for_invalid_json(tmp_path):
    broken_file = tmp_path / "broken.json"
    broken_file.write_text("{bad json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        chat_bot_module.load_data(str(broken_file))


def test_load_faq_data_uses_expected_project_path(monkeypatch):
    captured = {}
    original_open = open

    def fake_open(path, *args, **kwargs):
        captured["path"] = path
        if path == "src/services/info/chat_bot.json":
            return io.StringIO(json.dumps(FAQ_DATA))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)
    actual = chat_bot_module.load_faq_data()
    assert captured["path"] == "src/services/info/chat_bot.json"
    assert actual == FAQ_DATA


def test_load_faq_data_propagates_file_not_found(monkeypatch):
    def fake_open(path, *args, **kwargs):
        raise FileNotFoundError(path)

    monkeypatch.setattr("builtins.open", fake_open)

    with pytest.raises(FileNotFoundError):
        chat_bot_module.load_faq_data()
