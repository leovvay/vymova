"""Арбитр: из кандидатов, двух слепых записей и акустики собирает подтверждённые паттерны."""
import json
from pathlib import Path

from ... import gemini
from .validate import check

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")


def _ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 60:02d}:{s % 60:02d}"


def run(lesson_dir: Path, name: str, folder: str, key: str) -> dict:
    manifest = json.loads((lesson_dir / "clips" / folder / "manifest.json").read_text(encoding="utf-8"))
    pair = json.loads((lesson_dir / "blind" / "index.json").read_text(encoding="utf-8")).get("pair")
    if not pair:
        return {"unavailable": True, "findings": []}
    a, b = ({x["clip"]: x["phonetic"] for x in json.loads((lesson_dir / "blind" / folder / f"{m}.json")
                                                          .read_text(encoding="utf-8"))} for m in pair)
    pass1 = json.loads((lesson_dir / "pass1.json").read_text(encoding="utf-8"))["students"].get(name, {})
    ac_file = lesson_dir / "acoustic" / f"{folder}.json"
    ac = json.loads(ac_file.read_text(encoding="utf-8")) if ac_file.exists() else {"skipped": True}
    acoustic = "not run" if ac.get("skipped") else json.dumps(
        [{k: f[k] for k in ("pattern_key", "label_ru", "verdict", "examples")} for f in ac.get("findings", [])],
        ensure_ascii=False)
    clips = "\n".join(json.dumps({"clip": c["clip"], "time": _ts(c["start"]), "asr": c["text"],
                                  "tutor_reply": c["teacher_reply"], "A": a.get(c["clip"], ""),
                                  "B": b.get(c["clip"], "")}, ensure_ascii=False) for c in manifest)
    prompt = (PROMPT.replace("{student}", name).replace("{candidates}", json.dumps(pass1, ensure_ascii=False))
              .replace("{acoustic}", acoustic).replace("{clips}", clips))
    out = gemini.generate_json(gemini.pick_main(key), [{"text": prompt}], key)
    replies = {c["clip"]: c["teacher_reply"] for c in manifest}
    times = {c["clip"]: _ts(c["start"]) for c in manifest}
    findings = []
    for f in out.get("findings", []):
        f = check(f, a, b, replies)
        for ex in f["examples"]:
            ex["time"] = times.get(ex["clip"], "")
        if ac.get("findings") and f.get("acoustic_pattern"):
            hit = next((x for x in ac["findings"] if x["pattern_key"] == f["acoustic_pattern"]), None)
            f["acoustic"] = {"pattern_key": hit["pattern_key"], "verdict": hit["verdict"]} if hit else None
        findings.append(f)
    return {"unavailable": False, "pair": pair, "findings": findings}
