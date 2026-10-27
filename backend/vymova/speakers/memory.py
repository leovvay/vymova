"""Voice memory across lessons: /data/voices.json — {name: {embedding, n, role}}."""
import json
import os
from pathlib import Path

from ..config import paths
from .embeddings import cosine

THRESHOLD = 0.96  # on the reference lesson: same person 0.99–1.0, different male voices up to 0.93


def _load() -> dict:
    f = paths().voices_file
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _save(data: dict) -> None:
    f = paths().voices_file
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)


def _lesson_vec(lesson_dir: Path, speaker_id: str) -> list[float] | None:
    f = lesson_dir / "voice_embeddings.json"
    return json.loads(f.read_text(encoding="utf-8")).get(speaker_id) if f.exists() else None


def remember(name: str, speaker_id: str, lesson_dir: Path, role: str = "student") -> None:
    vec = _lesson_vec(lesson_dir, speaker_id)
    if not vec:
        return
    data = _load()
    cur = data.get(name)
    if cur:
        n = cur["n"]
        vec = [(a * n + b) / (n + 1) for a, b in zip(cur["embedding"], vec)]
        data[name] = {"embedding": vec, "n": n + 1, "role": role}
    else:
        data[name] = {"embedding": vec, "n": 1, "role": role}
    _save(data)


def suggest(lesson_dir: Path, speaker_id: str) -> tuple[str | None, str | None]:
    vec = _lesson_vec(lesson_dir, speaker_id)
    if not vec:
        return None, None
    best, score = None, THRESHOLD
    for name, rec in _load().items():
        s = cosine(vec, rec["embedding"])
        if s >= score:
            best, score = (name, rec.get("role", "student")), s
    return best if best else (None, None)
