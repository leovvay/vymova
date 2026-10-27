"""Атомарная запись JSON: файл появляется только целиком (артефакт = шаг готов)."""
import json
import os
from pathlib import Path


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)
    return path
