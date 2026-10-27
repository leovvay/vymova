"""Blind check: two models independently transcribe the phonetics of each student turn."""
import base64
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ... import gemini
from ...jsonio import write_json
from .align import misaligned

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")
BATCH = 15  # long batches confuse models: the transcription drifts onto neighbouring turns
PARALLEL = 4


def _ask(model: str, batch: list[dict], clip_dir: Path, key: str) -> dict[str, dict]:
    parts: list[dict] = [{"text": PROMPT}]
    for c in batch:
        parts.append({"text": f"\nClip {c['clip']}:"})
        parts.append({"inline_data": {"mime_type": "audio/mp3",
                                      "data": base64.b64encode((clip_dir / c["file"]).read_bytes()).decode()}})
    got = gemini.generate_json(model, parts, key)
    if isinstance(got, dict):  # a single turn often arrives as an object, not a list
        got = got.get("clips") if isinstance(got.get("clips"), list) else [got]
    items = [x for x in got if isinstance(x, dict)] if isinstance(got, list) else []
    if len(batch) == 1 and len(items) == 1:
        items[0]["clip"] = batch[0]["clip"]
    return {x.get("clip"): x for x in items}


def _transcribe(model: str, clips: list[dict], clip_dir: Path, key: str, partial: Path) -> list[dict]:
    """Finished batches are saved in partial — after a failure, already-paid requests are not repeated."""
    by_id: dict[str, dict] = json.loads(partial.read_text(encoding="utf-8")) if partial.exists() else {}
    lock = threading.Lock()

    def run_batch(b: list[dict]) -> None:
        got = _ask(model, b, clip_dir, key)
        with lock:
            by_id.update(got)
            write_json(partial, by_id)

    batches = [clips[i:i + BATCH] for i in range(0, len(clips), BATCH)]
    todo = [b for b in batches if not all(c["clip"] in by_id for c in b)]
    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        list(ex.map(run_batch, todo))
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
        write_json(blind_dir / "_unavailable.json",
                   {"reason_ru": "Для этого ключа нет двух разных сильных моделей Gemini — блок «подтверждено» не формируется."})
        return {"pair": None}
    for name, folder in folders.items():
        clip_dir = lesson_dir / "clips" / folder
        clips = json.loads((clip_dir / "manifest.json").read_text(encoding="utf-8"))
        (blind_dir / folder).mkdir(exist_ok=True)
        todo = [m for m in pair if not (blind_dir / folder / f"{m}.json").exists()]
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {ex.submit(_transcribe, m, clips, clip_dir, key, blind_dir / folder / f"{m}.partial.json"): m
                    for m in todo}
            errors = []
            for fut in as_completed(futs):  # save each model immediately, even if the other one failed
                try:
                    write_json(blind_dir / folder / f"{futs[fut]}.json", fut.result())
                except Exception as e:  # noqa: BLE001
                    errors.append(e)
            if errors:
                raise errors[0]
    return {"pair": list(pair)}
