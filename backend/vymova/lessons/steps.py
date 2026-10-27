"""Регистрация шагов конвейера: связывает урок с функциями предметных областей."""
from .. import audio, settings, speakers, transcription
from . import runner, store
from .model import Lesson


def _ingest(lesson: Lesson) -> None:
    d = store.dir(lesson.id)
    audio.to_wav16k(d / lesson.source, d / "audio16k.wav")
    audio.to_mp3(d / lesson.source, d / "lesson.mp3")


def _transcribe(lesson: Lesson) -> None:
    d = store.dir(lesson.id)
    speech = d / "speech.m4a"
    audio.to_speech_m4a(d / lesson.source, speech)
    try:
        out = transcription.transcribe(speech, settings.load().elevenlabs_key, lesson.people)
    finally:
        speech.unlink(missing_ok=True)
    store.write_json(lesson.id, "transcript.json", out)


def _voices(lesson: Lesson) -> None:
    voices = speakers.build(store.dir(lesson.id), store.read_json(lesson.id, "transcript.json"))
    store.write_json(lesson.id, "voices.json", [v.model_dump() for v in voices])


def register_all() -> None:
    def art(name: str):
        return lambda l: store.dir(l.id) / name

    runner.register("ingest", _ingest, art("lesson.mp3"))
    runner.register("transcribe", _transcribe, art("transcript.json"))
    runner.register("voices", _voices, art("voices.json"))
