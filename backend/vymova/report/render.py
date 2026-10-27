"""Сборка HTML-отчёта урока из артефактов шагов."""
import json
import re
from pathlib import Path
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .. import audio
from ..analysis.acoustic.align import norm_word
from ..config import PORT
from ..transcription import words

HERE = Path(__file__).parent
LANG_TITLES = {"ru": "Русизмы", "pl": "Полонизмы", "be": "Белорусизмы", "en": "Англицизмы"}
SHORT = {"facebook/wav2vec2-lv-60-espeak-cv-ft": "lv-60", "facebook/wav2vec2-xlsr-53-espeak-cv-ft": "XLSR-53"}


def _plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    return one if n % 10 == 1 else few if 2 <= n % 10 <= 4 else many


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html", "j2"]))
    env.filters["plural"] = _plural
    return env


def clip_href(lesson_id: str, folder: str, clip_file: str) -> str:
    """Ссылка на клип через саму программу: работает и из PDF, открытого в браузере, и с диска
    (контейнер всегда запущен — --restart unless-stopped)."""
    return f"http://127.0.0.1:{PORT}/api/lessons/{quote(lesson_id)}/files/clips/{quote(folder)}/{quote(clip_file)}"


def _ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 60:02d}:{s % 60:02d}"


def _load(f: Path, default=None):
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


def _student(d: Path, lesson_id: str, name: str, folder: str, by_i: dict, host: str) -> dict:
    manifest = _load(d / "clips" / folder / "manifest.json", [])
    times = {c["clip"]: _ts(c["start"]) for c in manifest}
    adj = _load(d / "adjudication" / f"{folder}.json", {"findings": []})
    lang = _load(d / "language" / f"{folder}.json", {})
    ac = _load(d / "acoustic" / f"{folder}.json", {"skipped": True, "reason_ru": "нет данных"})
    pair = (_load(d / "blind" / "index.json", {}) or {}).get("pair") or []
    blind = {m: {x["clip"]: x["phonetic"] for x in _load(d / "blind" / folder / f"{m}.json", [])} for m in pair}
    unavailable = _load(d / "blind" / "_unavailable.json", {}) or {}

    findings = adj.get("findings", [])
    confirmed = [f for f in findings if f["status"] == "confirmed"]
    possible = [f for f in findings if f["status"] == "possible"]
    hl_words = {norm_word(e.get("word", "")) for f in confirmed + possible for e in f.get("examples", [])}

    acoustic, models = [], []
    if not ac.get("skipped"):
        ids = sorted({m for f in ac.get("findings", []) for m in f["models"]}, key=list(SHORT).index)
        models = [{"id": m, "short": SHORT.get(m, m)} for m in ids]
        shown = [f for f in ac.get("findings", []) if f["verdict"] in ("confirmed", "likely")
                 and any(r["n"] >= 5 for r in f["models"].values())][:8]
        for f in shown:
            natives = [f"{SHORT.get(m, m)}: {r['native_rate']:.0%}" for m, r in f["models"].items()
                       if r.get("native_rate") is not None]
            exs = [{**e, "time": times.get(e["clip"], "")} for e in f["examples"]]
            acoustic.append({**f, "native": " · ".join(natives) or "нет данных", "examples": exs})
            hl_words |= {norm_word(e["word"]) for e in exs}

    groups: dict[str, list] = {}
    for r in lang.get("interference", []):
        groups.setdefault(r.get("source_lang", "?"), []).append(r)
    interference = [{"title": LANG_TITLES.get(k, f"Другие языки ({k})"), "rows": v} for k, v in groups.items()]

    phones = ac.get("phones", {}) if not ac.get("skipped") else {}
    lv, xl = "facebook/wav2vec2-lv-60-espeak-cv-ft", "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
    clips = []
    for c in manifest:
        ws = []
        for i in c["word_idx"]:
            w = by_i.get(i)
            if not w:
                continue
            p = phones.get(str(i), {})
            ws.append({"text": w.text, "a": "".join(p.get(lv, [])) or "—", "b": "".join(p.get(xl, [])) or "—",
                       "hl": norm_word(w.text) in hl_words})
        clips.append({"clip": c["clip"], "time": times[c["clip"]], "words": ws,
                      "href": clip_href(lesson_id, folder, c["file"]),
                      "blind": [{"model": m, "text": blind[m].get(c["clip"], "—")} for m in pair]})

    return {"name": name, "low_speech": lang.get("low_speech", False), "speech_sec": lang.get("speech_sec", 0),
            "blind_unavailable": unavailable.get("reason_ru"), "top5": lang.get("top5", []),
            "confirmed": confirmed, "possible": possible, "acoustic": acoustic, "acoustic_models": models,
            "acoustic_skipped": ac.get("reason_ru") if ac.get("skipped") else None,
            "grammar": lang.get("grammar", []), "interference": interference,
            "strengths": lang.get("strengths_ru", []), "drills": lang.get("drills_ru", []), "clips": clips}


def build(lesson_dir: Path, lesson_id: str, date: str, topic: str, host_data_dir: str) -> Path:
    d = lesson_dir
    by_i = {w.i: w for w in words(_load(d / "transcript.json", {}))}
    folders = _load(d / "clips" / "index.json", {})
    students = [_student(d, lesson_id, n, f, by_i, host_data_dir) for n, f in folders.items()]
    y, m, dd = (date.split("-") + ["", "", ""])[:3]
    html = _env().get_template("template.html.j2").render(
        css=(HERE / "styles.css").read_text(encoding="utf-8"),
        lesson={"date_ru": f"{dd}.{m}.{y}", "topic": topic, "minutes": round(audio.duration(d / "lesson.mp3") / 60)},
        students=students, summary=_load(d / "summary.json", {"common": [], "per_student_top3": {}}))
    out = d / "report.html"
    out.write_text(html, encoding="utf-8")
    return out
