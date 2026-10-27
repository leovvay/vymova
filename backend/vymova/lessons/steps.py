"""Регистрация шагов конвейера: связывает урок с функциями предметных областей."""
from .. import audio
from . import runner, store
from .model import Lesson


def _ingest(lesson: Lesson) -> None:
    d = store.dir(lesson.id)
    audio.to_wav16k(d / lesson.source, d / "audio16k.wav")
    audio.to_mp3(d / lesson.source, d / "lesson.mp3")


def register_all() -> None:
    runner.register("ingest", _ingest, lambda l: store.dir(l.id) / "lesson.mp3")
