"""Один фоновый воркер: выполняет шаги урока по порядку, пропуская шаги с готовым артефактом."""
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from ..errors import StepError
from . import store
from .model import STEP_TITLES_RU, STEPS, Lesson

log = logging.getLogger("vymova.runner")


@dataclass
class _Step:
    fn: Callable[[Lesson], str | None]
    artifact: Callable[[Lesson], Path]


_registry: dict[str, _Step] = {}
_queue: "queue.Queue[str]" = queue.Queue()
_queued: set[str] = set()
_qlock = threading.Lock()
_started = False


def _delays() -> list[float]:
    return [float(x) for x in os.environ.get("VYMOVA_RETRY_DELAYS", "5,20,60").split(",") if x]


def register(step: str, fn: Callable[[Lesson], str | None], artifact: Callable[[Lesson], Path]) -> None:
    """fn может вернуть 'skipped', чтобы шаг считался пропущенным."""
    assert step in STEPS, step
    _registry[step] = _Step(fn, artifact)


def enqueue(lesson_id: str) -> None:
    with _qlock:
        if lesson_id in _queued:
            return
        _queued.add(lesson_id)
    _queue.put(lesson_id)


def retry(lesson_id: str) -> None:
    lesson = store.get(lesson_id)
    for st in lesson.steps.values():
        if st.status == "failed":
            st.status, st.error_ru = "pending", None
    store.save_state(lesson)
    enqueue(lesson_id)


def _set(lesson: Lesson, step: str, status: str, error_ru: str | None = None) -> None:
    st = lesson.steps[step]
    st.status, st.error_ru = status, error_ru
    if status == "running":
        st.started_at, st.finished_at = datetime.now(), None
    elif status in ("done", "failed", "skipped"):
        st.finished_at = datetime.now()
    store.save_state(lesson)


def _run_lesson(lesson_id: str) -> None:
    for step in STEPS:
        lesson = store.get(lesson_id)
        st = lesson.steps[step]
        if st.status in ("done", "skipped"):
            continue
        if st.status == "failed":
            return
        if step == "await_speakers":
            if (store.dir(lesson_id) / "speakers.json").exists():
                _set(lesson, step, "done")
                continue
            return
        reg = _registry.get(step)
        if reg is None:
            log.info("%s: step %s not available yet", lesson_id, step)
            return
        if reg.artifact(lesson).exists():
            _set(lesson, step, "done")
            continue
        _set(lesson, step, "running")
        delays = _delays()
        for attempt in range(len(delays) + 1):
            try:
                result = reg.fn(lesson)
                lesson = store.get(lesson_id)
                if result == "skipped":
                    _set(lesson, step, "skipped")
                elif reg.artifact(lesson).exists():
                    _set(lesson, step, "done")
                else:
                    raise StepError(f"Шаг «{STEP_TITLES_RU[step]}» не создал результат.")
                break
            except Exception as e:  # noqa: BLE001 - любая ошибка шага уходит в повтор
                msg = e.message_ru if isinstance(e, StepError) else \
                    f"Шаг «{STEP_TITLES_RU[step]}» не удался: {type(e).__name__}."
                log.warning("%s: step %s attempt %d failed: %s", lesson_id, step, attempt + 1, type(e).__name__)
                if attempt < len(delays) and not (isinstance(e, StepError) and not e.retry):
                    time.sleep(delays[attempt])
                    continue
                _set(store.get(lesson_id), step, "failed", msg)
                return


def _worker() -> None:
    while True:
        lesson_id = _queue.get()
        with _qlock:
            _queued.discard(lesson_id)
        try:
            _run_lesson(lesson_id)
        except Exception:  # noqa: BLE001 - воркер не должен умирать
            log.exception("runner crashed on %s", lesson_id)


def start() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_worker, name="vymova-runner", daemon=True).start()
    for lesson in store.list():
        if lesson.status not in ("done", "failed"):
            enqueue(lesson.id)
