from typing import Literal

from pydantic import BaseModel


class Sample(BaseModel):
    start: float
    end: float
    text: str
    file: str


class Voice(BaseModel):
    speaker_id: str
    minutes: float
    words: int
    samples: list[Sample]
    suggested_name: str | None = None
    suggested_role: Literal["teacher", "student"] | None = None


class SpeakerLabel(BaseModel):
    role: Literal["teacher", "student", "skip"]
    name: str | None = None


TEACHER = "Репетитор"
