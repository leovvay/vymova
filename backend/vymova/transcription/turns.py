from dataclasses import dataclass, field

FILL = {"угу", "окей", "е", "е-е", "е-е-е", "ем", "а-а", "а-а-а", "м-м", "ну", "так"}
MAX_WORD = 3.0  # Scribe sometimes stretches a word across a pause


@dataclass
class Word:
    i: int
    text: str
    start: float
    end: float
    speaker: str


@dataclass
class Turn:
    speaker: str
    start: float
    end: float
    word_idx: list[int] = field(default_factory=list)


def words(transcript: dict) -> list[Word]:
    out = []
    for i, w in enumerate(transcript.get("words", [])):
        if w.get("type") != "word":
            continue
        start, end = float(w["start"]), float(w["end"])
        if end - start > MAX_WORD:
            start = end - 0.6
        out.append(Word(i, w["text"], start, end, w.get("speaker_id", "speaker_0")))
    return out


def group(ws: list[Word], gap: float = 1.5) -> list[Turn]:
    turns: list[Turn] = []
    for w in ws:
        cur = turns[-1] if turns else None
        if cur and cur.speaker == w.speaker and w.start - cur.end < gap:
            cur.end = max(cur.end, w.end)
            cur.word_idx.append(w.i)
        else:
            turns.append(Turn(w.speaker, w.start, w.end, [w.i]))
    return turns


def is_filler_only(turn: Turn, by_i: dict[int, Word]) -> bool:
    return all(by_i[i].text.lower().strip(".,!?-—…") in FILL for i in turn.word_idx)
