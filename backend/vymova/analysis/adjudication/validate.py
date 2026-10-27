"""Механическая проверка цитат арбитра: каждая цитата обязана дословно быть в слепой записи своего клипа."""
import re
import unicodedata

APOS = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "ʹ": "'"})


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").lower()).translate(APOS)
    return re.sub(r"\s+", " ", s).strip()


def quote_ok(quote: str, transcription: str) -> bool:
    q = norm(quote)
    return len(q) >= 2 and q in norm(transcription)


def check(finding: dict, blind_a: dict[str, str], blind_b: dict[str, str], replies: dict[str, str | None]) -> dict:
    """Пересчитывает статус по реальным цитатам. Модель не может «подтвердить» без опоры на обе записи."""
    f = dict(finding)
    kept, best = [], "none"
    for ex in f.get("examples") or []:
        cid = ex.get("clip")
        if cid not in blind_a:
            continue
        q = ex.get("quotes") or {}
        a, b = quote_ok(q.get("A", ""), blind_a.get(cid, "")), quote_ok(q.get("B", ""), blind_b.get(cid, ""))
        ex = {**ex, "verified": "both" if a and b else "A" if a else "B" if b else "none"}
        if ex["verified"] == "both":
            best = "both"
        elif ex["verified"] != "none" and best == "none":
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
    f["examples"] = [e for e in kept if e["verified"] != "none"] if status != "rejected" else kept
    def taught(e: dict) -> bool:
        reply = norm(replies.get(e["clip"]) or "")
        word = norm(e.get("word", "")).strip(".,!?")
        return bool(word) and len(reply.split()) <= 8 and word in reply  # короткая реплика-повтор = поправка

    word_hits = [e for e in f["examples"] if taught(e)]
    f["taught_in_lesson"] = bool(word_hits)
    return f
