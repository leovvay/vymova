"""Checks that a phonetic transcription belongs to its own turn, not a neighbouring one (models "drift")."""
import difflib
import re
import unicodedata

MIN_LEN = 6


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"\[other\]|[^a-zа-яіїєґёыэъ ]", "", s.replace("'", ""))


def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def misaligned(clips: list[dict], got: dict[str, str]) -> list[str]:
    """Clips whose transcription resembles the neighbouring turn's text noticeably more than its own, or is empty."""
    bad = []
    for i, c in enumerate(clips):
        ph = got.get(c["clip"], "")
        if not ph.strip():
            bad.append(c["clip"])
            continue
        if len(norm(c["text"])) < MIN_LEN:
            continue
        own = sim(c["text"], ph)
        neigh = max((sim(clips[j]["text"], ph) for j in range(max(0, i - 12), min(len(clips), i + 13)) if j != i),
                    default=0.0)
        if neigh > own + 0.25:
            bad.append(c["clip"])
    return bad
