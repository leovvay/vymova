from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from . import runner, store
from .model import Lesson

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


def _get(lesson_id: str) -> Lesson:
    if not store.exists(lesson_id):
        raise HTTPException(404, "Урок не найден")
    return store.get(lesson_id)


@router.post("")
def create_lesson(file: UploadFile = File(...), date: str | None = Form(None), topic: str | None = Form(None)) -> Lesson:
    lesson = store.create(file.file, file.filename or "lesson", date or None, topic or None)
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
    if not f.is_relative_to(root) or not f.is_file() or f.name == "state.json":
        raise HTTPException(404, "Файл не найден")
    return FileResponse(f)
