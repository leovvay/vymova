import json
import os

from ..config import paths
from .model import Settings


def load() -> Settings:
    f = paths().settings_file
    if not f.exists():
        return Settings()
    return Settings.model_validate_json(f.read_text(encoding="utf-8"))


def save(s: Settings) -> None:
    f = paths().settings_file
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(s.model_dump(), ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)
