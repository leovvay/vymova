"""Grammar, interference, strengths, exercises and a top 5 per student."""
import json
from pathlib import Path

from ... import gemini
from ..speech import low_speech

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")
EMPTY = {"grammar": [], "interference": [], "strengths_ru": [], "drills_ru": [], "top5": []}


def _ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 60:02d}:{s % 60:02d}"


def run(lesson_dir: Path, name: str, folder: str, key: str) -> dict:
    manifest = json.loads((lesson_dir / "clips" / folder / "manifest.json").read_text(encoding="utf-8"))
    low, speech = low_speech(lesson_dir, folder)
    if low:
        return {**EMPTY, "low_speech": True, "speech_sec": speech}
    pair = json.loads((lesson_dir / "blind" / "index.json").read_text(encoding="utf-8")).get("pair") or []
    blind = [{x["clip"]: x["phonetic"] for x in json.loads((lesson_dir / "blind" / folder / f"{m}.json")
                                                           .read_text(encoding="utf-8"))} for m in pair]
    adj = json.loads((lesson_dir / "adjudication" / f"{folder}.json").read_text(encoding="utf-8"))
    patterns = [f["title_ru"] for f in adj.get("findings", []) if f["status"] == "confirmed"]
    clips = "\n".join(json.dumps({"clip": c["clip"], "time": _ts(c["start"]), "asr": c["text"],
                                  "tutor_reply": c["teacher_reply"],
                                  **{k: b.get(c["clip"], "") for k, b in zip("AB", blind)}}, ensure_ascii=False)
                      for c in manifest)
    prompt = (PROMPT.replace("{student}", name).replace("{patterns}", json.dumps(patterns, ensure_ascii=False))
              .replace("{clips}", clips))
    out = gemini.generate_json(gemini.pick_main(key), [{"text": prompt}], key)
    return {**EMPTY, **{k: out.get(k, []) for k in EMPTY}, "low_speech": False, "speech_sec": speech}
