"""Нарезка реплик каждого студента на клипы (границы — по словам Scribe)."""
from pathlib import Path

from ... import audio
from ...transcription import Word, group, is_filler_only, words

PAD_BEFORE, PAD_AFTER, REPLY_WINDOW = 0.3, 0.4, 3.0


def run(lesson_dir: Path, transcript: dict, students: dict[str, list[str]], teacher: list[str],
        folders: dict[str, str]) -> dict[str, str]:
    """Пишет clips/<папка>/cNN.mp3 и manifest.json на каждого студента. Возвращает {имя: папка}."""
    owner = {spk: name for name, spks in students.items() for spk in spks}
    owner.update({spk: "\0teacher" for spk in teacher})
    ws = [Word(w.i, w.text, w.start, w.end, owner.get(w.speaker, "\0other:" + w.speaker)) for w in words(transcript)]
    by_i = {w.i: w for w in ws}
    turns = group(ws)
    teacher_turns = [t for t in turns if t.speaker == "\0teacher"]
    for name, folder in folders.items():
        out_dir = lesson_dir / "clips" / folder
        manifest = []
        for t in (t for t in turns if t.speaker == name and not is_filler_only(t, by_i)):
            cid = f"c{len(manifest) + 1:02d}"
            audio.cut(lesson_dir / "lesson.mp3", t.start - PAD_BEFORE, t.end + PAD_AFTER, out_dir / f"{cid}.mp3")
            reply = next((r for r in teacher_turns if t.end <= r.start <= t.end + REPLY_WINDOW), None)
            manifest.append({
                "clip": cid, "start": round(t.start, 2), "end": round(t.end, 2), "file": f"{cid}.mp3",
                "text": " ".join(by_i[i].text for i in t.word_idx), "word_idx": t.word_idx,
                "teacher_reply": " ".join(by_i[i].text for i in reply.word_idx) if reply else None,
            })
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "manifest.json").write_text(__import__("json").dumps(manifest, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    return folders
