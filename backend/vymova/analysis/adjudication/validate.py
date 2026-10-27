"""Mechanical check of the adjudicator's quotes: each quote must appear verbatim in its clip's blind transcription."""
import re
import unicodedata

from ..blind.align import sim

APOS = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "ʹ": "'"})


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").lower()).translate(APOS)
    return re.sub(r"\s+", " ", s).strip()


def quote_ok(quote: str, transcription: str) -> bool:
    """A quote is whole words of the blind transcription, at least 3 letters."""
    q = norm(quote).strip(" .,;!?…")
    if sum(ch.isalpha() for ch in q) < 3:
        return False
    return re.search(r"(?<![\w'])" + re.escape(q) + r"(?![\w'])", norm(transcription)) is not None


MIN_AB_SIM = 0.5  # both models must hear the same spot, not different words


def check(finding: dict, blind_a: dict[str, str], blind_b: dict[str, str] | None, replies: dict[str, str | None],
          acoustic_ok: bool = False) -> dict:
    """Recomputes the status from the actual quotes. Two blind models: "confirmed" needs a matching quote from both.
    One blind model: "confirmed" needs verified quotes in two different clips, or one clip plus acoustic support."""
    if blind_b is None:
        return _check_single(finding, blind_a, replies, acoustic_ok)
    f = dict(finding)
    kept, best = [], "none"
    for ex in f.get("examples") or []:
        cid = ex.get("clip")
        if cid not in blind_a:
            continue
        q = ex.get("quotes") or {}
        a, b = quote_ok(q.get("A", ""), blind_a.get(cid, "")), quote_ok(q.get("B", ""), blind_b.get(cid, ""))
        if a and b and sim(q.get("A", ""), q.get("B", "")) < MIN_AB_SIM:
            a = b = False
            ex = {**ex, "verified": "mismatch"}
        else:
            ex = {**ex, "verified": "both" if a and b else "A" if a else "B" if b else "none"}
        if ex["verified"] == "both":
            best = "both"
        elif ex["verified"] in ("A", "B") and best == "none":
            best = "one"
        kept.append(ex)
    claimed = f.get("status")
    if claimed == "rejected":
        status = "rejected"
    elif best == "both" and claimed == "confirmed":
        status = "confirmed"
    elif best in ("both", "one"):
        status = "possible"
    else:
        status = "rejected"
        f["reason_ru"] = f.get("reason_ru") or "Цитаты из слепых записей не подтвердились."
    f["status"] = status
    f["examples"] = [e for e in kept if e["verified"] in ("both", "A", "B")] if status != "rejected" else kept
    def taught(e: dict) -> bool:
        reply = norm(replies.get(e["clip"]) or "")
        word = norm(e.get("word", "")).strip(".,!?")
        return bool(word) and len(reply.split()) <= 8 and word in reply  # short repeat reply = correction

    word_hits = [e for e in f["examples"] if taught(e)]
    f["taught_in_lesson"] = bool(word_hits)
    return f


def _taught(examples: list[dict], replies: dict[str, str | None]) -> bool:
    for e in examples:
        reply = norm(replies.get(e["clip"]) or "")
        word = norm(e.get("word", "")).strip(".,!?")
        if word and len(reply.split()) <= 8 and word in reply:
            return True
    return False


def _check_single(finding: dict, blind_a: dict[str, str], replies: dict[str, str | None], acoustic_ok: bool) -> dict:
    f = dict(finding)
    kept = []
    for ex in f.get("examples") or []:
        cid = ex.get("clip")
        if cid not in blind_a:
            continue
        ok = quote_ok((ex.get("quotes") or {}).get("A", ""), blind_a.get(cid, ""))
        kept.append({**ex, "verified": "A" if ok else "none"})
    clips_ok = {e["clip"] for e in kept if e["verified"] == "A"}
    if f.get("status") == "rejected":
        status = "rejected"
    elif len(clips_ok) >= 2 or (len(clips_ok) == 1 and acoustic_ok):
        status = "confirmed"
    elif clips_ok:
        status = "possible"
    else:
        status = "rejected"
        f["reason_ru"] = f.get("reason_ru") or "Цитаты из слепой записи не подтвердились."
    f["status"] = status
    f["examples"] = [e for e in kept if e["verified"] == "A"] if status != "rejected" else kept
    f["taught_in_lesson"] = _taught(f["examples"], replies)
    return f
