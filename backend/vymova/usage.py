"""Usage ledger: every paid API call is appended to <lesson>/usage.jsonl (tokens, credits)."""
import json
import threading
import time
from pathlib import Path

_lock = threading.Lock()
_current: tuple[Path, str] | None = None  # (lesson dir, step) — one runner thread, so a global is enough


def set_current(lesson_dir: Path | None, step: str | None) -> None:
    global _current
    _current = (lesson_dir, step) if lesson_dir and step else None


def record(service: str, **fields) -> None:
    cur = _current
    if cur is None:
        return
    line = json.dumps({"ts": round(time.time(), 3), "step": cur[1], "service": service, **fields}, ensure_ascii=False)
    with _lock, open(cur[0] / "usage.jsonl", "a", encoding="utf-8") as f:
        f.write(line + "\n")
