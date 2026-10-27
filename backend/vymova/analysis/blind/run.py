"""Слепая проверка: две модели независимо записывают фонетику каждой реплики студента."""
import base64
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ... import gemini
from .align import misaligned

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")
BATCH = 15  # длинные пачки модели путают: запись уезжает на соседние реплики
PARALLEL = 4


def _ask(model: str, batch: list[dict], clip_dir: Path, key: str) -> dict[str, dict]:
    parts: list[dict] = [{"text": PROMPT}]
    for c in batch:
        parts.append({"text": f"\nClip {c['clip']}:"})
        parts.append({"inline_data": {"mime_type": "audio/mp3",
                                      "data": base64.b64encode((clip_dir / c["file"]).read_bytes()).decode()}})
    got = gemini.generate_json(model, parts, key)
    return {x.get("clip"): x for x in got if isinstance(x, dict)}


def _transcribe(model: str, clips: list[dict], clip_dir: Path, key: str) -> list[dict]:
    by_id: dict[str, dict] = {}
    batches = [clips[i:i + BATCH] for i in range(0, len(clips), BATCH)]
    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        for got in ex.map(lambda b: _ask(model, b, clip_dir, key), batches):
            by_id.update(got)
    redo = [c for c in clips if c["clip"] in set(misaligned(clips, {k: v.get("phonetic", "") for k, v in by_id.items()}))]
    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        for got in ex.map(lambda c: _ask(model, [c], clip_dir, key), redo):
            by_id.update(got)
    out: list[dict] = []
    for c in clips:
        x = by_id.get(c["clip"], {})
        out.append({"clip": c["clip"], "phonetic": x.get("phonetic", ""),
                    "non_ukrainian_words": x.get("non_ukrainian_words", []), "notable_ru": x.get("notable_ru", "")})
    return out


def run(lesson_dir: Path, folders: dict[str, str], pair: tuple[str, str] | None, key: str) -> dict:
    blind_dir = lesson_dir / "blind"
    blind_dir.mkdir(exist_ok=True)
    if pair is None:
        (blind_dir / "_unavailable.json").write_text(json.dumps(
            {"reason_ru": "Для этого ключа нет двух разных сильных моделей Gemini — блок «подтверждено» не формируется."},
            ensure_ascii=False), encoding="utf-8")
        return {"pair": None}
    for name, folder in folders.items():
        clip_dir = lesson_dir / "clips" / folder
        clips = json.loads((clip_dir / "manifest.json").read_text(encoding="utf-8"))
        (blind_dir / folder).mkdir(exist_ok=True)
        todo = [m for m in pair if not (blind_dir / folder / f"{m}.json").exists()]
        with ThreadPoolExecutor(max_workers=2) as ex:
            results = dict(zip(todo, ex.map(lambda m: _transcribe(m, clips, clip_dir, key), todo)))
        for m, res in results.items():
            (blind_dir / folder / f"{m}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"pair": list(pair)}
