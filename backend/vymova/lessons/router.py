import re
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .. import speakers
from . import runner, store
from .model import Lesson

router = APIRouter(prefix="/api/lessons", tags=["lessons"])
MEDIA_EXT = {".mp4", ".m4a", ".mp3", ".wav", ".webm", ".ogg", ".oga", ".mov", ".mkv", ".aac", ".flac"}


def _get(lesson_id: str) -> Lesson:
    if not store.exists(lesson_id):
        raise HTTPException(404, "Урок не найден")
    return store.get(lesson_id)


@router.post("")
def create_lesson(file: UploadFile = File(...), date: str | None = Form(None), topic: str | None = Form(None),
                  people: int | None = Form(None)) -> Lesson:
    if date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise HTTPException(422, "Дата урока — в формате ГГГГ-ММ-ДД")
    if Path(file.filename or "").suffix.lower() not in MEDIA_EXT:
        raise HTTPException(422, "Нужен файл записи: mp4, m4a, mp3, wav, webm, ogg, mov, mkv, aac или flac")
    if people is not None and not 2 <= people <= 8:
        raise HTTPException(422, "Число людей на записи — от 2 до 8")
    lesson = store.create(file.file, file.filename or "lesson", date or None, topic or None, people)
    runner.enqueue(lesson.id)
    return lesson


@router.get("")
def list_lessons() -> list[Lesson]:
    return store.list()


@router.get("/{lesson_id}")
def get_lesson(lesson_id: str) -> Lesson:
    return _get(lesson_id)


@router.post("/{lesson_id}/retry")
def retry_lesson(lesson_id: str) -> Lesson:
    _get(lesson_id)
    runner.retry(lesson_id)
    return store.get(lesson_id)


@router.get("/{lesson_id}/files/{path:path}")
def lesson_file(lesson_id: str, path: str) -> FileResponse:
    _get(lesson_id)
    root = store.dir(lesson_id).resolve()
    f = (root / path).resolve()
    if not f.is_relative_to(root) or not f.is_file() or f.name == "state.json" or f.name.startswith("source."):
        raise HTTPException(404, "Файл не найден")
    return FileResponse(f, headers={"X-Content-Type-Options": "nosniff"})


@router.put("/{lesson_id}/speakers")
def label_speakers(lesson_id: str, labels: dict[str, speakers.SpeakerLabel]) -> Lesson:
    lesson = _get(lesson_id)
    if lesson.steps["voices"].status != "done":
        raise HTTPException(409, "Голоса ещё не найдены")
    if lesson.steps["clips"].status in ("running", "done"):
        raise HTTPException(409, "Разбор уже идёт — разметку голосов менять нельзя")
    known = {v["speaker_id"] for v in store.read_json(lesson_id, "voices.json")}
    if set(labels) - known:
        raise HTTPException(422, "Неизвестный голос")
    students: dict[str, list[str]] = {}
    display: dict[str, str] = {}
    teacher: list[str] = []
    for spk, lab in labels.items():
        if lab.role == "student":
            name = " ".join((lab.name or "").split())
            if not name:
                raise HTTPException(422, "У студента должно быть имя")
            name = display.setdefault(name.casefold(), name)  # «Влад» and «влад » are the same student
            students.setdefault(name, []).append(spk)
        elif lab.role == "teacher":
            teacher.append(spk)
    if not students:
        raise HTTPException(422, "Отметьте хотя бы одного студента")
    store.write_json(lesson_id, "speakers.json", {
        "labels": {k: v.model_dump() for k, v in labels.items()}, "students": students, "teacher": teacher})
    d = store.dir(lesson_id)
    for name, spks in students.items():
        for spk in spks:
            speakers.memory.remember(name, spk, d)
    for spk in teacher:
        speakers.memory.remember(speakers.TEACHER, spk, d, role="teacher")
    lesson = store.get(lesson_id)
    lesson.students = list(students)
    lesson.steps["await_speakers"].status = "done"  # status becomes "queued" right away, we don't wait for the worker
    store.save_state(lesson)
    runner.enqueue(lesson_id)
    return lesson
