import json
import os
import re
import shutil
import threading
from datetime import date as date_cls, datetime, timezone
from pathlib import Path
from typing import BinaryIO

from ..config import paths
from .model import Lesson

_lock = threading.RLock()
_TRANSLIT = dict(zip("абвгґдеєжзиіїйклмнопрстуфхцчшщьюяыэё",
                     ["a", "b", "v", "h", "g", "d", "e", "ie", "zh", "z", "y", "i", "i", "i", "k", "l", "m", "n", "o",
                      "p", "r", "s", "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "iu", "ia", "y", "e", "e"]))


def slugify(text: str) -> str:
    s = "".join(_TRANSLIT.get(c, c) for c in text.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40].strip("-")
    return s or "lesson"


def dir(lesson_id: str) -> Path:  # noqa: A001 - имя из плана
    return paths().lessons_dir / lesson_id


def _state_file(lesson_id: str) -> Path:
    return dir(lesson_id) / "state.json"


def create(file: BinaryIO, filename: str, date: str | None, topic: str | None, people: int | None = None) -> Lesson:
    day = date or date_cls.today().isoformat()
    base = f"{day}_{slugify(topic or '')}"
    with _lock:
        lesson_id, n = base, 1
        while dir(lesson_id).exists():
            n += 1
            lesson_id = f"{base}-{n}"
        d = dir(lesson_id)
        d.mkdir(parents=True)
        ext = Path(filename).suffix.lower() or ".bin"
        with open(d / f"source{ext}", "wb") as out:
            shutil.copyfileobj(file, out, length=1024 * 1024)
        lesson = Lesson(id=lesson_id, date=day, topic=topic or "", people=people, source=f"source{ext}",
                        created_at=datetime.now(timezone.utc))
        save_state(lesson)
    return lesson


def save_state(lesson: Lesson) -> None:
    with _lock:
        f = _state_file(lesson.id)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(lesson.model_dump_json(indent=1), encoding="utf-8")
        os.replace(tmp, f)


def get(lesson_id: str) -> Lesson:
    with _lock:
        return Lesson.model_validate_json(_state_file(lesson_id).read_text(encoding="utf-8"))


def exists(lesson_id: str) -> bool:
    return _state_file(lesson_id).exists()


def list() -> list[Lesson]:  # noqa: A001 - имя из плана
    out = []
    for f in paths().lessons_dir.glob("*/state.json"):
        try:
            out.append(Lesson.model_validate_json(f.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    return sorted(out, key=lambda l: l.created_at.timestamp() if l.created_at.tzinfo else l.created_at.replace(tzinfo=timezone.utc).timestamp(), reverse=True)


def read_json(lesson_id: str, name: str):
    return json.loads((dir(lesson_id) / name).read_text(encoding="utf-8"))


def write_json(lesson_id: str, name: str, data) -> Path:
    f = dir(lesson_id) / name
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(f.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)
    return f
