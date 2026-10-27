import json
from pathlib import Path
from src.config import ROOT


def data_path(path):
    source = Path(path)
    return source if source.is_absolute() else ROOT / source


def load_data(path: str):
    source = Path(path)
    if not source.is_absolute():
        source = ROOT / source
    with source.open(encoding="utf-8") as handle:
        return json.load(handle)
