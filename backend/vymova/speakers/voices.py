from collections import defaultdict
from pathlib import Path

from .. import audio
from ..transcription import Turn, Word, group, words
from . import memory
from .model import Sample, Voice


def build(lesson_dir: Path, transcript: dict) -> list[Voice]:
    ws = words(transcript)
    by_i = {w.i: w for w in ws}
    turns = group(ws)
    stats: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
    for w in ws:
        stats[w.speaker][0] += w.end - w.start
        stats[w.speaker][1] += 1
    voices = []
    for spk, (sec, n) in sorted(stats.items(), key=lambda kv: -kv[1][0]):
        samples = []
        for k, t in enumerate(_pick_samples([t for t in turns if t.speaker == spk], by_i), 1):
            f = f"voices/{spk}_{k}.mp3"
            audio.cut(lesson_dir / "lesson.mp3", t.start - 0.2, min(t.end, t.start + 8) + 0.3, lesson_dir / f)
            samples.append(Sample(start=t.start, end=t.end, file=f,
                                  text=" ".join(by_i[i].text for i in t.word_idx)))
        name, role = memory.suggest(lesson_dir, spk)
        voices.append(Voice(speaker_id=spk, minutes=round(sec / 60, 1), words=int(n), samples=samples,
                            suggested_name=name, suggested_role=role))
    return voices


def _pick_samples(turns: list[Turn], by_i: dict[int, Word]) -> list[Turn]:
    good = [t for t in turns if 3 <= t.end - t.start <= 8]
    pool = good if len(good) >= 2 else sorted(turns, key=lambda t: t.end - t.start, reverse=True)
    return sorted(pool, key=lambda t: len(t.word_idx), reverse=True)[:2]
