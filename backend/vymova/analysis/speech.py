"""Whether the student has enough Ukrainian speech to analyse."""
import json
from pathlib import Path

MIN_SPEECH_SEC, MIN_UKR_CLIPS = 30.0, 10


def low_speech(lesson_dir: Path, folder: str) -> tuple[bool, float]:
    """(too_little_speech, speech_seconds). A turn is "not Ukrainian" if both blind transcriptions assigned
    more than half of its words to other languages."""
    manifest = json.loads((lesson_dir / "clips" / folder / "manifest.json").read_text(encoding="utf-8"))
    speech = sum(c["end"] - c["start"] for c in manifest)
    pair = (json.loads((lesson_dir / "blind" / "index.json").read_text(encoding="utf-8")).get("pair") or []) \
        if (lesson_dir / "blind" / "index.json").exists() else []
    foreign: dict[str, list[int]] = {}
    for m in pair:
        f = lesson_dir / "blind" / folder / f"{m}.json"
        for x in json.loads(f.read_text(encoding="utf-8")) if f.exists() else []:
            foreign.setdefault(x["clip"], []).append(len(x.get("non_ukrainian_words") or []))
    ukr = 0
    for c in manifest:
        n = max(1, len(c["text"].split()))
        counts = foreign.get(c["clip"], [])
        if not counts or min(counts) * 2 <= n:
            ukr += 1
    return speech < MIN_SPEECH_SEC or ukr < MIN_UKR_CLIPS, round(speech, 1)
