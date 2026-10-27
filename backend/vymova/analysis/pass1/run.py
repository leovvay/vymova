"""Первый проход: Gemini слушает весь урок и выдаёт кандидатов в ошибки по каждому студенту."""
from pathlib import Path

from ... import gemini
from ...transcription import group, words

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")


def _ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 60:02d}:{s % 60:02d}"


def labelled_transcript(transcript: dict, names: dict[str, str]) -> str:
    ws = words(transcript)
    by_i = {w.i: w for w in ws}
    lines = []
    for t in group(ws, gap=1e9):
        label = names.get(t.speaker, "Другой")
        lines.append(f"[{_ts(t.start)}] {label}: " + " ".join(by_i[i].text for i in t.word_idx))
    return "\n".join(lines)


def run(lesson_dir: Path, transcript: dict, names: dict[str, str], students: list[str], key: str) -> dict:
    model = gemini.pick_main(key)
    uri = gemini.upload(lesson_dir / "lesson.mp3", key)
    prompt = PROMPT.replace("{students}", ", ".join(f'"{s}"' for s in students)) \
                   .replace("{transcript}", labelled_transcript(transcript, names))
    out = gemini.generate_json(model, [{"file_data": {"mime_type": "audio/mp3", "file_uri": uri}}, {"text": prompt}], key)
    res = {"model": model, "students": {}}
    for s in students:
        got = (out.get("students") or {}).get(s) or {}
        res["students"][s] = {"pronunciation_issues": got.get("pronunciation_issues", []),
                              "asr_mismatches": got.get("asr_mismatches", [])}
    return res
