from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field

from ..errors import StepError  # noqa: F401 - реэкспорт

StepName = Literal["ingest", "transcribe", "voices", "await_speakers", "clips", "pass1", "blind",
                   "acoustic", "adjudicate", "language", "summary", "report"]
STEPS: tuple[str, ...] = ("ingest", "transcribe", "voices", "await_speakers", "clips", "pass1", "blind",
                          "acoustic", "adjudicate", "language", "summary", "report")
STEP_TITLES_RU = {
    "ingest": "Подготовка записи", "transcribe": "Расшифровка и голоса", "voices": "Поиск голосов",
    "await_speakers": "Кто есть кто", "clips": "Нарезка реплик", "pass1": "Первичный разбор",
    "blind": "Слепая проверка реплик", "acoustic": "Акустическая проверка", "adjudicate": "Сверка находок",
    "language": "Грамматика и лексика", "summary": "Сводка по группе", "report": "PDF",
}
StepStatus = Literal["pending", "running", "done", "failed", "skipped"]


class StepState(BaseModel):
    status: StepStatus = "pending"
    error_ru: str | None = None
    attempts: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None


class Lesson(BaseModel):
    id: str
    date: str
    topic: str = ""
    people: int | None = None
    source: str
    created_at: datetime
    steps: dict[str, StepState] = Field(default_factory=lambda: {s: StepState() for s in STEPS})
    students: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def status(self) -> str:
        sts = [self.steps[s].status for s in STEPS]
        if "failed" in sts:
            return "failed"
        if all(s in ("done", "skipped") for s in sts):
            return "done"
        if self.steps["voices"].status == "done" and self.steps["await_speakers"].status != "done":
            return "awaiting_speakers"
        return "running" if "running" in sts else "queued"
