"""Group summary: common mistakes and the top three items per student."""
import json
from pathlib import Path

from ... import gemini

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")


def run(lesson_dir: Path, folders: dict[str, str], key: str) -> dict:
    data, top3 = {}, {}
    for name, folder in folders.items():
        lang = json.loads((lesson_dir / "language" / f"{folder}.json").read_text(encoding="utf-8"))
        adj = json.loads((lesson_dir / "adjudication" / f"{folder}.json").read_text(encoding="utf-8"))
        if lang.get("low_speech"):
            top3[name] = ["Мало речи для разбора"]
            continue
        data[name] = {"confirmed": [f["title_ru"] for f in adj.get("findings", []) if f["status"] == "confirmed"],
                      "top5": [t.get("title_ru", "") for t in lang.get("top5", [])]}
    if not data:
        return {"common": [], "per_student_top3": top3}
    out = gemini.generate_json(gemini.pick_main(key),
                               [{"text": PROMPT.replace("{students}", json.dumps(data, ensure_ascii=False))}], key)
    top3.update({k: v[:3] for k, v in (out.get("per_student_top3") or {}).items() if k in data})
    common = [c for c in out.get("common", []) if len(set(c.get("students", [])) & set(data)) >= 2][:5]
    return {"common": common, "per_student_top3": top3}
