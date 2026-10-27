"""Память голосов между уроками. Реализация подсказок — в embeddings (задача 4)."""
from pathlib import Path


def remember(name: str, speaker_id: str, lesson_dir: Path) -> None:
    return None


def suggest(lesson_dir: Path, speaker_id: str) -> tuple[str | None, str | None]:
    return None, None
